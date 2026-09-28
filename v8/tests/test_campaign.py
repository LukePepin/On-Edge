import copy
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from onedge_v8 import campaign as C  # noqa: E402

BASE = {
    "schema": "onedge.v8.campaign/1",
    "campaign_id": "unit-test",
    "config_version": 1,
    "title": "Unit test campaign",
    "kind": "software_test",
    "purpose": "Exercise validation and plan generation.",
    "procedure": "bench",
    "factors": {
        "workload": [{"level": "ECC", "purpose": "baseline workload"},
                     {"level": "ZKP", "purpose": "heavier workload"}],
        "alpha": [{"level": 0.3, "purpose": "mid weight"}, {"level": 0.5, "purpose": "fast"}],
        "failure_ms": [{"level": 0, "purpose": "no-injection control"}, {"level": 250, "purpose": "brief"},
                       {"level": 1000, "purpose": "sustained"}],
    },
    "design": {"type": "full_factorial"},
    "repetitions": 3,
    "ordering": {"method": "randomized_complete_blocks", "seed": 1234},
}


class RecurrenceTests(unittest.TestCase):
    def test_updates_to_cross_match_study_guide(self):
        self.assertEqual(C.attacked_updates_to_cross(0.1), 12)
        self.assertEqual(C.attacked_updates_to_cross(0.3), 4)
        self.assertEqual(C.attacked_updates_to_cross(0.5), 2)

    def test_float32_sequence_prints_like_firmware(self):
        t, seq = 100.0, []
        for _ in range(5):
            t = C.firmware_trust_update(t, 0.3, 0.0)
            seq.append(f"{t:.2f}")
        self.assertEqual(seq, ["70.00", "49.00", "34.30", "24.01", "16.81"])

    def test_recovery_update(self):
        self.assertAlmostEqual(C.firmware_trust_update(25.0, 0.5, 100.0), 62.5, places=4)


class ValidationTests(unittest.TestCase):
    def test_valid_config_builds_plan(self):
        plan = C.build_plan(BASE)
        self.assertEqual(plan["n_conditions"], 12)
        self.assertEqual(plan["n_trials"], 36)
        self.assertEqual(len({t["trial_id"] for t in plan["trials"]}), 36)
        self.assertEqual(plan["ordering"]["seed"], 1234)

    def test_problems_are_collected(self):
        bad = copy.deepcopy(BASE)
        bad["factors"]["alpha"][0]["level"] = 1.5
        bad["factors"]["failure_ms"].append({"level": 250, "purpose": "dup"})
        bad["factors"]["workload"][0].pop("purpose")
        bad["ordering"] = {"method": "randomized"}
        bad["repetitions"] = 0
        probs = C.validate(C.normalize(bad))
        joined = " | ".join(probs)
        for needle in ("alpha must be a number", "duplicate levels", "'purpose' text required",
                       "ordering.seed", "repetitions"):
            self.assertIn(needle, joined)
        with self.assertRaises(C.ConfigError) as ctx:
            C.build_plan(bad)
        self.assertGreaterEqual(len(ctx.exception.problems), 5)

    def test_unknown_workload_rejected(self):
        bad = copy.deepcopy(BASE)
        bad["factors"]["workload"].append({"level": "REAL_ZKP", "purpose": "not implemented"})
        self.assertTrue(any("workload must be one of" in p for p in C.validate(C.normalize(bad))))

    def test_robot_requires_operator_confirmation(self):
        cfg = copy.deepcopy(BASE)
        cfg["procedure"] = "robot"
        cfg["progression"] = {"mode": "automatic", "pause_on_operator_disconnect": True}
        self.assertTrue(any("robot procedures require" in p for p in C.validate(C.normalize(cfg))))

    def test_robot_timing_must_fit_sweep(self):
        cfg = copy.deepcopy(BASE)
        cfg["procedure"] = "robot"
        cfg["factors"]["failure_ms"].append({"level": 9000, "purpose": "too long"})
        self.assertTrue(any("exceeds the 8.5 s" in p for p in C.validate(C.normalize(cfg))))

    def test_approved_status_needs_approver(self):
        cfg = copy.deepcopy(BASE)
        cfg["status"] = "approved"
        self.assertTrue(any("approved_by" in p for p in C.validate(C.normalize(cfg))))


class OrderingTests(unittest.TestCase):
    def test_seed_reproducible_and_seed_sensitive(self):
        a = [t["condition_id"] for t in C.build_plan(BASE)["trials"]]
        b = [t["condition_id"] for t in C.build_plan(BASE)["trials"]]
        other = copy.deepcopy(BASE)
        other["ordering"]["seed"] = 99
        c = [t["condition_id"] for t in C.build_plan(other)["trials"]]
        self.assertEqual(a, b)
        self.assertNotEqual(a, c)

    def test_complete_blocks_contain_each_condition_once(self):
        plan = C.build_plan(BASE)
        for block in (1, 2, 3):
            ids = [t["condition_id"] for t in plan["trials"] if t["block"] == block]
            self.assertEqual(len(ids), 12)
            self.assertEqual(len(set(ids)), 12)

    def test_jitter_within_bounds_and_recorded(self):
        plan = C.build_plan(BASE)
        js = [t["injection_jitter_ms"] for t in plan["trials"]]
        self.assertTrue(all(0 <= j <= 300 for j in js))
        self.assertGreater(len(set(js)), 5)

    def test_explicit_sequence(self):
        cfg = copy.deepcopy(BASE)
        cfg["ordering"] = {"method": "explicit_sequence",
                           "sequence": ["ECC-a0.50-f1000", "ECC-a0.50-f0", "ECC-a0.50-f1000"]}
        plan = C.build_plan(cfg)
        self.assertEqual([t["condition_id"] for t in plan["trials"]],
                         ["ECC-a0.50-f1000", "ECC-a0.50-f0", "ECC-a0.50-f1000"])
        self.assertEqual([t["repetition"] for t in plan["trials"]], [1, 1, 2])
        cfg["ordering"]["sequence"] = ["NOPE"]
        with self.assertRaises(C.ConfigError):
            C.build_plan(cfg)

    def test_plan_hash_changes_with_config(self):
        h1 = C.build_plan(BASE)["plan_sha256"]
        cfg = copy.deepcopy(BASE)
        cfg["trial"] = {"baseline_ms": 3000}
        self.assertNotEqual(h1, C.build_plan(cfg)["plan_sha256"])

    def test_model_expectations_are_labeled(self):
        plan = C.build_plan(BASE)
        for c in plan["conditions"]:
            self.assertEqual(c["model"]["label"], "MODEL")
        by = {c["condition_id"]: c["model"]["expectation"] for c in plan["conditions"]}
        self.assertIn("ends before crossing", by["ZKP-a0.30-f250"])
        self.assertIn("crossing likely", by["ECC-a0.30-f1000"])
        self.assertEqual(by["ECC-a0.50-f0"], "no injection (control)")


if __name__ == "__main__":
    unittest.main()
