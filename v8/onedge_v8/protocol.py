"""Trust-monitor serial protocol: byte framing, message parsing, and continuity checks.

Data path: raw bytes -> LineFramer -> FramedLine -> parse_line() -> DeviceMessage
           -> Continuity (sequence gaps, device resets, 32-bit clock unwrap).

Two firmware protocols are understood:

* ``v8``: firmware/trust_monitor_v8. Every record carries ``ev`` (record type), ``seq``
  (per-boot message counter, +1 per record) and ``t_us`` (device micros(), 32-bit, wraps
  every ~71.6 min). Missing records are detectable from ``seq``.
* ``legacy``: firmware/unified_trust_monitor_template (V6/V7). Reports
  ``{"cycle", "exec_time_ms", "trust_score"}`` without device time. ``cycle`` increases by
  one per trust update and resets on configuration, so missing update reports are still
  detectable, but device event times are not.

Nothing here discards bytes silently: malformed, oversized or unterminated input becomes a
message with a non-"ok" status so that it is counted and recorded.
"""
from __future__ import annotations

import json
import math
from dataclasses import dataclass, field

MAX_LINE_BYTES = 512
U32 = 1 << 32

# ---------------------------------------------------------------------------------------
# Framing
# ---------------------------------------------------------------------------------------


@dataclass
class FramedLine:
    raw: bytes                  # line content without the terminating newline / CR
    rx_mono_ns: int             # host monotonic time of the read that completed the line
    first_rx_mono_ns: int       # host monotonic time of the read that delivered its first byte
    rx_wall_ns: int             # host wall-clock time matching rx_mono_ns
    overflow: bool = False      # line exceeded MAX_LINE_BYTES and was split
    terminated: bool = True     # False only for a trailing fragment flushed at disconnect


class LineFramer:
    """Accumulates bytes across reads and splits them on ``\\n``.

    Handles partial lines (bytes of one line spread over several reads) and several lines
    delivered in one read. ``\\r`` before the newline is removed.
    """

    def __init__(self, max_line_bytes: int = MAX_LINE_BYTES):
        self.max_line_bytes = max_line_bytes
        self._buf = bytearray()
        self._first_rx: int | None = None
        self._in_overflow = False

    def feed(self, data: bytes, rx_mono_ns: int, rx_wall_ns: int) -> list[FramedLine]:
        out: list[FramedLine] = []
        start = 0
        n = len(data)
        while start < n:
            nl = data.find(b"\n", start)
            end = n if nl < 0 else nl
            if self._first_rx is None and (end > start or nl >= 0):
                self._first_rx = rx_mono_ns
            self._buf.extend(data[start:end])
            if nl < 0:
                if len(self._buf) > self.max_line_bytes:
                    # Emit the oversized prefix now; the rest of this line stays flagged.
                    out.append(self._emit(rx_mono_ns, rx_wall_ns, overflow=True, terminated=False))
                    self._in_overflow = True
                break
            overflow = self._in_overflow or len(self._buf) > self.max_line_bytes
            out.append(self._emit(rx_mono_ns, rx_wall_ns, overflow=overflow, terminated=True))
            self._in_overflow = False
            start = nl + 1
        return out

    def pending_bytes(self) -> int:
        return len(self._buf)

    def flush_partial(self, rx_mono_ns: int, rx_wall_ns: int) -> FramedLine | None:
        """Emit an unterminated trailing fragment (e.g. when the port disconnects)."""
        if not self._buf:
            return None
        line = self._emit(rx_mono_ns, rx_wall_ns, overflow=self._in_overflow, terminated=False)
        self._in_overflow = False
        return line

    def _emit(self, rx_mono_ns: int, rx_wall_ns: int, overflow: bool, terminated: bool) -> FramedLine:
        raw = bytes(self._buf)
        if raw.endswith(b"\r"):
            raw = raw[:-1]
        first = self._first_rx if self._first_rx is not None else rx_mono_ns
        self._buf.clear()
        self._first_rx = None
        return FramedLine(raw=raw, rx_mono_ns=rx_mono_ns, first_rx_mono_ns=first,
                          rx_wall_ns=rx_wall_ns, overflow=overflow, terminated=terminated)


# ---------------------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------------------

# Message status values (anything other than OK is a data-quality event).
OK = "ok"
EMPTY = "empty"
INVALID_ENCODING = "invalid_encoding"
NOT_JSON_OBJECT = "not_json_object"
MALFORMED_JSON = "malformed_json"
INVALID_FIELDS = "invalid_fields"
INVALID_VALUE = "invalid_value"
UNKNOWN_MESSAGE = "unknown_message"
OVERFLOW = "overflow"
UNTERMINATED = "unterminated"

_INT, _U32, _NUM, _BIT, _STR = "int", "u32", "num", "bit", "str"

V8_REQUIRED = {
    "boot": {"seq": _U32, "t_us": _U32, "fw": _STR, "ver": _STR, "proto": _INT},
    "hello": {"seq": _U32, "t_us": _U32, "fw": _STR, "ver": _STR, "proto": _INT},
    "cfg": {"seq": _U32, "t_us": _U32, "algo": _STR, "wl": _STR, "alpha": _NUM, "trust": _NUM,
            "cycle": _INT, "attack": _BIT, "d12": _BIT},
    "cmd": {"seq": _U32, "t_us": _U32, "cmd": _STR, "attack": _BIT, "prev": _BIT, "cycle": _INT},
    "upd": {"seq": _U32, "t_us": _U32, "t0_us": _U32, "cycle": _INT, "exec_ms": _NUM, "obs": _NUM,
            "trust": _NUM, "attack": _BIT, "below": _BIT, "d12": _BIT},
    "out": {"seq": _U32, "t_us": _U32, "level": _BIT, "cycle": _INT},
    "idle": {"seq": _U32, "t_us": _U32},
    "err": {"seq": _U32, "t_us": _U32, "code": _STR},
}

TRUST_TOLERANCE = 1e-3


@dataclass
class DeviceMessage:
    kind: str                       # v8 record type, "legacy_upd", "legacy_ready", or "unparsed"
    status: str                     # OK or an error code above
    protocol: str | None            # "v8", "legacy" or None when unparsed
    fields: dict = field(default_factory=dict)
    raw: str = ""                   # decoded text (replacement chars if undecodable)
    problems: list = field(default_factory=list)

    @property
    def ok(self) -> bool:
        return self.status == OK

    @property
    def seq(self):
        return self.fields.get("seq") if self.protocol == "v8" else None

    @property
    def t_us(self):
        return self.fields.get("t_us") if self.protocol == "v8" else None


def _type_ok(value, kind: str) -> bool:
    if kind == _STR:
        return isinstance(value, str)
    if isinstance(value, bool):
        return False
    if kind == _INT:
        return isinstance(value, int)
    if kind == _U32:
        return isinstance(value, int) and 0 <= value < U32
    if kind == _BIT:
        return isinstance(value, int) and value in (0, 1)
    if kind == _NUM:
        return isinstance(value, (int, float)) and math.isfinite(float(value))
    return False


def _range_problems(kind: str, f: dict) -> list:
    problems = []
    for key in ("trust", "obs"):
        if key in f and isinstance(f[key], (int, float)) and not isinstance(f[key], bool):
            if not (-TRUST_TOLERANCE <= float(f[key]) <= 100.0 + TRUST_TOLERANCE):
                problems.append(f"{key} out of range 0-100: {f[key]}")
    if kind == "upd" and _type_ok(f.get("exec_ms"), _NUM) and not (0.0 <= float(f["exec_ms"]) < 60000.0):
        problems.append(f"exec_ms out of range: {f['exec_ms']}")
    if kind == "cfg" and _type_ok(f.get("alpha"), _NUM) and not (0.0 < float(f["alpha"]) <= 1.0):
        problems.append(f"alpha out of range (0,1]: {f['alpha']}")
    return problems


def parse_line(raw: bytes, overflow: bool = False, terminated: bool = True) -> DeviceMessage:
    """Parse one framed line. Never raises; problems are reported in the result."""
    text = raw.decode("utf-8", errors="replace")
    if overflow:
        return DeviceMessage("unparsed", OVERFLOW, None, raw=text, problems=["line exceeded maximum length"])
    if not terminated:
        return DeviceMessage("unparsed", UNTERMINATED, None, raw=text, problems=["no terminating newline"])
    try:
        raw.decode("utf-8")
    except UnicodeDecodeError:
        return DeviceMessage("unparsed", INVALID_ENCODING, None, raw=text, problems=["not valid UTF-8"])
    s = text.strip()
    if not s:
        return DeviceMessage("unparsed", EMPTY, None, raw=text)
    if not (s.startswith("{") and s.endswith("}")):
        return DeviceMessage("unparsed", NOT_JSON_OBJECT, None, raw=text)
    try:
        obj = json.loads(s)
    except ValueError as exc:
        return DeviceMessage("unparsed", MALFORMED_JSON, None, raw=text, problems=[str(exc)])
    if not isinstance(obj, dict):
        return DeviceMessage("unparsed", NOT_JSON_OBJECT, None, raw=text)

    if "ev" in obj:
        kind = obj.get("ev")
        if not isinstance(kind, str) or kind not in V8_REQUIRED:
            return DeviceMessage("unparsed", UNKNOWN_MESSAGE, "v8", fields=obj, raw=text,
                                 problems=[f"unknown record type {kind!r}"])
        problems = [f"{k}: missing" for k in V8_REQUIRED[kind] if k not in obj]
        problems += [f"{k}: bad type/value {obj[k]!r}" for k, t in V8_REQUIRED[kind].items()
                     if k in obj and not _type_ok(obj[k], t)]
        if problems:
            return DeviceMessage(kind, INVALID_FIELDS, "v8", fields=obj, raw=text, problems=problems)
        problems = _range_problems(kind, obj)
        if problems:
            return DeviceMessage(kind, INVALID_VALUE, "v8", fields=obj, raw=text, problems=problems)
        return DeviceMessage(kind, OK, "v8", fields=obj, raw=text)

    if "trust_score" in obj:
        problems = []
        if not _type_ok(obj.get("cycle"), _INT):
            problems.append("cycle: missing or bad type")
        for k in ("exec_time_ms", "trust_score"):
            if not _type_ok(obj.get(k), _NUM):
                problems.append(f"{k}: missing or bad type")
        if problems:
            return DeviceMessage("legacy_upd", INVALID_FIELDS, "legacy", fields=obj, raw=text, problems=problems)
        f = {"cycle": obj["cycle"], "exec_ms": float(obj["exec_time_ms"]), "trust": float(obj["trust_score"])}
        problems = _range_problems("upd", f)
        status = INVALID_VALUE if problems else OK
        return DeviceMessage("legacy_upd", status, "legacy", fields=f, raw=text, problems=problems)

    if obj.get("status") == "READY":
        return DeviceMessage("legacy_ready", OK, "legacy", fields=obj, raw=text)
    return DeviceMessage("unparsed", UNKNOWN_MESSAGE, None, fields=obj, raw=text,
                         problems=["JSON object without a recognised record type"])


# ---------------------------------------------------------------------------------------
# Continuity: sequence numbers, device resets, device clock
# ---------------------------------------------------------------------------------------


@dataclass
class ContinuityEvent:
    kind: str          # "gap", "duplicate", "reset", "clock_backstep", "legacy_cycle_gap"
    detail: dict


class Continuity:
    """Tracks one device stream: sequence continuity, resets and the unwrapped device clock.

    A *device epoch* is one uninterrupted period of device uptime. It starts at the first
    record seen and changes when the device evidently restarted (``boot`` record, sequence
    regression, or backwards device time). Device timestamps from different epochs are
    never comparable.
    """

    def __init__(self, backstep_reset_us: int = 100_000):
        self.backstep_reset_us = backstep_reset_us
        self.small_backsteps = 0
        self.epoch = 0
        self._started = False
        self._next_seq: int | None = None
        self._last_raw_t: int | None = None
        self._last_ext_t: int | None = None
        self._legacy_next_cycle: int | None = None
        self.missing_total = 0
        self.gap_events = 0
        self.duplicates = 0
        self.resets = 0

    def _new_epoch(self, reason: str, detail: dict, events: list):
        if self._started:
            self.epoch += 1
            self.resets += 1
            events.append(ContinuityEvent("reset", {"reason": reason, "new_epoch": self.epoch, **detail}))
        self._started = True
        self._next_seq = None
        self._last_raw_t = None
        self._last_ext_t = None

    def unwrap(self, t_us: int) -> int:
        """Extend a 32-bit device timestamp within the current epoch (call after observe())."""
        if self._last_raw_t is None:
            return t_us
        delta = (t_us - self._last_raw_t) % U32
        if delta < U32 // 2:
            return self._last_ext_t + delta
        return self._last_ext_t - (U32 - delta)

    def observe(self, msg: DeviceMessage) -> tuple[list, dict]:
        """Update continuity state with a parsed message.

        Returns (events, annotations) where annotations contains ``epoch`` and, for v8
        records, ``t_dev_us`` (unwrapped device time) and ``t0_dev_us`` for updates.
        """
        events: list = []
        ann: dict = {}
        if msg.protocol == "v8" and msg.ok:
            seq = msg.fields["seq"]
            t_raw = msg.fields["t_us"]
            if msg.kind == "boot":
                self._new_epoch("boot_record", {"seq": seq}, events)
            elif self._next_seq is not None:
                if seq == self._next_seq:
                    pass
                elif seq > self._next_seq:
                    missing = seq - self._next_seq
                    self.missing_total += missing
                    self.gap_events += 1
                    events.append(ContinuityEvent("gap", {"expected": self._next_seq, "got": seq,
                                                          "missing": missing}))
                elif seq == self._next_seq - 1:
                    self.duplicates += 1
                    events.append(ContinuityEvent("duplicate", {"seq": seq}))
                else:
                    self._new_epoch("sequence_regression", {"expected": self._next_seq, "got": seq}, events)
            else:
                self._started = True
            # device clock: records carry EVENT times, so a record can be stamped slightly
            # earlier than the one before it; only a large backwards jump indicates a restart.
            if self._last_raw_t is not None:
                delta = (t_raw - self._last_raw_t) % U32
                if delta >= U32 // 2:
                    back_us = U32 - delta
                    if back_us > self.backstep_reset_us:
                        events.append(ContinuityEvent("clock_backstep", {"back_us": back_us, "seq": seq}))
                        self._new_epoch("device_time_backwards", {"back_us": back_us}, events)
                    else:
                        self.small_backsteps += 1
            t_ext = self.unwrap(t_raw)
            self._last_raw_t = t_raw
            self._last_ext_t = t_ext
            self._next_seq = seq + 1
            ann["t_dev_us"] = t_ext
            if msg.kind == "upd":
                ann["t0_dev_us"] = t_ext - ((t_raw - msg.fields["t0_us"]) % U32)
            if msg.kind == "cfg":
                self._legacy_next_cycle = None
        elif msg.protocol == "legacy" and msg.ok and msg.kind == "legacy_upd":
            cyc = msg.fields["cycle"]
            if self._legacy_next_cycle is not None and cyc != self._legacy_next_cycle:
                if cyc > self._legacy_next_cycle:
                    missing = cyc - self._legacy_next_cycle
                    self.missing_total += missing
                    self.gap_events += 1
                    events.append(ContinuityEvent("legacy_cycle_gap", {"expected": self._legacy_next_cycle,
                                                                       "got": cyc, "missing": missing}))
                else:
                    events.append(ContinuityEvent("reset", {"reason": "legacy_cycle_restart", "got": cyc}))
            self._legacy_next_cycle = cyc + 1
        elif msg.protocol == "legacy" and msg.kind == "legacy_ready":
            self._legacy_next_cycle = 0
        ann["epoch"] = self.epoch
        return events, ann

    def summary(self) -> dict:
        return {"epoch": self.epoch, "missing_records": self.missing_total, "gap_events": self.gap_events,
                "duplicates": self.duplicates, "resets": self.resets, "small_backsteps": self.small_backsteps}
