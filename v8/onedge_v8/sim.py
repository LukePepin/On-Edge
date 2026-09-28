"""SOFTWARE SIMULATION of the trust monitor, its serial link, and the robot.

Everything produced here is labeled simulated by the daemon and stored under a separate
data root. It exists to exercise the acquisition, campaign and dashboard software without
hardware; it is not evidence about the physical system.

SimMonitor follows firmware/trust_monitor_v8 (protocol 1) or, with protocol="legacy", the
historical template's report format. Timing parameters default to historical summaries
(ECC 111.54 ms, two scalar multiplications 224.86 ms) but are configurable.
SimRobot is a kinematic stand-in: it follows trajectories, publishes joint states in the
UR ROS 2 driver's joint order, and performs a simulated safeguard stop when the simulated
D12 output goes low.
"""
from __future__ import annotations

import math
import random
import threading
import time
from dataclasses import dataclass, field

from .campaign import f32, firmware_trust_update
from .telemetry import CANONICAL_JOINTS, joint_sample_from_msg
from .transport import TransportError

UR_ROS2_JOINT_ORDER = ["shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint",
                       "wrist_3_joint", "shoulder_pan_joint"]
SAFETY_MODES = {1: "NORMAL", 3: "PROTECTIVE_STOP", 5: "SAFEGUARD_STOP", 7: "ROBOT_EMERGENCY_STOP"}


@dataclass
class SimFaults:
    """Deterministic fault injection (seeded)."""
    seed: int = 1
    chunk_max: int = 0                 # >0: reads return random 1..chunk_max byte chunks
    drop_line_prob: float = 0.0        # a whole record disappears (sequence gap)
    corrupt_line_prob: float = 0.0     # one byte of a record is altered
    reset_at_s: list = field(default_factory=list)       # device resets (host time since start)
    disconnect_at_s: float | None = None                 # transport raises at this time ...
    reconnect_after_s: float = 1.0                       # ... and can reopen after this long
    stall_at_s: float | None = None                      # device output pauses ...
    stall_s: float = 0.0                                 # ... for this long (bytes buffered)
    exec_spike_cycles: list = field(default_factory=list)  # cycle numbers with a 500 ms workload


class SimMonitor:
    def __init__(self, protocol: str = "v8", ecc_ms: float = 111.54, zkp_mult_ms: float = 112.43,
                 jitter_ms: float = 0.2, loop_delay_ms: float = 10.0, report_cost_ms: float = 0.15,
                 drift_ppm: float = 25.0, start_offset_us: int = 0, faults: SimFaults | None = None):
        self.protocol = protocol
        self.ecc_ms, self.zkp_mult_ms, self.jitter_ms = ecc_ms, zkp_mult_ms, jitter_ms
        self.loop_delay_ms, self.report_cost_ms = loop_delay_ms, report_cost_ms
        self.drift_ppm = drift_ppm
        self.start_offset_us = start_offset_us
        self.faults = faults or SimFaults()
        self._rng = random.Random(self.faults.seed)
        self._lock = threading.Lock()
        self._cv = threading.Condition(self._lock)
        self._rx = bytearray()
        self._out = bytearray()
        self._running = False
        self._thread = None
        self.t_start = time.monotonic()
        self.d12 = 1
        self.d12_listeners: list = []
        self._resets_done = 0
        self.disconnected_at = None
        self._boot()

    # ---- device state --------------------------------------------------------------------
    def _boot(self):
        self.boot_ns = time.monotonic_ns()
        self.seq = 0
        self.trust = 100.0
        self.alpha = 0.3
        self.algo = "UNKNOWN"
        self.wl = None
        self.cycle = 0
        self.attack = False
        self.configured = False
        self.n_cfg = 0
        self.last_write_us = -1
        self._set_d12(1)            # firmware drives D12 HIGH at boot (see review notes)
        self._line = bytearray()

    def _set_d12(self, level: int):
        changed = level != self.d12
        self.d12 = level
        if changed:
            for cb in list(self.d12_listeners):
                cb(level)

    def dev_us(self) -> int:
        el = (time.monotonic_ns() - self.boot_ns) / 1000.0 * (1.0 + self.drift_ppm * 1e-6)
        return int(el + self.start_offset_us) & 0xFFFFFFFF

    # ---- host side -----------------------------------------------------------------------
    def host_write(self, data: bytes):
        with self._cv:
            self._rx.extend(data)

    def host_read(self, max_bytes: int, timeout_s: float) -> bytes:
        deadline = time.monotonic() + timeout_s
        with self._cv:
            while not self._out and time.monotonic() < deadline:
                self._cv.wait(max(0.0, deadline - time.monotonic()))
            f = self.faults
            if f.stall_at_s is not None and f.stall_at_s <= self.elapsed() < f.stall_at_s + f.stall_s:
                return b""
            n = min(max_bytes, len(self._out))
            if f.chunk_max and n:
                n = min(n, self._rng.randint(1, f.chunk_max))
            data = bytes(self._out[:n])
            del self._out[:n]
            return data

    def elapsed(self) -> float:
        return time.monotonic() - self.t_start

    # ---- thread --------------------------------------------------------------------------
    def start(self):
        self._running = True
        self._thread = threading.Thread(target=self._run, name="sim-monitor", daemon=True)
        self._thread.start()

    def stop(self):
        self._running = False
        if self._thread:
            self._thread.join(timeout=2)

    def _sleep(self, ms: float):
        end = time.monotonic() + ms / 1000.0
        while self._running:
            left = end - time.monotonic()
            if left <= 0:
                return
            time.sleep(min(left, 0.005))
            self._maybe_reset()

    def _maybe_reset(self):
        f = self.faults
        if self._resets_done < len(f.reset_at_s) and self.elapsed() >= f.reset_at_s[self._resets_done]:
            self._resets_done += 1
            with self._cv:
                self._rx.clear()
            self._boot()
            self._emit_identity("boot")
            raise _Reset()

    def _run(self):
        self._emit_identity("boot")
        while self._running:
            try:
                self._setup_phase()
                while self._running:
                    self._loop_once()
            except _Reset:
                continue

    def _setup_phase(self):
        last_hello = time.monotonic()
        while self._running and not self.configured:
            if self.protocol == "v8" and time.monotonic() - last_hello >= 1.0:
                self._emit_identity("hello")
                last_hello = time.monotonic()
            for line in self._take_lines():
                self._handle_line(line, setup=True)
                if self.configured:
                    break
            self._sleep(1)

    def _take_lines(self) -> list:
        with self._cv:
            data = bytes(self._rx)
            self._rx.clear()
        lines = []
        for b in data:
            if b == 10:
                lines.append(self._line.decode("utf-8", "replace").strip())
                self._line = bytearray()
            else:
                self._line.append(b)
                if len(self._line) > 200:
                    self._err("overflow", len(self._line))
                    self._line = bytearray()
        return lines

    def _handle_line(self, line: str, setup: bool = False):
        import json
        t = self.dev_us()
        if not setup and line in ("ATTACK", "RECOVER"):
            prev = self.attack
            self.attack = line == "ATTACK"
            if self.protocol == "v8":
                self._emit({"ev": "cmd", "t_us": t, "cmd": line, "attack": int(self.attack), "prev": int(prev),
                            "cycle": self.cycle})
            return
        if line.startswith("{") and line.endswith("}"):
            try:
                doc = json.loads(line)
            except ValueError:
                self._err("bad_json", len(line))
                return
            if isinstance(doc, dict) and "algo" in doc and "alpha" in doc:
                self._apply_config(doc, t)
            else:
                self._err("bad_cfg", len(line))
            return
        if line:
            self._err("unknown_cmd", len(line))

    def _apply_config(self, doc: dict, t: int):
        self.algo = str(doc["algo"])
        self.alpha = f32(float(doc["alpha"]))
        self.trust = 100.0
        self.cycle = 0
        self.attack = False
        if self.algo == "ZKP":
            self.wl = "ZKP"
        elif self.algo == "ECC":
            self.wl = "ECC"
        elif self.algo == "CLOUD":
            self.wl = None
        t_high = self.dev_us()
        changed = self.d12 == 0
        self._set_d12(1)
        self.n_cfg += 1
        self.configured = True
        if self.protocol == "legacy":
            self._write_line('{"status": "READY"}')
            return
        self._emit({"ev": "cfg", "t_us": t, "algo": self.algo[:16], "wl": self.wl or "NONE",
                    "alpha": round(self.alpha, 4), "trust": 100.0, "cycle": 0, "attack": 0, "d12": 1,
                    "n_cfg": self.n_cfg})
        if changed:
            self._emit({"ev": "out", "t_us": t_high, "pin": 12, "level": 1, "cycle": self.cycle,
                        "trust": round(self.trust, 4)})

    def _loop_once(self):
        for line in self._take_lines():
            self._handle_line(line)
        if self.wl is None:
            self._sleep(1)
            return
        t0 = self.dev_us()
        base = self.ecc_ms if self.wl == "ECC" else 2 * self.zkp_mult_ms
        exec_ms = max(0.1, base + self._rng.uniform(-self.jitter_ms, self.jitter_ms))
        if self.cycle in self.faults.exec_spike_cycles:
            exec_ms = 500.0
        self._sleep(exec_ms)
        exec_f = f32(exec_ms)
        obs = 100.0
        if self.attack:
            obs = 0.0
        else:
            thr = 150.0 if self.wl == "ECC" else 400.0
            if exec_f > thr:
                obs = max(0.0, f32(100.0 - f32(exec_f - thr)))
        self.trust = firmware_trust_update(self.trust, self.alpha, obs)
        t_upd = self.dev_us()
        below = self.trust < 30.0
        out_pending = None
        if below:
            t_out = self.dev_us()
            if self.d12 == 1:
                out_pending = t_out
            self._set_d12(0)
        if self.protocol == "legacy":
            self._write_line('{"cycle": %d, "exec_time_ms": %s, "trust_score": %s}'
                             % (self.cycle, _arduino_float(exec_f), _arduino_float(self.trust)))
        else:
            self._emit({"ev": "upd", "t_us": t_upd, "t0_us": t0, "cycle": self.cycle, "exec_ms": round(exec_f, 3),
                        "obs": round(obs, 4), "trust": round(self.trust, 4), "attack": int(self.attack),
                        "below": int(below), "d12": self.d12, "pw_us": self.last_write_us})
            self.last_write_us = int(self.report_cost_ms * 1000)
            if out_pending is not None:
                self._emit({"ev": "out", "t_us": out_pending, "pin": 12, "level": 0, "cycle": self.cycle,
                            "trust": round(self.trust, 4)})
        self._sleep(self.report_cost_ms)
        self.cycle += 1
        self._sleep(self.loop_delay_ms)

    # ---- output ----------------------------------------------------------------------------
    def _emit_identity(self, ev: str):
        if self.protocol == "legacy":
            return
        self._emit({"ev": ev, "t_us": self.dev_us(), "fw": "trust_monitor_v8_SIM", "ver": "8.0.0-sim",
                    "build": "simulation", "proto": 1, "thr": 30.0, "pen_ecc_ms": 150.0, "pen_zkp_ms": 400.0,
                    "pin": 12, "d12": self.d12, "n_cfg": self.n_cfg})

    def _err(self, code: str, n: int):
        if self.protocol == "v8":
            self._emit({"ev": "err", "t_us": self.dev_us(), "code": code, "len": n})

    def _emit(self, rec: dict):
        import json
        ordered = {"ev": rec.pop("ev"), "seq": self.seq, "t_us": rec.pop("t_us")}
        ordered.update(rec)
        self.seq = (self.seq + 1) & 0xFFFFFFFF
        self._write_line(json.dumps(ordered, separators=(",", ":")))

    def _write_line(self, text: str):
        data = (text + "\r\n").encode()
        f = self.faults
        if f.drop_line_prob and self._rng.random() < f.drop_line_prob:
            return
        if f.corrupt_line_prob and self._rng.random() < f.corrupt_line_prob and len(data) > 4:
            i = self._rng.randint(1, len(data) - 3)
            data = data[:i] + b"#" + data[i + 1:]
        with self._cv:
            self._out.extend(data)
            self._cv.notify_all()


class _Reset(Exception):
    pass


def _arduino_float(x: float, digits: int = 2) -> str:
    """Arduino Print::printFloat output (used by the legacy protocol)."""
    if math.isnan(x):
        return "nan"
    neg = x < 0
    x = abs(x) + 0.5 / (10 ** digits)
    ip = int(x)
    rem = x - ip
    s = ("-" if neg else "") + str(ip) + "."
    for _ in range(digits):
        rem *= 10
        d = int(rem)
        s += str(d)
        rem -= d
    return s


class SimTransport:
    simulated = True

    def __init__(self, monitor: SimMonitor, read_timeout_s: float = 0.02):
        self.monitor = monitor
        self.read_timeout_s = read_timeout_s
        self.port = "sim://trust-monitor"
        self._open = False

    @property
    def description(self) -> str:
        return "SIMULATED trust monitor (software model)"

    def _check_disconnect(self):
        m = self.monitor                       # fault state lives on the device, not the handle
        f = m.faults
        if f.disconnect_at_s is not None and m.disconnected_at is None and m.elapsed() >= f.disconnect_at_s:
            m.disconnected_at = time.monotonic()
            self._open = False
            raise TransportError("simulated USB disconnect")

    def open(self):
        m = self.monitor
        if m.disconnected_at is not None and time.monotonic() - m.disconnected_at < m.faults.reconnect_after_s:
            raise TransportError("simulated device not present")
        self._open = True

    def read(self, max_bytes: int = 4096) -> bytes:
        if not self._open:
            raise TransportError("port not open")
        self._check_disconnect()
        return self.monitor.host_read(max_bytes, self.read_timeout_s)

    def write(self, data: bytes):
        if not self._open:
            raise TransportError("port not open")
        self._check_disconnect()
        self.monitor.host_write(data)

    def close(self):
        self._open = False


# ---------------------------------------------------------------------------------------
# Simulated robot
# ---------------------------------------------------------------------------------------

@dataclass
class SimRobotFaults:
    telemetry_dropout_at_s: float | None = None
    telemetry_dropout_s: float = 0.0
    protective_stop_at_s: float | None = None


class SimRobot:
    """Implements the RobotInterface used by the runner (see robot.py)."""
    kind = "sim"
    simulated = True

    def __init__(self, monitor: SimMonitor | None = None, rate_hz: float = 125.0, controller_delay_ms: float = 12.0,
                 decel_ms: float = 320.0, faults: SimRobotFaults | None = None):
        self.rate_hz = rate_hz
        self.controller_delay_ms = controller_delay_ms
        self.decel_ms = decel_ms
        self.faults = faults or SimRobotFaults()
        self._lock = threading.RLock()
        self.q = [math.radians(v) for v in (0.0, -90.0, -90.0, -60.0, -265.0, -280.0)]
        self.qd = [0.0] * 6
        self.safety = 1
        self.program_running = True
        self._traj = None
        self._stop_until = None
        self._decel_from = None
        self._running = False
        self._cb_joint = self._cb_state = self._cb_event = None
        self.t_start = time.monotonic()
        self._pending_safeguard = None
        if monitor is not None:
            monitor.d12_listeners.append(self._on_d12)

    # ---- RobotInterface ----------------------------------------------------------------------
    def capabilities(self) -> dict:
        return {"joint_telemetry": True, "safety_mode": True, "program_state": True, "trajectory": True,
                "dashboard": True, "simulated": True}

    def start(self, on_joint, on_robot_state, on_event):
        self._cb_joint, self._cb_state, self._cb_event = on_joint, on_robot_state, on_event
        self._running = True
        threading.Thread(target=self._run, name="sim-robot", daemon=True).start()
        self._publish_state("safety_mode", self.safety)
        self._publish_state("program_running", 1)

    def stop(self):
        self._running = False

    def send_trajectory(self, phase: int, joint_names, points):
        with self._lock:
            if self.safety != 1 or not self.program_running:
                self._event({"event": "trajectory", "phase": phase, "status": "rejected",
                             "reason": "robot not ready (safety mode or program not running)"})
                return
            start = list(self.q)
            self._traj = {"phase": phase, "t0": time.monotonic(), "start": start,
                          "points": [(list(p), float(t)) for p, t in points]}
        self._event({"event": "trajectory", "phase": phase, "status": "sent"})
        self._event({"event": "trajectory", "phase": phase, "status": "accepted"})

    def cancel_trajectory(self):
        with self._lock:
            tr = self._traj
            self._traj = None
            if tr:
                self._decel_from = (time.monotonic(), list(self.qd))
        if tr:
            self._event({"event": "trajectory", "phase": tr["phase"], "status": "canceled"})

    def dashboard(self, command: str) -> dict:
        c = command.strip()
        with self._lock:
            if c == "safetymode" or c == "safetystatus":
                resp = f"Safetymode: {SAFETY_MODES.get(self.safety, self.safety)}"
            elif c == "robotmode":
                resp = "Robotmode: RUNNING"
            elif c == "programState":
                resp = "PLAYING sim_external_control.urp" if self.program_running else "PAUSED sim_external_control.urp"
            elif c == "play":
                if self.safety == 1:
                    self.program_running = True
                    resp = "Starting program"
                else:
                    resp = "Failed to execute: play"
            elif c == "pause":
                self.program_running = False
                resp = "Pausing program"
            elif c == "unlock protective stop":
                if self.safety == 3:
                    self.safety = 1
                resp = "Protective stop releasing"
            else:
                resp = f"could not understand: '{c}'"
        if c in ("play", "pause"):
            self._publish_state("program_running", int(self.program_running))
        if c == "unlock protective stop":
            self._publish_state("safety_mode", self.safety)
        return {"ok": True, "response": resp, "simulated": True}

    def controller_ok(self) -> tuple:
        return True, "simulated controller: passthrough active"

    def activate_trajectory_controller(self) -> tuple:
        return True, "simulated controller switch"

    # ---- dynamics ------------------------------------------------------------------------------
    def _on_d12(self, level: int):
        with self._lock:
            if level == 0:
                self._pending_safeguard = time.monotonic() + self.controller_delay_ms / 1000.0
            else:
                self._pending_safeguard = None
                if self.safety == 5:
                    self.safety = 1
                    self._publish_state("safety_mode", 1)

    def _event(self, ev: dict):
        if self._cb_event:
            self._cb_event(ev)

    def _publish_state(self, source: str, value: int):
        if self._cb_state:
            name = SAFETY_MODES.get(value, str(value)) if source == "safety_mode" else str(bool(value))
            self._cb_state(source, value, name)

    def _run(self):
        period = 1.0 / self.rate_hz
        nxt = time.monotonic()
        while self._running:
            nxt += period
            now = time.monotonic()
            self._step(now)
            f = self.faults
            el = now - self.t_start
            dropout = f.telemetry_dropout_at_s is not None and f.telemetry_dropout_at_s <= el < (
                f.telemetry_dropout_at_s + f.telemetry_dropout_s)
            if not dropout and self._cb_joint:
                with self._lock:
                    q, qd = list(self.q), list(self.qd)
                order = [CANONICAL_JOINTS.index(n) for n in UR_ROS2_JOINT_ORDER]
                wall = time.time_ns()
                sample = joint_sample_from_msg(UR_ROS2_JOINT_ORDER, [q[i] for i in order], [qd[i] for i in order],
                                               wall - 300_000, time.monotonic_ns(), wall)
                self._cb_joint(sample)
            time.sleep(max(0.0, nxt - time.monotonic()))

    def _step(self, now: float):
        ev = None
        with self._lock:
            f = self.faults
            if f.protective_stop_at_s is not None and self.safety == 1 and now - self.t_start >= f.protective_stop_at_s:
                f.protective_stop_at_s = None
                self._halt(now, 3)
                ev = ("safety_mode", 3)
            if self._pending_safeguard is not None and now >= self._pending_safeguard:
                self._pending_safeguard = None
                self._halt(now, 5)
                ev = ("safety_mode", 5)
            if self._decel_from is not None:
                t0, v0 = self._decel_from
                k = max(0.0, 1.0 - (now - t0) / (self.decel_ms / 1000.0))
                self.qd = [v * k for v in v0]
                dt = 1.0 / self.rate_hz
                self.q = [q + v * dt for q, v in zip(self.q, self.qd)]
                if k == 0.0:
                    self._decel_from = None
                    self.qd = [0.0] * 6
            elif self._traj is not None:
                self._follow(now)
            else:
                self.qd = [0.0] * 6
        if ev:
            self._publish_state(*ev)
            if ev[1] in (3, 5):
                self.program_running = False
                self._publish_state("program_running", 0)

    def _halt(self, now: float, mode: int):
        self.safety = mode
        tr = self._traj
        self._traj = None
        self._decel_from = (now, list(self.qd))
        if tr:
            threading.Thread(target=self._event, args=({"event": "trajectory", "phase": tr["phase"],
                                                         "status": "aborted",
                                                         "reason": f"simulated {SAFETY_MODES[mode]}"},),
                             daemon=True).start()

    def _follow(self, now: float):
        tr = self._traj
        t = now - tr["t0"]
        prev_q, prev_t = tr["start"], 0.0
        for q_target, t_target in tr["points"]:
            if t <= t_target:
                s = (t - prev_t) / max(1e-6, t_target - prev_t)
                sm = s * s * (3 - 2 * s)
                dsm = 6 * s * (1 - s) / max(1e-6, t_target - prev_t)
                self.q = [a + (b - a) * sm for a, b in zip(prev_q, q_target)]
                self.qd = [(b - a) * dsm for a, b in zip(prev_q, q_target)]
                return
            prev_q, prev_t = q_target, t_target
        self.q = list(tr["points"][-1][0])
        self.qd = [0.0] * 6
        self._traj = None
        threading.Thread(target=self._event, args=({"event": "trajectory", "phase": tr["phase"],
                                                     "status": "succeeded"},), daemon=True).start()
