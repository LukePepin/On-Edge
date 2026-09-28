"""DeviceLink: the ONLY owner of the trust monitor's serial port.

* One reader thread: read() -> raw bytes recorded first -> framing -> parsing -> continuity
  -> recorded device record -> live bus. No input-buffer flushing anywhere.
* send(): every command is validated, timestamped (request, write start, write end on the
  host monotonic clock) and recorded, whether it comes from the runner or the operator.
* Disconnects are detected, recorded and reported; the reader reopens the port by itself,
  but the runner treats a disconnect during an attempt as an acquisition failure.
"""
from __future__ import annotations

import collections
import json
import threading
import time

from . import protocol as P
from .telemetry import Freshness, FreshnessMonitor
from .transport import TransportError

ALLOWED_COMMANDS = ("ATTACK", "RECOVER")
WORKLOADS = ("ECC", "ZKP")


class LinkError(RuntimeError):
    pass


def config_command(workload: str, alpha: float) -> str:
    if workload not in WORKLOADS:
        raise LinkError(f"workload must be one of {WORKLOADS}")
    if not (0.0 < float(alpha) <= 1.0):
        raise LinkError("alpha must be in (0, 1]")
    return json.dumps({"algo": workload, "alpha": round(float(alpha), 4)}, separators=(",", ":"))


class DeviceLink:
    def __init__(self, transport_factory, recorder, bus, device_stale_ms: float = 1000.0,
                 reconnect_interval_s: float = 1.0):
        self._factory = transport_factory
        self.recorder = recorder
        self.bus = bus
        self.reconnect_interval_s = reconnect_interval_s
        self.transport = None
        self.connected = False
        self._running = False
        self._thread = None
        self._tx_lock = threading.Lock()
        self._cv = threading.Condition()
        self._recent = collections.deque(maxlen=400)
        self.framer = P.LineFramer()
        self.cont = P.Continuity()
        self.freshness = FreshnessMonitor("device", device_stale_ms)
        self.counters = collections.Counter()
        self.identity: dict | None = None
        self.protocol: str | None = None
        self.state = {"trust": None, "attack": None, "d12": None, "cycle": None, "workload": None, "alpha": None,
                      "exec_ms": None, "rx_mono_ns": None, "seq": None}
        self.last_error: str | None = None
        self.description = None
        self.simulated = False
        self._after_connect = False
        self.disconnects = 0
        self._connected_since = None
        self._backoff_s = reconnect_interval_s
        self.max_backoff_s = 5.0

    # ------------------------------------------------------------------ lifecycle
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._reader, name="device-link", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=3)
        self._close()

    def _close(self):
        if self.transport is not None:
            try:
                self.transport.close()
            except Exception:
                pass
        self.connected = False

    def _event(self, event: str, **detail):
        t_mono, t_wall = time.monotonic_ns(), time.time_ns()
        rec = {"t_mono_ns": t_mono, "t_wall_ns": t_wall, "event": event, **detail}
        self.recorder.record("host", rec)
        self.bus.publish("link", rec)

    # ------------------------------------------------------------------ reader
    def _reader(self):
        while self._running:
            if not self.connected:
                try:
                    self.transport = self._factory()
                    self.transport.open()
                    self.description = self.transport.description
                    self.simulated = bool(getattr(self.transport, "simulated", False))
                    self.connected = True
                    self._connected_since = time.monotonic()
                    self._after_connect = True
                    self.last_error = None
                    self._event("link_connected", port=getattr(self.transport, "port", None),
                                description=self.description, simulated=self.simulated)
                except TransportError as exc:
                    if self.last_error != str(exc):
                        self._event("link_unavailable", error=str(exc))
                    self.last_error = str(exc)
                    time.sleep(self.reconnect_interval_s)
                    continue
            try:
                data = self.transport.read(4096)
            except TransportError as exc:
                self._on_disconnect(str(exc))
                continue
            if data:
                t_mono, t_wall = time.monotonic_ns(), time.time_ns()
                self.recorder.record_raw_serial(data, t_mono, t_wall)
                self.counters["bytes"] += len(data)
                self.counters["reads"] += 1
                for fl in self.framer.feed(data, t_mono, t_wall):
                    self._handle(fl)

    def _on_disconnect(self, error: str):
        t_mono, t_wall = time.monotonic_ns(), time.time_ns()
        frag = self.framer.flush_partial(t_mono, t_wall)
        if frag is not None:
            self._handle(frag)
        self.disconnects += 1
        self.last_error = error
        self._close()
        # Back off before reopening. A port that opens but fails immediately (flapping USB,
        # wrong device) must not spin: the delay doubles while connections stay short.
        lasted = time.monotonic() - self._connected_since if self._connected_since else 0.0
        if lasted >= 2.0:
            self._backoff_s = self.reconnect_interval_s
        else:
            self._backoff_s = min(self.max_backoff_s, self._backoff_s * 2)
        self._event("link_disconnected", error=error, connected_for_s=round(lasted, 3),
                    retry_in_s=round(self._backoff_s, 3))
        with self._cv:
            self._cv.notify_all()
        end = time.monotonic() + self._backoff_s
        while self._running and time.monotonic() < end:
            time.sleep(0.05)

    def _handle(self, fl: P.FramedLine):
        msg = P.parse_line(fl.raw, fl.overflow, fl.terminated)
        events, ann = self.cont.observe(msg)
        rec = {"rx_mono_ns": fl.rx_mono_ns, "rx_wall_ns": fl.rx_wall_ns, "first_rx_mono_ns": fl.first_rx_mono_ns,
               "status": msg.status, "kind": msg.kind, "proto": msg.protocol, "epoch": ann.get("epoch", 0),
               "f": msg.fields}
        for k in ("t_dev_us", "t0_dev_us"):
            if k in ann:
                rec[k] = ann[k]
        if not msg.ok:
            rec["raw"] = msg.raw[:600]
            rec["problems"] = msg.problems
            self.counters["not_ok"] += 1
            self.counters[f"status_{msg.status}"] += 1
        if self._after_connect:
            rec["first_after_connect"] = True
            self._after_connect = False
        if events:
            rec["cont"] = [{"kind": e.kind, **e.detail} for e in events]
            for e in events:
                self.counters[f"cont_{e.kind}"] += 1
        self.counters["lines"] += 1
        self.freshness.note(fl.rx_mono_ns, valid=msg.ok)
        self._update_state(msg, rec)
        self.recorder.record("device", rec)
        self.bus.publish("device", rec)
        with self._cv:
            self._recent.append(rec)
            self._cv.notify_all()

    def _update_state(self, msg: P.DeviceMessage, rec: dict):
        if not msg.ok:
            return
        self.protocol = msg.protocol
        f = msg.fields
        s = self.state
        s["rx_mono_ns"] = rec["rx_mono_ns"]
        if msg.kind in ("boot", "hello"):
            self.identity = {k: f.get(k) for k in ("fw", "ver", "build", "proto", "thr", "pen_ecc_ms", "pen_zkp_ms")}
            s["d12"] = f.get("d12", s["d12"])
        elif msg.kind == "cfg":
            s.update({"workload": f["wl"], "alpha": f["alpha"], "trust": f["trust"], "attack": f["attack"],
                      "d12": f["d12"], "cycle": f["cycle"]})
        elif msg.kind == "cmd":
            s["attack"] = f["attack"]
        elif msg.kind == "upd":
            s.update({"trust": f["trust"], "attack": f["attack"], "d12": f["d12"], "cycle": f["cycle"],
                      "exec_ms": f["exec_ms"]})
        elif msg.kind == "out":
            s["d12"] = f["level"]
        elif msg.kind == "legacy_upd":
            s.update({"trust": f["trust"], "cycle": f["cycle"], "exec_ms": f["exec_ms"], "d12": None, "attack": None})
            self.identity = self.identity or {"fw": "legacy (unified_trust_monitor_template)", "proto": 0}
        s["seq"] = f.get("seq")

    # ------------------------------------------------------------------ commands
    def send(self, text: str, purpose: str, source: str = "runner", note: str | None = None) -> dict:
        """Send one validated command line. Returns the recorded tx record."""
        if text not in ALLOWED_COMMANDS and not text.startswith("{"):
            raise LinkError(f"refusing to send unrecognised command {text!r}")
        if text.startswith("{"):
            try:
                obj = json.loads(text)
                config_command(obj["algo"], obj["alpha"])
            except (ValueError, KeyError, TypeError) as exc:
                raise LinkError(f"invalid configuration command: {exc}")
        t_req = time.monotonic_ns()
        rec = {"t_request_mono_ns": t_req, "t_wall_ns": time.time_ns(), "cmd": text if not text.startswith("{") else "CONFIG",
               "text": text, "purpose": purpose, "source": source, "note": note}
        with self._tx_lock:
            if not self.connected or self.transport is None:
                rec.update({"ok": False, "error": "link not connected", "t_write_start_mono_ns": None,
                            "t_write_end_mono_ns": None})
            else:
                data = (text + "\n").encode("ascii")
                rec["t_write_start_mono_ns"] = time.monotonic_ns()
                try:
                    self.transport.write(data)
                    rec["t_write_end_mono_ns"] = time.monotonic_ns()
                    rec.update({"ok": True, "error": None})
                except TransportError as exc:
                    rec.update({"ok": False, "error": str(exc), "t_write_end_mono_ns": time.monotonic_ns()})
        self.counters["tx_ok" if rec["ok"] else "tx_failed"] += 1
        self.recorder.record("tx", rec)
        self.bus.publish("tx", rec)
        if not rec["ok"]:
            raise LinkError(rec["error"])
        return rec

    def wait_for(self, predicate, timeout_s: float, after_rx_ns: int = 0):
        """Wait for a recorded device record (dict) satisfying predicate, received after after_rx_ns."""
        deadline = time.monotonic() + timeout_s
        with self._cv:
            while True:
                for rec in self._recent:
                    if rec["rx_mono_ns"] >= after_rx_ns and predicate(rec):
                        return rec
                left = deadline - time.monotonic()
                if left <= 0 or not self._running:
                    return None
                self._cv.wait(min(left, 0.05))

    # ------------------------------------------------------------------ status
    def status(self) -> dict:
        now = time.monotonic_ns()
        fresh, age = self.freshness.state(now)
        if not self.connected:
            fresh = Freshness.UNAVAILABLE if self.last_error else Freshness.MISSING
        return {"connected": self.connected, "description": self.description, "simulated": self.simulated,
                "protocol": self.protocol, "identity": self.identity, "freshness": fresh.value, "age_ms": age,
                "state": dict(self.state), "continuity": self.cont.summary(), "counters": dict(self.counters),
                "disconnects": self.disconnects, "last_error": self.last_error, "pending_bytes": self.framer.pending_bytes()}
