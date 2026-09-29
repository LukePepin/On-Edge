"""Clock domains, same-clock intervals, and device-to-host clock alignment.

Clock domains recorded by V8 (see docs/v8/DATASET_SCHEMA.md):

* ``device_us``   Nano micros(): 1 us resolution, 32-bit on the wire, unwrapped per device
                  epoch (boot). Only comparable within one epoch.
* ``host_mono_ns`` time.monotonic_ns() on the recording host (the Pi): used for all host
                  intervals. Not affected by wall-clock steps.
* ``host_wall_ns`` time.time_ns() on the recording host: for human reference and to relate
                  ROS header stamps (Pi system time) to host_mono_ns.
* ``ros_stamp_ns`` ROS header.stamp set by the UR driver on the Pi (system clock).

Rule enforced here: an interval may only be computed between two timestamps on the same
clock (and, for the device clock, the same epoch). Relating device time to host time
requires an explicit ClockFit whose uncertainty is carried with the result.
"""
from __future__ import annotations

from dataclasses import dataclass

DEVICE_US = "device_us"
HOST_MONO_NS = "host_mono_ns"
HOST_WALL_NS = "host_wall_ns"
ROS_STAMP_NS = "ros_stamp_ns"

_UNIT_TO_MS = {DEVICE_US: 1e-3, HOST_MONO_NS: 1e-6, HOST_WALL_NS: 1e-6, ROS_STAMP_NS: 1e-6}


class ClockMismatch(ValueError):
    """Raised when code tries to subtract timestamps from different clocks or epochs."""


@dataclass(frozen=True)
class Stamp:
    clock: str
    value: int
    epoch: int = 0

    def to_dict(self) -> dict:
        return {"clock": self.clock, "value": self.value, "epoch": self.epoch}


def interval_ms(start: Stamp, end: Stamp) -> float:
    """Elapsed time end - start in milliseconds, same clock only."""
    if start.clock != end.clock:
        raise ClockMismatch(f"cannot subtract {start.clock} from {end.clock} without alignment")
    if start.epoch != end.epoch:
        raise ClockMismatch(f"{start.clock} stamps from different epochs ({start.epoch}, {end.epoch})")
    return (end.value - start.value) * _UNIT_TO_MS[start.clock]


def _quantile(sorted_vals: list, q: float) -> float:
    if not sorted_vals:
        return float("nan")
    idx = min(len(sorted_vals) - 1, max(0, int(round(q * (len(sorted_vals) - 1)))))
    return sorted_vals[idx]


@dataclass
class ClockFit:
    """Relationship host_rx_mono_ns ~= offset_ns + slope_ns_per_us * device_us + delay.

    Estimated from (device time of a record, host receipt time of that record) pairs by a
    minimum-delay (lower envelope) method: a record cannot arrive before it was sent, so
    the fitted line lies on or below every point. The fitted offset therefore includes the
    unknown *minimum* one-way latency d_min (USB/tty path), and mapping a device instant
    to host time gives an upper estimate that is late by d_min. ``d_min_bound_ms`` is an
    ASSUMED bound on d_min (not measured by this system); cross-clock results carry the
    range [value - bound, value].

    The slope limit is wide (2 %) because the Nano 33 BLE's micros() was measured running
    ~7,200 ppm fast against the Pi on 2026-09-28 (suspected: the Mbed core leaves the nRF52840
    on its internal RC oscillator). Slopes beyond 1,000 ppm are accepted but noted.
    """

    slope_ns_per_us: float
    offset_ns: float
    epoch: int
    n_points: int
    span_s: float
    slope_estimated: bool
    residual_p50_ms: float
    residual_p95_ms: float
    residual_max_ms: float
    d_min_bound_ms: float
    note: str = ""
    slope_source: str = "nominal"      # "attempt", "context" (neighbouring records) or "nominal"

    @property
    def ppm(self) -> float:
        return (self.slope_ns_per_us / 1000.0 - 1.0) * 1e6

    def dev_to_host_ns(self, t_dev_us: int) -> float:
        return self.offset_ns + self.slope_ns_per_us * t_dev_us

    def to_dict(self) -> dict:
        return {"method": "min_delay_two_window", "epoch": self.epoch, "slope_ns_per_us": self.slope_ns_per_us,
                "offset_ns": self.offset_ns, "drift_ppm": self.ppm, "n_points": self.n_points,
                "span_s": self.span_s, "slope_estimated": self.slope_estimated,
                "residual_ms": {"p50": self.residual_p50_ms, "p95": self.residual_p95_ms,
                                "max": self.residual_max_ms},
                "assumed_min_latency_bound_ms": self.d_min_bound_ms, "note": self.note,
                "slope_source": self.slope_source}

    @classmethod
    def estimate(cls, pairs: list, epoch: int = 0, min_points: int = 20, min_span_s: float = 5.0,
                 d_min_bound_ms: float = 2.0, max_abs_ppm: float = 20000.0,
                 note_abs_ppm: float = 1000.0, slope: float | None = None, slope_note: str = ""):
        """pairs: iterable of (t_dev_us, host_rx_mono_ns) from ONE device epoch.

        ``slope``: use this rate (e.g. estimated from neighbouring records of the same epoch)
        instead of estimating it; only the offset is then fitted to ``pairs``.
        """
        pts = sorted((int(d), int(h)) for d, h in pairs)
        if len(pts) < 2:
            return None
        span_s = (pts[-1][0] - pts[0][0]) / 1e6
        fixed, slope = slope, 1000.0
        estimated = False
        note = ""
        source = "nominal"
        if fixed is not None:
            slope, estimated, source = fixed, True, "context"
            note = f"slope {fixed:.3f} ns/us ({(fixed / 1000.0 - 1.0) * 1e6:+.0f} ppm) from {slope_note or 'context'}"
        elif len(pts) >= min_points and span_s >= min_span_s:
            third = max(1, len(pts) // 3)

            def two_window(ref):
                a = min(pts[:third], key=lambda p: p[1] - ref * p[0])
                b = min(pts[-third:], key=lambda p: p[1] - ref * p[0])
                return (b[1] - a[1]) / (b[0] - a[0]) if b[0] > a[0] else None

            cand = two_window(1000.0)
            if cand is not None:
                cand = two_window(cand) or cand   # second pass: minima selected along the first estimate
            if cand is not None:
                ppm = (cand / 1000.0 - 1.0) * 1e6
                if abs(ppm) <= max_abs_ppm:
                    slope, estimated, source = cand, True, "attempt"
                    if abs(ppm) > note_abs_ppm:
                        note = (f"large device clock rate offset {ppm:+.0f} ppm (negative: device clock fast; "
                                f"oscillator likely not crystal-referenced); slope estimated from the data")
                else:
                    note = f"slope estimate {cand:.3f} ns/us rejected (> {max_abs_ppm} ppm); nominal used"
        else:
            note = f"too few points/span for slope (n={len(pts)}, span={span_s:.1f}s); nominal 1 us = 1000 ns used"
        offset = min(h - slope * d for d, h in pts)
        res = sorted((h - (offset + slope * d)) / 1e6 for d, h in pts)
        return cls(slope_ns_per_us=slope, offset_ns=offset, epoch=epoch, n_points=len(pts), span_s=span_s,
                   slope_estimated=estimated, residual_p50_ms=_quantile(res, 0.5),
                   residual_p95_ms=_quantile(res, 0.95), residual_max_ms=res[-1],
                   d_min_bound_ms=d_min_bound_ms, note=note, slope_source=source)


@dataclass
class AlignedInterval:
    value_ms: float        # upper estimate (uses the fitted line, which includes d_min)
    lower_ms: float
    upper_ms: float
    note: str

    def to_dict(self) -> dict:
        return {"value_ms": self.value_ms, "range_ms": [self.lower_ms, self.upper_ms], "note": self.note}


def aligned_interval_ms(start: Stamp, end: Stamp, fit: ClockFit) -> AlignedInterval:
    """Cross-clock interval between a host_mono_ns stamp and a device_us stamp.

    Mapping a device instant to host time is late by the unknown minimum latency
    d_min in [0, bound]. If the device stamp is the END, the true interval lies in
    [value - bound, value]; if it is the START, in [value, value + bound].
    """
    if fit is None:
        raise ClockMismatch("no clock fit available for cross-clock interval")
    b = fit.d_min_bound_ms
    if start.clock == HOST_MONO_NS and end.clock == DEVICE_US:
        if end.epoch != fit.epoch:
            raise ClockMismatch("device stamp epoch does not match clock fit")
        v = (fit.dev_to_host_ns(end.value) - start.value) / 1e6
        return AlignedInterval(v, v - b, v, "device end mapped to host clock; true value may be up to "
                               f"{b} ms earlier (assumed min-latency bound)")
    if start.clock == DEVICE_US and end.clock == HOST_MONO_NS:
        if start.epoch != fit.epoch:
            raise ClockMismatch("device stamp epoch does not match clock fit")
        v = (end.value - fit.dev_to_host_ns(start.value)) / 1e6
        return AlignedInterval(v, v, v + b, "device start mapped to host clock; true value may be up to "
                               f"{b} ms longer (assumed min-latency bound)")
    raise ClockMismatch(f"aligned interval needs one host_mono_ns and one device_us stamp, got "
                        f"{start.clock} and {end.clock}")


def ros_stamp_to_mono_ns(stamp_ns: int, rx_mono_ns: int, rx_wall_ns: int) -> int:
    """Express a ROS header stamp (Pi system clock) on the host monotonic clock.

    Uses the wall/monotonic offset captured when the message was received on the same
    machine. Valid while the system clock is not stepped between stamp and receipt.
    """
    return stamp_ns - (rx_wall_ns - rx_mono_ns)
