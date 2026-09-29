import math
import os
import random
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from onedge_v8 import clocks as C  # noqa: E402
from onedge_v8 import telemetry as T  # noqa: E402

UR_ROS2_ORDER = ["shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint", "wrist_3_joint",
                 "shoulder_pan_joint"]


class ClockTests(unittest.TestCase):
    def test_same_clock_only(self):
        a, b = C.Stamp(C.DEVICE_US, 1000), C.Stamp(C.DEVICE_US, 251000)
        self.assertAlmostEqual(C.interval_ms(a, b), 250.0)
        with self.assertRaises(C.ClockMismatch):
            C.interval_ms(a, C.Stamp(C.HOST_MONO_NS, 5))
        with self.assertRaises(C.ClockMismatch):
            C.interval_ms(a, C.Stamp(C.DEVICE_US, 5, epoch=1))

    def test_fit_recovers_drift_and_offset(self):
        rng = random.Random(3)
        true_off, ppm = 5_000_000_000, 40.0
        pairs = []
        for k in range(300):
            dev = 1_000_000 + k * 100_000                      # 30 s span
            delay = 0.2e6 + rng.expovariate(1 / 0.5e6)          # >= 0.2 ms
            host = true_off + dev * 1000 * (1 + ppm * 1e-6) + delay
            pairs.append((dev, int(host)))
        fit = C.ClockFit.estimate(pairs)
        self.assertTrue(fit.slope_estimated)
        self.assertLess(abs(fit.ppm - ppm), 3.0)
        # mapped time is late by ~ the minimum delay (0.2 ms), never early
        mapped = fit.dev_to_host_ns(2_000_000)
        truth = true_off + 2_000_000 * 1000 * (1 + ppm * 1e-6)
        self.assertGreaterEqual(mapped - truth, 0.1e6)
        self.assertLess(mapped - truth, 0.4e6)
        self.assertGreaterEqual(fit.residual_p50_ms, 0.0)

    def test_fit_accepts_large_rc_oscillator_offset(self):
        # Nano 33 BLE on 2026-09-28: device clock ~7,200 ppm fast (992.8 host ns per device us)
        rng = random.Random(4)
        slope_true = 992.84
        pairs = [(k * 120_000, int(7e9 + slope_true * k * 120_000 + 0.3e6 + rng.expovariate(1 / 5e6)))
                 for k in range(90)]                                        # ~10.7 s span
        fit = C.ClockFit.estimate(pairs)
        self.assertTrue(fit.slope_estimated)
        self.assertLess(abs(fit.slope_ns_per_us - slope_true), 0.5)
        self.assertIn("rate offset", fit.note)
        self.assertLess(fit.residual_max_ms, 60.0)

    def test_fit_rejects_implausible_slope(self):
        pairs = [(k * 100_000, int(k * 100_000 * 1100.0)) for k in range(100)]   # +10 %
        fit = C.ClockFit.estimate(pairs)
        self.assertFalse(fit.slope_estimated)
        self.assertEqual(fit.slope_ns_per_us, 1000.0)

    def test_fit_without_enough_span_uses_nominal_slope(self):
        fit = C.ClockFit.estimate([(0, 10_000), (100_000, 100_010_000), (200_000, 200_020_000)])
        self.assertFalse(fit.slope_estimated)
        self.assertEqual(fit.slope_ns_per_us, 1000.0)

    def test_aligned_interval_carries_range(self):
        fit = C.ClockFit(1000.0, 0.0, 0, 50, 10.0, True, 0.1, 0.5, 1.0, 2.0)
        r = C.aligned_interval_ms(C.Stamp(C.HOST_MONO_NS, 100_000_000), C.Stamp(C.DEVICE_US, 150_000), fit)
        self.assertAlmostEqual(r.value_ms, 50.0)
        self.assertEqual((r.lower_ms, r.upper_ms), (48.0, 50.0))
        r = C.aligned_interval_ms(C.Stamp(C.DEVICE_US, 150_000), C.Stamp(C.HOST_MONO_NS, 200_000_000), fit)
        self.assertEqual((r.lower_ms, r.upper_ms), (50.0, 52.0))
        with self.assertRaises(C.ClockMismatch):
            C.aligned_interval_ms(C.Stamp(C.HOST_MONO_NS, 1), C.Stamp(C.HOST_MONO_NS, 2), fit)

    def test_ros_stamp_to_mono(self):
        self.assertEqual(C.ros_stamp_to_mono_ns(stamp_ns=1_000_000, rx_mono_ns=500, rx_wall_ns=1_000_900), -400)


class FreshnessTests(unittest.TestCase):
    def test_states(self):
        f = T.FreshnessMonitor("joints", stale_after_ms=100)
        self.assertEqual(f.state(0)[0], T.Freshness.MISSING)
        f.note(1_000_000_000)
        self.assertEqual(f.state(1_050_000_000)[0], T.Freshness.FRESH)
        self.assertEqual(f.state(1_200_000_000)[0], T.Freshness.STALE)
        f.note(1_210_000_000, valid=False)
        self.assertEqual(f.state(1_211_000_000)[0], T.Freshness.INVALID)
        self.assertEqual(T.FreshnessMonitor("x", 100, configured=False).state(0)[0], T.Freshness.UNAVAILABLE)


def sample(t_ms, vmax, valid=True, stamp=True):
    t = int(t_ms * 1e6)
    vel = [vmax, 0.0, 0.0, 0.0, 0.0, 0.0]
    pos = [0.1] * 6
    s = T.joint_sample_from_msg(UR_ROS2_ORDER, pos, vel, stamp_ns=(t + 7_000_000_000) if stamp else None,
                                rx_mono_ns=t + 300_000, rx_wall_ns=t + 7_000_000_000 + 300_000)
    if not valid:
        s.valid = False
    return s


class JointAndMotionTests(unittest.TestCase):
    def test_name_mapping_uses_names_not_positions(self):
        pos = [1.0, 2.0, 3.0, 4.0, 5.0, 0.5]       # message order (shoulder_lift first)
        s = T.joint_sample_from_msg(UR_ROS2_ORDER, pos, [0] * 6, None, 10, 20)
        self.assertTrue(s.valid)
        self.assertEqual(s.position, (0.5, 1.0, 2.0, 3.0, 4.0, 5.0))
        self.assertEqual(s.order, (5, 0, 1, 2, 3, 4))

    def test_invalid_messages_are_not_zero_filled(self):
        s = T.joint_sample_from_msg(UR_ROS2_ORDER[:5], [0] * 5, [0] * 5, None, 1, 1)
        self.assertFalse(s.valid)
        self.assertIsNone(s.velocity)
        self.assertIsNone(s.max_abs_vel)
        s = T.joint_sample_from_msg(UR_ROS2_ORDER, [0] * 6, [math.nan] + [0] * 5, None, 1, 1)
        self.assertFalse(s.valid)
        s = T.joint_sample_from_msg(UR_ROS2_ORDER, [0] * 6, [], None, 1, 1)
        self.assertFalse(s.valid)

    def test_stamp_time_is_used(self):
        s = sample(100, 0.0)
        self.assertEqual(s.t_mono_ns, 100_000_000)       # stamp mapped to mono, not rx time

    def crit(self):
        return T.MotionCriteria(v_still_rad_s=0.01, still_hold_ms=100, max_gap_ms=20, v_move_rad_s=0.05,
                                move_hold_ms=50)

    def test_standstill_found_on_fresh_samples(self):
        s = [sample(t, 0.5 if t < 300 else 0.001) for t in range(0, 600, 8)]
        r = T.find_standstill(s, 0, self.crit())
        self.assertEqual(r.status, "reached")
        self.assertEqual(r.t_mono_ns, 304_000_000)

    def test_gap_prevents_standstill_decision(self):
        s = [sample(t, 0.5) for t in range(0, 300, 8)] + [sample(t, 0.001) for t in range(400, 460, 8)]
        r = T.find_standstill(s, 0, self.crit())
        self.assertEqual(r.status, "undetermined")

    def test_missing_telemetry_is_never_standstill(self):
        self.assertEqual(T.find_standstill([], 0, self.crit()).status, "no_data")
        s = [sample(t, 0.5) for t in range(0, 200, 8)]
        r = T.find_standstill(s, 0, self.crit(), before_ns=int(1e9))   # data stop at 192 ms, window to 1 s
        self.assertEqual(r.status, "undetermined")
        s = [sample(t, 0.001, valid=False) for t in range(0, 600, 8)]
        self.assertEqual(T.find_standstill(s, 0, self.crit()).status, "no_data")

    def test_not_reached_with_complete_data(self):
        s = [sample(t, 0.5) for t in range(0, 600, 8)]
        self.assertEqual(T.find_standstill(s, 0, self.crit(), before_ns=int(600e6)).status, "not_reached")

    def test_window_after_gap_reports_preceding_gap(self):
        s = [sample(t, 0.5) for t in range(0, 100, 8)] + [sample(t, 0.001) for t in range(150, 400, 8)]
        r = T.find_standstill(s, 0, self.crit())
        self.assertEqual(r.status, "reached")
        self.assertGreater(r.preceding_gap_ms, 20)

    def test_confirm_moving(self):
        s = [sample(t, 0.0 if t < 100 else 0.2) for t in range(0, 400, 8)]
        r = T.confirm_moving(s, 0, self.crit())
        self.assertEqual(r.status, "reached")
        self.assertEqual(r.t_mono_ns, 104_000_000)

    def test_live_classification_unknown_when_stale(self):
        s = [sample(t, 0.001) for t in range(0, 400, 8)]
        now = s[-1].rx_mono_ns + 1_000_000
        self.assertEqual(T.classify_motion_now(s, now, T.Freshness.STALE, self.crit()), "unknown")
        self.assertEqual(T.classify_motion_now(s, now, T.Freshness.FRESH, self.crit()), "still")


if __name__ == "__main__":
    unittest.main()
