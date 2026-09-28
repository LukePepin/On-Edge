import json
import os
import shutil
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from onedge_v8 import dataset as D  # noqa: E402
from onedge_v8.exclusions import ExclusionError, ExclusionRegistry  # noqa: E402
from onedge_v8.recorder import Recorder, RecorderError  # noqa: E402
from onedge_v8.telemetry import joint_sample_from_msg  # noqa: E402

NAMES = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint", "wrist_1_joint", "wrist_2_joint",
         "wrist_3_joint"]


def tree_hashes(root):
    out = {}
    for d, _, files in os.walk(root):
        for f in files:
            p = os.path.join(d, f)
            out[os.path.relpath(p, root)] = D.sha256_file(p)
    return out


class RecorderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="v8rec_")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_full_lifecycle_and_immutability(self):
        r = Recorder(self.tmp, run_meta={"test": True}, fsync_interval_s=0.2)
        r.record_raw_serial(b"before session\n", 1, 1)
        r.record("device", {"rx_mono_ns": 1, "note": "no session yet"})
        sdir = r.open_session("S1", {"session_id": "S1"}, plan={"trials": []}, config_text='{"a": 1}')
        with self.assertRaises(FileExistsError):
            Recorder(self.tmp, run_id=r.run_id)          # run dir cannot be reused
        r.record("device", {"rx_mono_ns": 2, "note": "between attempts"})
        adir = r.begin_attempt("T001_A1", {"trial_id": "T001", "attempt": 1})
        with self.assertRaises(RecorderError):
            r.begin_attempt("T002_A1", {})
        r.record_raw_serial(b'{"ev":"upd"}\n', 3, 3)
        r.record("device", {"rx_mono_ns": 3, "status": "ok"})
        r.record("tx", {"cmd": "ATTACK"})
        s = joint_sample_from_msg(NAMES, [0.1] * 6, [0.0] * 6, 5, 6, 7)
        self.assertTrue(r.record_joint(s))
        r.end_attempt({"status": "completed"})
        self.assertFalse(r.record_joint(s))               # outside attempts: not recorded
        with self.assertRaises(FileExistsError):
            os.mkdir(adir)
        r.close_session({"final_state": "completed"}, manifest_fn=D.build_manifest)
        r.stop()
        self.assertTrue(r.healthy, r.errors)
        # run log captured everything, including bytes outside the session
        raw_run, _ = D.read_jsonl(os.path.join(r.run_dir, "serial_rx_raw.jsonl"))
        self.assertEqual(len(raw_run), 2)
        raw_sess, _ = D.read_jsonl(os.path.join(sdir, "serial_rx_raw.jsonl"))
        self.assertEqual(len(raw_sess), 1)
        self.assertEqual(raw_sess[0]["attempt_id"], "T001_A1")
        nos, _ = D.read_jsonl(os.path.join(r.run_dir, "device_msgs_nosession.jsonl"))
        idle, _ = D.read_jsonl(os.path.join(sdir, "device_msgs_idle.jsonl"))
        self.assertEqual((len(nos), len(idle)), (1, 1))
        att = D.load_attempt(adir)
        self.assertEqual(att["status"], "completed")
        self.assertEqual(len(att["device"]), 1)
        self.assertEqual(len(att["joints"]), 1)
        with open(os.path.join(sdir, "manifest.json"), encoding="utf-8") as f:
            man = json.load(f)
        for f in man["files"]:
            self.assertEqual(D.sha256_file(os.path.join(sdir, f["path"])), f["sha256"])
        idx, _ = D.read_jsonl(os.path.join(sdir, "attempts.jsonl"))
        self.assertEqual([e["event"] for e in idx], ["attempt_started", "attempt_ended"])

    def test_session_ids_are_never_reused(self):
        r = Recorder(self.tmp)
        r.open_session("S1", {})
        r.close_session({})
        with self.assertRaises(FileExistsError):
            r.open_session("S1", {})
        r.stop()

    def test_interrupted_attempt_is_recovered_without_modifying_data(self):
        r = Recorder(self.tmp)
        sdir = r.open_session("S2", {"session_id": "S2"})
        adir = r.begin_attempt("T001_A1", {"trial_id": "T001"})
        for i in range(5):
            r.record("device", {"rx_mono_ns": 100 + i, "status": "ok"})
        r.sync()
        r.stop()                                   # "crash": no end_attempt / close_session
        with open(os.path.join(adir, "device_msgs.jsonl"), "a", encoding="utf-8") as f:
            f.write('{"rx_mono_ns": 999, "stat')   # truncated final line
        before = tree_hashes(sdir)
        recs, issues = D.read_jsonl(os.path.join(adir, "device_msgs.jsonl"))
        self.assertEqual(len(recs), 5)
        self.assertEqual(issues[0]["issue"], "truncated_final_line")
        self.assertEqual(D.load_attempt(adir)["status"], "unfinalized")
        marked = D.recover_session(sdir)
        self.assertEqual(marked, ["T001_A1"])
        after = tree_hashes(sdir)
        for k, v in before.items():
            self.assertEqual(after[k], v, f"{k} was modified by recovery")
        self.assertIn(os.path.join("attempts", "T001_A1", "attempt_recovered.json"), after)
        self.assertIn("session_recovered.json", after)
        self.assertEqual(D.load_attempt(adir)["status"], "interrupted")
        self.assertEqual(D.recover_session(sdir), [])          # idempotent
        ov = D.session_overview(sdir)
        self.assertEqual(ov["attempts"][0]["status"], "interrupted")

    def test_safe_join_blocks_traversal(self):
        self.assertTrue(D.safe_join(self.tmp, "a/b.json").startswith(os.path.abspath(self.tmp)))
        with self.assertRaises(ValueError):
            D.safe_join(self.tmp, "../outside.txt")


class ExclusionTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="v8exc_")
        self.reg = ExclusionRegistry(self.tmp)
        os.makedirs(os.path.join(self.tmp, "sessions", "S1"))
        with open(os.path.join(self.tmp, "sessions", "S1", "raw.txt"), "w") as f:
            f.write("raw data")

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def test_exclude_restore_history_counts(self):
        raw_before = tree_hashes(os.path.join(self.tmp, "sessions"))
        with self.assertRaises(ExclusionError):
            self.reg.exclude("S1", "T001_A1", "bad")                     # reason too short
        self.reg.exclude("S1", "T001_A1", "operator bumped the cable", operator="luke")
        self.reg.exclude("S1", "T002_A1", "comparison plot only: robot slowed", scopes=["comparison_plots"])
        self.assertTrue(self.reg.is_excluded("S1", "T001_A1"))
        self.assertTrue(self.reg.is_excluded("S1", "T002_A1", "comparison_plots"))
        self.assertFalse(self.reg.is_excluded("S1", "T002_A1", "timing_analysis"))
        c = self.reg.counts("S1", ["T001_A1", "T002_A1", "T003_A1"])
        self.assertEqual((c["total"], c["excluded"], c["included"]), (3, 1, 2))
        self.reg.restore("S1", "T001_A1", "cable issue was after the measurement window")
        self.assertFalse(self.reg.is_excluded("S1", "T001_A1"))
        with self.assertRaises(ExclusionError):
            self.reg.restore("S1", "T001_A1", "already restored, should fail")
        hist = self.reg.history("S1", "T001_A1")
        self.assertEqual([h["action"] for h in hist], ["exclude", "restore"])
        self.assertEqual(tree_hashes(os.path.join(self.tmp, "sessions")), raw_before)
        self.assertTrue(os.path.exists(os.path.join(self.tmp, "annotations", "exclusions.jsonl")))

    def test_unknown_scope_rejected(self):
        with self.assertRaises(ExclusionError):
            self.reg.exclude("S1", "T001_A1", "a valid long reason", scopes=["everything"])


if __name__ == "__main__":
    unittest.main()
