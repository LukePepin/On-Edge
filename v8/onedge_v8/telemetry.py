"""Telemetry freshness, joint samples, and motion criteria (moving / standstill).

Principles (V8 correction of the historical logger):

* Missing or stale telemetry is represented as missing/stale. It is never replaced by zeros
  and never interpreted as standstill.
* Joint values are mapped to canonical joint order by *name*. The historical logger copied
  the first six values in message order under canonical column labels; the V6 file
  trial_ECC_outage1000_ewma3_iter3_1786495528.csv matches the 'Pick' pose rotated by one
  joint, which suggests those per-joint column labels were shifted (the per-row maximum
  over all joints is unaffected). V8 records the original message order as well.
* Standstill is an operational criterion with declared parameters, evaluated only on fresh
  samples. A telemetry gap inside the evaluation window makes the result undetermined.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from enum import Enum

from .clocks import ros_stamp_to_mono_ns

CANONICAL_JOINTS = ("shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
                    "wrist_1_joint", "wrist_2_joint", "wrist_3_joint")


class Freshness(str, Enum):
    FRESH = "fresh"             # a valid sample arrived within the staleness limit
    STALE = "stale"             # the last valid sample is older than the limit
    MISSING = "missing"         # configured source, but nothing valid received yet
    INVALID = "invalid"         # the most recent message from the source was invalid
    UNAVAILABLE = "unavailable"  # source not configured / not present in this mode


class FreshnessMonitor:
    def __init__(self, name: str, stale_after_ms: float, configured: bool = True):
        self.name = name
        self.stale_after_ns = int(stale_after_ms * 1e6)
        self.configured = configured
        self.last_valid_ns: int | None = None
        self.last_any_ns: int | None = None
        self.last_was_valid = True
        self.valid_count = 0
        self.invalid_count = 0

    def note(self, rx_mono_ns: int, valid: bool = True):
        self.last_any_ns = rx_mono_ns
        self.last_was_valid = valid
        if valid:
            self.last_valid_ns = rx_mono_ns
            self.valid_count += 1
        else:
            self.invalid_count += 1

    def state(self, now_mono_ns: int) -> tuple[Freshness, float | None]:
        if not self.configured:
            return Freshness.UNAVAILABLE, None
        if self.last_any_ns is None:
            return Freshness.MISSING, None
        age_ms = None if self.last_valid_ns is None else (now_mono_ns - self.last_valid_ns) / 1e6
        if not self.last_was_valid:
            return Freshness.INVALID, age_ms
        if age_ms is not None and age_ms * 1e6 <= self.stale_after_ns:
            return Freshness.FRESH, age_ms
        return Freshness.STALE, age_ms

    def to_dict(self, now_mono_ns: int) -> dict:
        st, age = self.state(now_mono_ns)
        return {"source": self.name, "state": st.value, "age_ms": age, "valid": self.valid_count,
                "invalid": self.invalid_count, "stale_after_ms": self.stale_after_ns / 1e6}


@dataclass
class JointSample:
    rx_mono_ns: int
    rx_wall_ns: int
    stamp_ns: int | None              # ROS header stamp (driver clock), if present
    position: tuple | None            # canonical order, rad
    velocity: tuple | None            # canonical order, rad/s
    order: tuple | None               # message index of each canonical joint
    valid: bool
    problem: str | None = None

    @property
    def t_mono_ns(self) -> int:
        """Sample time on the host monotonic clock: the driver stamp when available."""
        if self.stamp_ns:
            return ros_stamp_to_mono_ns(self.stamp_ns, self.rx_mono_ns, self.rx_wall_ns)
        return self.rx_mono_ns

    @property
    def max_abs_vel(self) -> float | None:
        if not self.valid or self.velocity is None:
            return None
        return max(abs(v) for v in self.velocity)


def joint_sample_from_msg(names, positions, velocities, stamp_ns, rx_mono_ns, rx_wall_ns) -> JointSample:
    """Build a sample by joint name. Invalid messages are kept, flagged, and never zero-filled."""
    names = list(names or [])
    positions = list(positions or [])
    velocities = list(velocities or [])
    idx = {n: i for i, n in enumerate(names)}
    missing = [j for j in CANONICAL_JOINTS if j not in idx]
    if missing:
        return JointSample(rx_mono_ns, rx_wall_ns, stamp_ns, None, None, None, False,
                           "missing joints: " + ",".join(missing))
    order = tuple(idx[j] for j in CANONICAL_JOINTS)
    if len(positions) < len(names) or len(velocities) < len(names):
        return JointSample(rx_mono_ns, rx_wall_ns, stamp_ns, None, None, order, False,
                           f"array length mismatch (names={len(names)}, pos={len(positions)}, vel={len(velocities)})")
    pos = tuple(float(positions[i]) for i in order)
    vel = tuple(float(velocities[i]) for i in order)
    if not all(math.isfinite(v) for v in pos + vel):
        return JointSample(rx_mono_ns, rx_wall_ns, stamp_ns, pos, vel, order, False, "non-finite value")
    return JointSample(rx_mono_ns, rx_wall_ns, stamp_ns, pos, vel, order, True)


@dataclass
class MotionCriteria:
    """Operational motion definitions. Values are recorded with every run (proposed, not standard)."""
    v_still_rad_s: float = 0.01      # every joint |velocity| below this ...
    still_hold_ms: float = 250.0     # ... continuously for this long
    max_gap_ms: float = 40.0         # consecutive fresh samples may not be further apart than this
    v_move_rad_s: float = 0.05       # "moving": max joint |velocity| at or above this ...
    move_hold_ms: float = 100.0      # ... continuously for this long

    @classmethod
    def from_dict(cls, d: dict | None) -> "MotionCriteria":
        d = d or {}
        st, mv = d.get("standstill", {}), d.get("moving", {})
        return cls(v_still_rad_s=float(st.get("v_still_rad_s", cls.v_still_rad_s)),
                   still_hold_ms=float(st.get("hold_ms", cls.still_hold_ms)),
                   max_gap_ms=float(st.get("max_gap_ms", cls.max_gap_ms)),
                   v_move_rad_s=float(mv.get("v_move_rad_s", cls.v_move_rad_s)),
                   move_hold_ms=float(mv.get("hold_ms", cls.move_hold_ms)))

    def to_dict(self) -> dict:
        return {"standstill": {"v_still_rad_s": self.v_still_rad_s, "hold_ms": self.still_hold_ms,
                               "max_gap_ms": self.max_gap_ms},
                "moving": {"v_move_rad_s": self.v_move_rad_s, "hold_ms": self.move_hold_ms}}


@dataclass
class MotionResult:
    status: str                  # "reached" | "not_reached" | "undetermined" | "no_data"
    t_mono_ns: int | None        # start of the qualifying window (host monotonic)
    reason: str
    gaps: int = 0                # gaps longer than max_gap_ms (including leading/trailing)
    max_gap_ms: float = 0.0
    preceding_gap_ms: float | None = None  # time since previous sample (or interval start) at window start

    def to_dict(self) -> dict:
        return {"status": self.status, "t_mono_ns": self.t_mono_ns, "reason": self.reason, "gaps": self.gaps,
                "max_gap_ms": self.max_gap_ms, "preceding_gap_ms": self.preceding_gap_ms}


def _windowed(samples, after_ns, before_ns, criteria, predicate, hold_ms) -> MotionResult:
    """Find the first window of continuous fresh samples satisfying ``predicate`` for ``hold_ms``.

    A gap (> max_gap_ms between consecutive samples, or from the interval start/end) breaks
    the window. If no window is found and a gap could hide one, the result is undetermined.
    When a window starts right after a gap, ``preceding_gap_ms`` exposes that the true onset
    may lie inside the gap (the reported onset is then an upper bound).
    """
    pts = sorted((s for s in samples if s.valid), key=lambda s: s.t_mono_ns)
    pts = [s for s in pts if s.t_mono_ns >= after_ns and (before_ns is None or s.t_mono_ns <= before_ns)]
    if not pts:
        return MotionResult("no_data", None, "no valid joint samples in the evaluation interval")
    max_gap_ns = criteria.max_gap_ms * 1e6
    hold_ns = hold_ms * 1e6
    win_start = None
    win_gap_ms = None
    prev_t = after_ns
    gaps = 0
    worst = 0.0
    gap_since_violation = False
    for s in pts:
        t = s.t_mono_ns
        dt = t - prev_t
        worst = max(worst, dt / 1e6)
        if dt > max_gap_ns:
            gaps += 1
            win_start = None                 # continuity across the gap is unknown
            gap_since_violation = True
        if predicate(s):
            if win_start is None:
                win_start, win_gap_ms = t, dt / 1e6
            if t - win_start >= hold_ns:
                return MotionResult("reached", win_start, "criterion satisfied on fresh samples",
                                    gaps, worst, win_gap_ms)
        else:
            win_start = None
            gap_since_violation = False
        prev_t = t
    if before_ns is not None and before_ns - prev_t > max_gap_ns:
        gaps += 1
        worst = max(worst, (before_ns - prev_t) / 1e6)
        gap_since_violation = True
    if win_start is not None:
        return MotionResult("undetermined", None, "criterion held until the data ended, not for the full hold time",
                            gaps, worst)
    if gap_since_violation:
        return MotionResult("undetermined", None, "telemetry gap after the last contrary sample", gaps, worst)
    if worst * 1e6 >= hold_ns:
        return MotionResult("undetermined", None, "a telemetry gap at least as long as the hold time could hide "
                            "a qualifying window", gaps, worst)
    return MotionResult("not_reached", None, "criterion not satisfied in the evaluation interval", gaps, worst)


def find_standstill(samples, after_ns: int, criteria: MotionCriteria, before_ns: int | None = None) -> MotionResult:
    """First window after ``after_ns`` where all joints stay below v_still for still_hold_ms."""
    return _windowed(samples, after_ns, before_ns, criteria,
                     lambda s: s.max_abs_vel is not None and s.max_abs_vel < criteria.v_still_rad_s,
                     criteria.still_hold_ms)


def confirm_moving(samples, after_ns: int, criteria: MotionCriteria, before_ns: int | None = None) -> MotionResult:
    """First window after ``after_ns`` where the arm moves at or above v_move for move_hold_ms."""
    return _windowed(samples, after_ns, before_ns, criteria,
                     lambda s: s.max_abs_vel is not None and s.max_abs_vel >= criteria.v_move_rad_s,
                     criteria.move_hold_ms)


def classify_motion_now(recent, now_mono_ns: int, freshness: Freshness, criteria: MotionCriteria) -> str:
    """Live display state: 'moving', 'still', 'transition' or 'unknown' (never 'still' without fresh data)."""
    if freshness != Freshness.FRESH or not recent:
        return "unknown"
    valid = [s for s in recent if s.valid]
    if not valid:
        return "unknown"
    horizon = now_mono_ns - int(max(criteria.still_hold_ms, criteria.move_hold_ms) * 1e6)
    window = [s for s in valid if s.rx_mono_ns >= horizon]
    if len(window) < 2:
        return "unknown"
    v = [s.max_abs_vel for s in window]
    if all(x < criteria.v_still_rad_s for x in v):
        return "still"
    if all(x >= criteria.v_move_rad_s for x in v):
        return "moving"
    return "transition"
