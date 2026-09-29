"""End-to-end campaign execution through the SIMULATED transport and robot (software only)."""
import base64
import copy
import json
import os
import shutil
import sys
import tempfile
import time
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sim_stack import BENCH, ROBOT, Stack  # noqa: E402
from onedge_v8 import dataset  # noqa: E402
from onedge_v8.runner import RunnerError  # noqa: E402
from onedge_v8.sim import SimFaults, SimRobotFaults  # noqa: E402


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp(prefix="v8run_")
        self.stacks = []

    def tearDown(self):
        for s in self.stacks:
            s.close()
        shutil.rmtree(self.tmp, ignore_errors=True)

    def stack(self, **kw):
        s = Stack(self.tmp, **kw)
        self.stacks.append(s)
        return s

    def attempts(self, s, sid):
        return dataset.session_overview(s.session_dir(sid))["attempts"]


class BenchCampaignTests(Base):
    def test_full_campaign_every_attempt_recorded(self):
        s = self.stack()
        sid = s.start()["session_id"]
        s.wait_state("COMPLETED", 90)
        ov = dataset.session_overview(s.session_dir(sid))
        self.assertEqual(len(ov["attempts"]), 8)
        self.assertTrue(all(a["status"] == "completed" for a in ov["attempts"]))
        self.assertEqual(ov["end"]["counts"], {"planned": 8, "completed": 8, "skipped": 0, "unresolved": 0,
                                               "attempts": 8})
        self.assertTrue(ov["meta"]["simulated"])
        self.assertEqual(ov["meta"]["data_origin"], "software_simulation")
        by_cond = {}
        for a in ov["attempts"]:
            by_cond.setdefault(a["condition_id"], []).append(a)
        for a in by_cond["ECC-a0.50-f0"] + by_cond["ZKP-a0.50-f0"]:
            self.assertEqual(a["outcome"]["injection"], "not_planned")
            self.assertEqual(a["outcome"]["crossing"], "no_crossing_in_complete_record")   # valid data, no crossing
        for a in by_cond["ECC-a0.50-f200"] + by_cond["ZKP-a0.50-f200"]:
            summ = json.load(open(os.path.join(s.session_dir(sid), "attempts", a["attempt_id"], "summary.json"),
                                  encoding="utf-8"))
            self.assertEqual(summ["outcome"]["injection"], "processed")
            self.assertEqual(summ["outcome"]["crossing"], "crossed_while_attack_active")
            self.assertTrue(summ["model_check"]["agrees"])
            iv = summ["key_intervals"]
            self.assertEqual(iv["device_attack_to_cross"]["clock"], "device_us")
            self.assertGreater(iv["device_attack_to_cross"]["value_ms"], 0)
            self.assertGreaterEqual(iv["device_cross_to_out_low"]["value_ms"], 0)
            self.assertIn("aligned_attack_sent_to_device_processed", iv)
            self.assertEqual(summ["records"]["missing_by_sequence"], 0)
        manifest = json.load(open(os.path.join(s.session_dir(sid), "manifest.json"), encoding="utf-8"))
        self.assertTrue(any(f["path"].endswith("summary.json") for f in manifest["files"]))

    def test_raw_serial_bytes_are_all_preserved(self):
        s = self.stack(faults=SimFaults(chunk_max=7, seed=3))
        sid = s.start()["session_id"]
        s.wait_state("COMPLETED", 90)
        s.link.stop()               # freeze the byte counter (the simulated monitor keeps emitting)
        s.recorder.sync()           # and flush every chunk read so far
        recs, issues = dataset.read_jsonl(os.path.join(s.recorder.run_dir, "serial_rx_raw.jsonl"))
        self.assertFalse(issues)
        total = sum(len(base64.b64decode(r["b64"])) for r in recs)
        self.assertEqual(total, s.link.counters["bytes"])
        self.assertTrue(max(r["n"] for r in recs) <= 7)            # partial lines really happened
        ov = dataset.session_overview(s.session_dir(sid))
        self.assertTrue(all(a["status"] == "completed" for a in ov["attempts"]))

    def test_pause_between_trials_and_resume(self):
        s = self.stack()
        s.start()
        s.wait(lambda: s.runner.current is not None, 10)
        s.runner.pause("narration break")
        self.assertIsNotNone(s.runner.current)                     # the running attempt is not interrupted
        s.wait_state("PAUSED", 20)
        self.assertEqual(s.runner.status()["progress"]["attempts"], 1)
        time.sleep(0.5)
        self.assertEqual(s.runner.status()["progress"]["attempts"], 1)   # nothing started while paused
        s.runner.resume()
        s.wait_state("COMPLETED", 90)

    def test_abort_mid_trial_is_controlled_and_does_not_reconfigure(self):
        cfg = copy.deepcopy(BENCH)
        cfg["factors"]["failure_ms"] = [{"level": 1500, "purpose": "long"}]
        s = self.stack(config=cfg)
        sid = s.start()["session_id"]
        s.wait(lambda: (s.runner.current or {}).get("phase") == "failure_window", 20)
        t_abort = time.monotonic_ns()
        s.runner.abort("operator saw something")
        s.wait_state("ABORTED", 20)
        a = self.attempts(s, sid)
        self.assertEqual(len(a), 1)
        self.assertEqual(a[0]["status"], "aborted_operator")
        tx, _ = dataset.read_jsonl(os.path.join(s.session_dir(sid), "attempts", a[0]["attempt_id"], "serial_tx.jsonl"))
        after = [t for t in tx if t["t_request_mono_ns"] > t_abort]
        self.assertEqual(after, [])            # no RECOVER, no configuration (would raise D12) after abort

    def test_serial_disconnect_holds_then_retry_preserves_both_attempts(self):
        s = self.stack(faults=SimFaults(disconnect_at_s=1.6, reconnect_after_s=0.5))
        sid = s.start()["session_id"]
        s.wait_state("HOLD", 30)
        self.assertIn("failed_acquisition", s.runner.hold["reason"])
        with self.assertRaises(RunnerError):
            s.runner.decide("continue", "not allowed after a failure", "op")
        s.wait(lambda: s.link.connected, 10)
        s.runner.decide("retry", "cable reseated", "op")
        s.wait_state(("COMPLETED", "HOLD"), 90)
        a = self.attempts(s, sid)
        failed = [x for x in a if x["status"] == "failed_acquisition"]
        self.assertEqual(len(failed), 1)
        first = failed[0]
        retry = [x for x in a if x["trial_id"] == first["trial_id"] and x["attempt"] == 2]
        self.assertEqual(len(retry), 1)
        self.assertEqual(retry[0]["status"], "completed")
        ev, _ = dataset.read_jsonl(os.path.join(s.session_dir(sid), "session_events.jsonl"))
        self.assertTrue(any(e.get("event") == "operator_decision" and e.get("decision") == "retry" for e in ev))
        self.assertLess(s.link.disconnects, 5)                      # no reconnect storm

    def test_device_reset_is_detected_and_skip_is_recorded(self):
        s = self.stack(faults=SimFaults(reset_at_s=[1.6]))
        sid = s.start()["session_id"]
        s.wait_state("HOLD", 30)
        self.assertIn("reset", s.runner.hold["reason"])
        s.runner.decide("skip", "reset under investigation", "op")
        s.wait_state(("COMPLETED", "HOLD"), 90)
        ov = dataset.session_overview(s.session_dir(sid))
        failed = [a for a in ov["attempts"] if a["status"] == "failed_acquisition"]
        self.assertEqual(len(failed), 1)
        self.assertIn("reset", failed[0]["reason"])
        if s.runner.state == "COMPLETED":
            self.assertEqual(ov["end"]["counts"]["skipped"], 1)

    def test_dropped_records_are_detected_and_hold_for_review(self):
        s = self.stack(faults=SimFaults(drop_line_prob=0.25, seed=11))
        s.start()
        s.wait_state("HOLD", 60)
        self.assertIn("sequence_gap", s.runner.hold["reason"])
        self.assertIn("continue", s.runner.hold["allowed"])
        s.runner.decide("continue", "gaps noted; outside the analysis window", "op")
        s.wait(lambda: s.runner.status()["progress"]["next_index"] >= 1, 10)

    def test_legacy_firmware_protocol_runs_degraded(self):
        cfg = copy.deepcopy(BENCH)
        cfg["factors"]["workload"] = [{"level": "ECC", "purpose": "a"}]
        cfg["factors"]["failure_ms"] = [{"level": 200, "purpose": "sustained"}]
        cfg["repetitions"] = 1
        s = self.stack(config=cfg, monitor={"protocol": "legacy"})
        sid = s.start()["session_id"]
        s.wait_state(("COMPLETED", "HOLD"), 30)
        a = self.attempts(s, sid)[0]
        summ = json.load(open(os.path.join(s.session_dir(sid), "attempts", a["attempt_id"], "summary.json"),
                              encoding="utf-8"))
        self.assertEqual(summ["device_protocol"], "legacy")
        self.assertEqual(summ["outcome"]["crossing"], "undetermined_legacy_protocol")
        self.assertIn("legacy firmware protocol", " ".join(summ["notes"]))

    def test_unacknowledged_attack_is_a_procedure_failure(self):
        cfg = copy.deepcopy(BENCH)
        cfg["factors"]["failure_ms"] = [{"level": 200, "purpose": "sustained"}]
        s = self.stack(config=cfg)
        orig = s.monitor._handle_line

        def ignore_attack(line, setup=False):
            if line == "ATTACK":
                return
            orig(line, setup)
        s.monitor._handle_line = ignore_attack
        sid = s.start()["session_id"]
        s.wait_state("HOLD", 30)
        self.assertIn("ATTACK was not acknowledged", s.runner.hold["reason"])
        self.assertEqual(self.attempts(s, sid)[0]["status"], "failed_procedure")

    def test_operator_disconnect_pauses_progression(self):
        cfg = copy.deepcopy(BENCH)
        cfg["progression"]["pause_on_operator_disconnect"] = True
        s = self.stack(config=cfg)
        s.start()
        s.wait_state("PAUSED", 10)
        self.assertIn("operator connection lost", s.runner.state_reason)
        s.runner.heartbeat("dashboard-1")
        s.runner.resume()
        s.wait(lambda: s.runner.current is not None, 10)
        self.assertIsNotNone(s.runner.current)

    def test_manual_command_during_attempt_needs_confirmation_and_is_recorded(self):
        cfg = copy.deepcopy(BENCH)
        cfg["factors"]["failure_ms"] = [{"level": 0, "purpose": "control"}]
        cfg["trial"]["post_recover_ms"] = 1500
        s = self.stack(config=cfg)
        sid = s.start()["session_id"]
        s.wait(lambda: (s.runner.current or {}).get("phase") == "observe", 20)
        with self.assertRaises(RunnerError):
            s.runner.manual_command("ATTACK", "demo of manual control", "op")
        s.runner.manual_command("ATTACK", "demo of manual control", "op", confirm_departure=True)
        s.wait_state("HOLD", 20)
        a = self.attempts(s, sid)[0]
        self.assertEqual(len(a["departures"]), 1)
        self.assertIn("operator_commands_during_attempt", s.runner.hold["reason"])

    def test_config_change_without_version_bump_is_refused(self):
        s = self.stack()
        s.start()
        s.runner.abort("end quickly")
        s.wait_state("ABORTED", 20)
        path = os.path.join(s.campaign_dir, s.name)
        cfg = json.load(open(path, encoding="utf-8"))
        cfg["trial"]["baseline_ms"] = 900
        json.dump(cfg, open(path, "w", encoding="utf-8"))
        prev = s.runner.preview(s.name)
        with self.assertRaises(RunnerError):
            s.runner.start(s.name, prev["plan"]["plan_sha256"], "op")


class RobotProcedureTests(Base):
    def test_robot_trials_with_confirmation_safeguard_and_standstill(self):
        s = self.stack(config=ROBOT, robot="sim")
        with self.assertRaises(RunnerError):
            s.start()                                     # requires explicit motion acknowledgement
        sid = s.start(acks=["robot_motion_authorized"])["session_id"]
        for _ in range(2):
            s.wait_state(("AWAITING_CONFIRMATION", "COMPLETED", "HOLD"), 30)
            if s.runner.state != "AWAITING_CONFIRMATION":
                break
            s.runner.confirm_next("op", ["area clear", "e-stop reachable"])
            s.wait(lambda: s.runner.current is not None, 10)
            s.wait(lambda: s.runner.current is None, 40)
        s.wait_state(("COMPLETED", "HOLD"), 40)
        self.assertEqual(s.runner.state, "COMPLETED", s.runner.hold)
        ov = dataset.session_overview(s.session_dir(sid))
        by = {a["condition_id"]: a for a in ov["attempts"]}
        crossing = by["ECC-a0.50-f800"]
        summ = json.load(open(os.path.join(s.session_dir(sid), "attempts", crossing["attempt_id"], "summary.json"),
                              encoding="utf-8"))
        self.assertEqual(summ["motion"]["moving_before_injection"]["status"], "reached")
        self.assertEqual(summ["motion"]["standstill_after_out_low"]["status"], "reached")
        self.assertIsNotNone(summ["events"]["H_RX_SAFEGUARD"])
        self.assertIn("host_attack_sent_to_standstill", summ["key_intervals"])
        self.assertIn("aligned_out_low_to_standstill", summ["key_intervals"])
        control = by["ECC-a0.50-f0"]
        self.assertEqual(control["status"], "completed")
        # a safeguard stop pauses the sweep goal (as on the real UR5); the runner must cancel it while D12
        # is low, so it cannot resume when the next configuration closes the loop (URI, 2026-09-29)
        self.assertEqual(crossing["status"], "completed")
        evs = [json.loads(l) for l in open(os.path.join(s.session_dir(sid), "attempts", crossing["attempt_id"],
                                                       "host_events.jsonl"), encoding="utf-8")]
        self.assertTrue(any(e.get("event") == "trajectory" and e.get("status") == "canceled" for e in evs))
        self.assertFalse(s.runner.robot.trajectory_active())

    def test_decision_reason_is_optional(self):
        s = self.stack(config=ROBOT, robot="sim",
                       robot_faults=SimRobotFaults(telemetry_dropout_at_s=0.0, telemetry_dropout_s=60.0))
        s.start(acks=["robot_motion_authorized"])
        s.wait_state("AWAITING_CONFIRMATION", 20)
        s.runner.confirm_next("op")
        s.wait_state("HOLD", 30)
        s.runner.decide("skip", "", "op")
        s.wait_state(("AWAITING_CONFIRMATION", "COMPLETED", "HOLD"), 20)

    def test_telemetry_dropout_prevents_injection(self):
        s = self.stack(config=ROBOT, robot="sim",
                       robot_faults=SimRobotFaults(telemetry_dropout_at_s=0.0, telemetry_dropout_s=60.0))
        s.start(acks=["robot_motion_authorized"])
        s.wait_state("AWAITING_CONFIRMATION", 20)
        s.runner.confirm_next("op")
        s.wait_state("HOLD", 30)
        self.assertIn("joint telemetry is", s.runner.hold["reason"])

    def test_protective_stop_interrupts_progression(self):
        s = self.stack(config=ROBOT, robot="sim", robot_faults=SimRobotFaults(protective_stop_at_s=1.2))
        sid = s.start(acks=["robot_motion_authorized"])["session_id"]
        s.wait_state("AWAITING_CONFIRMATION", 20)
        s.runner.confirm_next("op")
        s.wait_state("HOLD", 30)
        self.assertIn("fault_robot", s.runner.hold["reason"])
        self.assertIn("PROTECTIVE_STOP", s.runner.hold["reason"])
        self.assertEqual(self.attempts(s, sid)[0]["status"], "fault_robot")


class RecoveryTests(Base):
    def test_interrupted_session_recovered_at_daemon_start(self):
        from onedge_v8.daemon import Daemon
        data_root = os.path.join(self.tmp, "data")
        s = self.stack()
        sid = s.start()["session_id"]
        s.wait(lambda: (s.runner.current or {}).get("phase") == "baseline", 20)
        # simulate a process crash: nothing may finalize the attempt or the session
        s.recorder.end_attempt = lambda meta: None
        s.recorder.write_derived = lambda *a, **k: None
        s.recorder.close_session = lambda *a, **k: None
        s.runner._stop = True
        s.link.stop()
        s.monitor.stop()
        s.recorder.sync()
        s.recorder.stop()
        self.stacks.remove(s)
        cfg = {"schema": "onedge.v8.daemon/1", "mode": "simulated", "data_root": data_root,
               "campaign_dir": s.campaign_dir, "api": {"port": 0, "serve_dashboard": False},
               "sim": {"monitor": {"ecc_ms": 20}}, "robot": {"interface": "none"}}
        d = Daemon(cfg)
        try:
            self.assertEqual([r["session_id"] for r in d.recovered], [sid])
            ov = dataset.session_overview(os.path.join(data_root, "sessions", sid))
            self.assertEqual(ov["attempts"][0]["status"], "interrupted")
            self.assertIsNotNone(ov["recovered"])
        finally:
            d.shutdown()


if __name__ == "__main__":
    unittest.main()
