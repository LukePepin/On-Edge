"""Dashboard server: mode separation, exclusions API, verified sync (software only)."""
import json
import os
import shutil
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "dashboard"))

import server as dash  # noqa: E402
from onedge_v8 import dataset  # noqa: E402
from onedge_v8.daemon import Daemon  # noqa: E402


def req(url, method="GET", body=None):
    data = json.dumps(body or {}).encode() if method == "POST" else None
    r = urllib.request.Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(r, timeout=10) as resp:
            return resp.status, json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read().decode())


class DashboardServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.mkdtemp(prefix="v8dash_")
        camp = os.path.join(cls.tmp, "campaigns")
        os.makedirs(camp)
        cfg = json.load(open(os.path.join(HERE, "..", "config", "campaigns", "sim_smoke.json"), encoding="utf-8"))
        cfg["factors"]["workload"] = cfg["factors"]["workload"][:1]
        cfg["factors"]["alpha"] = cfg["factors"]["alpha"][1:]
        cfg["factors"]["failure_ms"] = [{"level": 300, "purpose": "sustained"}]
        cfg["trial"].update({"baseline_ms": 500, "post_recover_ms": 300, "inter_trial_ms": 50})
        cfg["progression"]["pause_on_operator_disconnect"] = False
        with open(os.path.join(camp, "t.json"), "w", encoding="utf-8") as f:
            json.dump(cfg, f)
        cls.pi_root = os.path.join(cls.tmp, "pi_data")
        cls.daemon = Daemon({"schema": "onedge.v8.daemon/1", "mode": "simulated", "data_root": cls.pi_root,
                             "campaign_dir": camp, "api": {"port": 0, "serve_dashboard": False},
                             "sim": {"monitor": {"ecc_ms": 20, "zkp_mult_ms": 12}}, "robot": {"interface": "none"}})
        cls.pi = f"http://127.0.0.1:{cls.daemon.server.port}"
        prev = cls.daemon.runner.preview("t.json")
        cls.sid = cls.daemon.runner.start("t.json", prev["plan"]["plan_sha256"], "test")["session_id"]
        deadline = time.monotonic() + 60
        while cls.daemon.runner.state != "COMPLETED" and time.monotonic() < deadline:
            time.sleep(0.1)
        cls.mirror = os.path.join(cls.tmp, "mirror")
        cls.sim_root = os.path.join(cls.tmp, "sim_local")
        cls.d = dash.Dashboard(cls.pi, {"mirror": cls.mirror, "sim": cls.sim_root}, 0)
        cls.d.server.start()
        cls.url = f"http://127.0.0.1:{cls.d.server.port}"
        cls.replay_only = dash.Dashboard(None, {"mirror": cls.mirror, "sim": cls.sim_root}, 0)
        cls.replay_only.server.start()
        cls.url_ro = f"http://127.0.0.1:{cls.replay_only.server.port}"

    @classmethod
    def tearDownClass(cls):
        cls.d.server.stop()
        cls.replay_only.server.stop()
        cls.daemon.shutdown()
        shutil.rmtree(cls.tmp, ignore_errors=True)

    def test_campaign_completed_through_daemon(self):
        self.assertEqual(self.daemon.runner.state, "COMPLETED")

    def test_replay_only_dashboard_cannot_send_controls(self):
        code, body = req(f"{self.url_ro}/api/live/campaign/abort", "POST", {"reason": "x"})
        self.assertEqual(code, 503)
        code, _ = req(f"{self.url_ro}/api/local/info")
        self.assertEqual(code, 200)

    def test_replay_routes_are_read_only(self):
        code, _ = req(f"{self.url}/api/replay/sim/sessions", "POST", {})
        self.assertEqual(code, 404)
        code, _ = req(f"{self.url}/api/live/sessions", "POST", {})      # not a control prefix
        self.assertEqual(code, 404)

    def test_live_proxy_and_control_gating(self):
        code, st = req(f"{self.url}/api/live/status")
        self.assertEqual(code, 200)
        self.assertTrue(st["simulated"])
        code, body = req(f"{self.url}/api/live/campaign/resume", "POST", {"operator": "t"})
        self.assertEqual(code, 409)                     # runner refuses: nothing paused

    def test_sync_is_verified_and_never_overwrites(self):
        code, rep = req(f"{self.url}/api/sync", "POST", {})
        self.assertEqual(code, 200)
        self.assertEqual(rep["root"], "sim")            # simulated source goes to the simulated root
        s = [x for x in rep["sessions"] if x["session_id"] == self.sid][0]
        local = os.path.join(self.sim_root, "sessions", self.sid)
        man = dataset.build_manifest(os.path.join(self.pi_root, "sessions", self.sid))
        self.assertEqual(s["copied"] + s["unchanged"], len(man["files"]))   # independent of test order
        self.assertGreater(len(man["files"]), 5)
        self.assertEqual(s["conflicts"], [])
        for f in man["files"]:
            self.assertEqual(dataset.sha256_file(os.path.join(local, f["path"])), f["sha256"])
        code, rep2 = req(f"{self.url}/api/sync", "POST", {})
        s2 = [x for x in rep2["sessions"] if x["session_id"] == self.sid][0]
        self.assertEqual(s2["copied"], 0)
        victim = os.path.join(local, "session.json")
        with open(victim, "a", encoding="utf-8") as f:
            f.write("\n")                              # local copy now differs
        before = dataset.sha256_file(victim)
        code, rep3 = req(f"{self.url}/api/sync", "POST", {})
        s3 = [x for x in rep3["sessions"] if x["session_id"] == self.sid][0]
        self.assertIn("session.json", s3["conflicts"])
        self.assertEqual(dataset.sha256_file(victim), before)   # not overwritten

    def test_exclusion_roundtrip_via_api(self):
        req(f"{self.url}/api/sync", "POST", {})
        code, ov = req(f"{self.url}/api/replay/sim/sessions/{self.sid}")
        self.assertEqual(code, 200)
        aid = ov["attempts"][0]["attempt_id"]
        code, err = req(f"{self.url}/api/exclusions/sim", "POST",
                        {"action": "exclude", "session_id": self.sid, "attempt_id": aid, "reason": "no"})
        self.assertEqual(code, 400)                     # reason too short
        code, _ = req(f"{self.url}/api/exclusions/sim", "POST",
                      {"action": "exclude", "session_id": self.sid, "attempt_id": aid,
                       "reason": "test exclusion reason", "operator": "t"})
        self.assertEqual(code, 200)
        code, ov = req(f"{self.url}/api/replay/sim/sessions/{self.sid}")
        self.assertEqual(ov["exclusion_counts"]["excluded"], 1)
        self.assertEqual(ov["attempts"][0]["exclusions"], ["all"])
        code, _ = req(f"{self.url}/api/exclusions/sim", "POST",
                      {"action": "restore", "session_id": self.sid, "attempt_id": aid, "reason": "restored in test"})
        code, ov = req(f"{self.url}/api/replay/sim/sessions/{self.sid}")
        self.assertEqual(ov["exclusion_counts"]["excluded"], 0)
        code, pay = req(f"{self.url}/api/replay/sim/sessions/{self.sid}/attempts/{aid}")
        self.assertEqual(code, 200)
        self.assertIn("updates", pay["series"])
        self.assertTrue(pay["start"]["simulated"])

    def test_path_traversal_rejected(self):
        code, _ = req(f"{self.pi}/api/sessions/{self.sid}/file?path=../../../etc/passwd")
        self.assertEqual(code, 403)


if __name__ == "__main__":
    unittest.main()
