"""Helpers that assemble the acquisition stack around the simulator for end-to-end tests."""
import copy
import json
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from onedge_v8.bus import EventBus  # noqa: E402
from onedge_v8.device_link import DeviceLink  # noqa: E402
from onedge_v8.recorder import Recorder  # noqa: E402
from onedge_v8.robot import NullRobot  # noqa: E402
from onedge_v8.runner import CampaignRunner, RobotMonitor  # noqa: E402
from onedge_v8.sim import SimFaults, SimMonitor, SimRobot, SimRobotFaults, SimTransport  # noqa: E402

FAST_MONITOR = dict(ecc_ms=20.0, zkp_mult_ms=12.0, jitter_ms=0.5, loop_delay_ms=10.0, report_cost_ms=0.1)

BENCH = {
    "schema": "onedge.v8.campaign/1", "campaign_id": "sim-bench", "config_version": 1,
    "title": "Simulated bench test", "kind": "software_test", "purpose": "end-to-end software test",
    "procedure": "bench",
    "factors": {"workload": [{"level": "ECC", "purpose": "a"}, {"level": "ZKP", "purpose": "b"}],
                "alpha": [{"level": 0.5, "purpose": "fast"}],
                "failure_ms": [{"level": 0, "purpose": "control"}, {"level": 200, "purpose": "sustained"}]},
    "design": {"type": "full_factorial"}, "repetitions": 2,
    "ordering": {"method": "randomized_complete_blocks", "seed": 7},
    "trial": {"baseline_ms": 500, "injection_jitter_ms": 40, "post_recover_ms": 300, "inter_trial_ms": 100,
              "config_ack_timeout_ms": 800, "attack_ack_timeout_ms": 500, "recover_ack_timeout_ms": 500},
    "progression": {"mode": "automatic", "pause_on_operator_disconnect": False},
}

ROBOT = {
    "schema": "onedge.v8.campaign/1", "campaign_id": "sim-robot", "config_version": 1,
    "title": "Simulated robot test", "kind": "software_test", "purpose": "robot procedure software test",
    "procedure": "robot",
    "factors": {"workload": [{"level": "ECC", "purpose": "a"}],
                "alpha": [{"level": 0.5, "purpose": "fast"}],
                "failure_ms": [{"level": 0, "purpose": "control"}, {"level": 800, "purpose": "sustained"}]},
    "design": {"type": "full_factorial"}, "repetitions": 1,
    "ordering": {"method": "fixed_blocks"},
    "trial": {"baseline_ms": 500, "injection_jitter_ms": 0, "post_recover_ms": 600, "inter_trial_ms": 100,
              "config_ack_timeout_ms": 800, "attack_ack_timeout_ms": 500, "recover_ack_timeout_ms": 500,
              "motion": {"approach_s": 2.0, "time_scale": 0.25, "inject_after_moving_ms": 200,
                         "moving_timeout_ms": 2000, "settle_timeout_ms": 3000, "trajectory_timeout_s": 8.0,
                         "program_wait_s": 5.0, "resume_program": "dashboard_play"}},
    "telemetry": {"joint_stale_ms": 100, "standstill": {"v_still_rad_s": 0.01, "hold_ms": 150, "max_gap_ms": 40},
                  "moving": {"v_move_rad_s": 0.05, "hold_ms": 60}},
    "progression": {"mode": "operator_confirm_each_trial", "pause_on_operator_disconnect": False},
}


class Stack:
    def __init__(self, tmp, config=None, monitor=None, faults=None, robot=None, robot_faults=None, name="c.json"):
        self.tmp = tmp
        self.campaign_dir = os.path.join(tmp, "campaigns")
        os.makedirs(self.campaign_dir, exist_ok=True)
        self.name = name
        cfg = copy.deepcopy(config or BENCH)
        with open(os.path.join(self.campaign_dir, name), "w", encoding="utf-8") as f:
            json.dump(cfg, f, indent=2)
        self.recorder = Recorder(os.path.join(tmp, "data"), run_meta={"test": True})
        self.bus = EventBus()
        mk = dict(FAST_MONITOR)
        mk.update(monitor or {})
        self.monitor = SimMonitor(faults=faults or SimFaults(), **mk)
        self.monitor.start()
        self.link = DeviceLink(lambda: SimTransport(self.monitor), self.recorder, self.bus, reconnect_interval_s=0.2)
        if robot == "sim":
            self.robot = SimRobot(self.monitor, rate_hz=250.0, faults=robot_faults or SimRobotFaults())
        else:
            self.robot = NullRobot()
        self.rm = RobotMonitor(self.recorder, self.bus, self.robot.capabilities())
        self.robot.start(self.rm.on_joint, self.rm.on_state, self.rm.on_event)
        self.runner = CampaignRunner(self.link, self.robot, self.rm, self.recorder, self.bus, self.campaign_dir,
                                     "simulated", {"test": True})
        self.link.start()
        self.wait(lambda: self.link.connected, 5)

    def start(self, acks=None):
        prev = self.runner.preview(self.name)
        assert prev["valid"], prev.get("problems")
        return self.runner.start(self.name, prev["plan"]["plan_sha256"], "test-operator", acks or [])

    @staticmethod
    def wait(pred, timeout):
        end = time.monotonic() + timeout
        while time.monotonic() < end:
            if pred():
                return True
            time.sleep(0.02)
        return False

    def wait_state(self, states, timeout=60):
        states = (states,) if isinstance(states, str) else states
        ok = self.wait(lambda: self.runner.state in states, timeout)
        assert ok, f"timeout waiting for {states}; state={self.runner.state} ({self.runner.state_reason})"

    def session_dir(self, sid):
        return os.path.join(self.tmp, "data", "sessions", sid)

    def close(self):
        try:
            self.runner.shutdown(timeout_s=10)
        finally:
            self.link.stop()
            self.robot.stop()
            self.monitor.stop()
            self.recorder.stop()
