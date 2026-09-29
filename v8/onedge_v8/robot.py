"""Robot interfaces used by the campaign runner.

Interface (duck-typed; SimRobot in sim.py implements the same methods):
  kind, simulated, capabilities() -> dict
  start(on_joint, on_robot_state, on_event), stop()
  send_trajectory(phase, joint_names, points), cancel_trajectory()
  dashboard(command) -> {"ok", "response", ...}
  controller_ok() -> (bool, text)

NullRobot   bench mode: no robot telemetry (reported as UNAVAILABLE, never as zero motion).
RosRobot    ROS 2 Humble on the Pi: /joint_states, UR driver safety mode / program state,
            FollowJointTrajectory on the passthrough controller (as the historical node).
URDashboard TCP client for the UR dashboard server (port 29999) with an allowlist.
"""
from __future__ import annotations

import socket
import threading
import time

from .telemetry import joint_sample_from_msg

READ_ONLY_DASHBOARD = {"robotmode", "safetymode", "safetystatus", "programState", "running", "polyscopeVersion",
                       "get robot model", "get serial number", "is in remote control", "get loaded program",
                       "isProgramSaved"}
STATE_CHANGING_DASHBOARD = {"play", "pause", "stop", "close safety popup", "close popup", "unlock protective stop"}


class NullRobot:
    kind = "none"
    simulated = False

    def capabilities(self) -> dict:
        return {"joint_telemetry": False, "safety_mode": False, "program_state": False, "trajectory": False,
                "dashboard": False, "simulated": False}

    def start(self, on_joint, on_robot_state, on_event):
        pass

    def stop(self):
        pass

    def send_trajectory(self, phase, joint_names, points):
        raise RuntimeError("no robot interface configured (bench mode)")

    def cancel_trajectory(self):
        pass

    def trajectory_active(self) -> bool:
        return False

    def dashboard(self, command: str) -> dict:
        return {"ok": False, "response": "no robot interface configured"}

    def controller_ok(self):
        return False, "no robot interface configured"

    def activate_trajectory_controller(self):
        return False, "no robot interface configured"


class URDashboard:
    """One TCP connection per command: banner, command line, one response line."""

    def __init__(self, host: str, port: int = 29999, timeout_s: float = 2.0):
        self.host, self.port, self.timeout_s = host, port, timeout_s

    def command(self, cmd: str) -> dict:
        cmd = cmd.strip()
        if cmd not in READ_ONLY_DASHBOARD and cmd not in STATE_CHANGING_DASHBOARD:
            return {"ok": False, "response": f"command not in allowlist: {cmd!r}"}
        t0 = time.monotonic_ns()
        try:
            with socket.create_connection((self.host, self.port), timeout=self.timeout_s) as s:
                f = s.makefile("rwb")
                banner = f.readline().decode("utf-8", "replace").strip()
                f.write((cmd + "\n").encode())
                f.flush()
                resp = f.readline().decode("utf-8", "replace").strip()
            return {"ok": True, "command": cmd, "banner": banner, "response": resp,
                    "t_send_mono_ns": t0, "t_resp_mono_ns": time.monotonic_ns()}
        except OSError as exc:
            return {"ok": False, "command": cmd, "response": f"dashboard server error: {exc}",
                    "t_send_mono_ns": t0, "t_resp_mono_ns": time.monotonic_ns()}


class RosRobot:
    """ROS 2 interface (rclpy imported lazily; source the ROS setup before starting)."""
    kind = "ros"
    simulated = False

    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.joint_topic = cfg.get("joint_topic", "/joint_states")
        self.safety_topic = cfg.get("safety_mode_topic", "/io_and_status_controller/safety_mode")
        self.program_topic = cfg.get("program_running_topic", "/io_and_status_controller/robot_program_running")
        self.action_name = cfg.get("trajectory_action", "/passthrough_trajectory_controller/follow_joint_trajectory")
        self.controller_name = cfg.get("trajectory_controller", "passthrough_trajectory_controller")
        self.dash = URDashboard(cfg["ur_host"], int(cfg.get("dashboard_port", 29999))) if cfg.get("ur_host") else None
        self._caps = {"joint_telemetry": False, "safety_mode": False, "program_state": False, "trajectory": False,
                      "dashboard": self.dash is not None, "simulated": False}
        self._node = None
        self._goal = None
        self._lock = threading.Lock()
        self.import_errors = []

    def capabilities(self) -> dict:
        return dict(self._caps)

    def start(self, on_joint, on_robot_state, on_event):
        import rclpy
        from rclpy.executors import MultiThreadedExecutor
        from rclpy.node import Node
        from rclpy.qos import DurabilityPolicy, HistoryPolicy, QoSProfile, ReliabilityPolicy
        from sensor_msgs.msg import JointState

        self._on_event = on_event
        if not rclpy.ok():
            rclpy.init()
        node = Node("onedge_v8_acquisition")
        self._node = node
        rel = ReliabilityPolicy.BEST_EFFORT if self.cfg.get("joint_qos") == "best_effort" else ReliabilityPolicy.RELIABLE
        qos = QoSProfile(depth=200, reliability=rel, history=HistoryPolicy.KEEP_LAST)
        # io_and_status_controller publishes safety mode and program state latched, on change only
        # (verified 2026-09-29): subscribe TRANSIENT_LOCAL to receive the current value at startup
        state_qos = QoSProfile(depth=10, reliability=ReliabilityPolicy.RELIABLE, history=HistoryPolicy.KEEP_LAST,
                               durability=DurabilityPolicy.TRANSIENT_LOCAL)

        def joint_cb(msg):
            rx_mono, rx_wall = time.monotonic_ns(), time.time_ns()
            stamp = msg.header.stamp.sec * 1_000_000_000 + msg.header.stamp.nanosec
            on_joint(joint_sample_from_msg(msg.name, msg.position, msg.velocity, stamp or None, rx_mono, rx_wall))

        node.create_subscription(JointState, self.joint_topic, joint_cb, qos)
        self._caps["joint_telemetry"] = True
        try:
            from ur_dashboard_msgs.msg import SafetyMode

            def safety_cb(msg):
                on_robot_state("safety_mode", int(msg.mode), _safety_name(int(msg.mode)))
            node.create_subscription(SafetyMode, self.safety_topic, safety_cb, state_qos)
            self._caps["safety_mode"] = True
        except ImportError as exc:
            self.import_errors.append(f"safety mode unavailable: {exc}")
        try:
            from std_msgs.msg import Bool
            node.create_subscription(Bool, self.program_topic,
                                     lambda m: on_robot_state("program_running", int(m.data), str(bool(m.data))),
                                     state_qos)
            self._caps["program_state"] = True
        except ImportError as exc:
            self.import_errors.append(f"program state unavailable: {exc}")
        try:
            from control_msgs.action import FollowJointTrajectory
            from rclpy.action import ActionClient
            self._FJT = FollowJointTrajectory
            self._action = ActionClient(node, FollowJointTrajectory, self.action_name)
            self._caps["trajectory"] = True
        except ImportError as exc:
            self.import_errors.append(f"trajectory unavailable: {exc}")
        self._executor = MultiThreadedExecutor(num_threads=3)
        self._executor.add_node(node)
        threading.Thread(target=self._spin, name="ros-executor", daemon=True).start()

    def _spin(self):
        try:
            self._executor.spin()
        except Exception as exc:  # executor shutdown or ROS error
            self._on_event({"event": "ros_executor_stopped", "error": str(exc)})

    def stop(self):
        try:
            if self._executor:
                self._executor.shutdown(timeout_sec=1.0)
            if self._node:
                self._node.destroy_node()
        except Exception:
            pass

    def send_trajectory(self, phase: int, joint_names, points):
        from trajectory_msgs.msg import JointTrajectoryPoint
        if not self._caps["trajectory"]:
            raise RuntimeError("trajectory action unavailable")
        if not self._action.server_is_ready():
            self._on_event({"event": "trajectory", "phase": phase, "status": "rejected",
                            "reason": f"action server {self.action_name} not ready"})
            return
        goal = self._FJT.Goal()
        goal.trajectory.joint_names = list(joint_names)
        for pos, t in points:
            pt = JointTrajectoryPoint()
            pt.positions = [float(p) for p in pos]
            pt.time_from_start.sec = int(t)
            pt.time_from_start.nanosec = int(round((t - int(t)) * 1e9))
            goal.trajectory.points.append(pt)
        self._on_event({"event": "trajectory", "phase": phase, "status": "sent"})
        fut = self._action.send_goal_async(goal)

        def on_goal(f):
            gh = f.result()
            if not gh.accepted:
                self._on_event({"event": "trajectory", "phase": phase, "status": "rejected",
                                "reason": "goal rejected by controller"})
                return
            with self._lock:
                self._goal = gh
            self._on_event({"event": "trajectory", "phase": phase, "status": "accepted"})
            gh.get_result_async().add_done_callback(lambda r: on_result(r))

        def on_result(r):
            res = r.result()
            code = getattr(res.result, "error_code", None)
            status = {4: "succeeded", 5: "canceled", 6: "aborted"}.get(getattr(res, "status", None), "finished")
            with self._lock:
                self._goal = None
            self._on_event({"event": "trajectory", "phase": phase, "status": status, "error_code": code,
                            "error_string": getattr(res.result, "error_string", "")})

        fut.add_done_callback(on_goal)

    def cancel_trajectory(self):
        with self._lock:
            gh = self._goal
        if gh is not None:
            gh.cancel_goal_async()
            self._on_event({"event": "trajectory", "status": "cancel_requested"})

    def trajectory_active(self) -> bool:
        """True while a goal sent by this process has no result. A goal left by an earlier daemon
        run is not visible here: stop the External Control program at the pendant after a fault."""
        with self._lock:
            return self._goal is not None

    def dashboard(self, command: str) -> dict:
        if self.dash is None:
            return {"ok": False, "response": "ur_host not configured"}
        return self.dash.command(command)

    def activate_trajectory_controller(self):
        """Same switch as the historical wrapper after Play (ros2 control switch_controllers --activate
        passthrough_trajectory_controller --deactivate scaled_joint_trajectory_controller
        forward_position_controller), as a service call with BEST_EFFORT strictness."""
        try:
            from controller_manager_msgs.srv import SwitchController
        except ImportError as exc:
            return False, f"controller_manager_msgs unavailable: {exc}"
        cli = self._node.create_client(SwitchController, "/controller_manager/switch_controller")
        if not cli.wait_for_service(timeout_sec=2.0):
            return False, "switch_controller service not available"
        req = SwitchController.Request()
        act = [self.controller_name]
        deact = list(self.cfg.get("deactivate_controllers",
                                  ["scaled_joint_trajectory_controller", "forward_position_controller"]))
        if hasattr(req, "activate_controllers"):
            req.activate_controllers, req.deactivate_controllers = act, deact
        else:
            req.start_controllers, req.stop_controllers = act, deact
        req.strictness = 1                       # BEST_EFFORT: inactive controllers are not an error
        if hasattr(req, "activate_asap"):
            req.activate_asap = True
        fut = cli.call_async(req)
        deadline = time.monotonic() + 5.0
        while not fut.done() and time.monotonic() < deadline:
            time.sleep(0.02)
        if not fut.done():
            return False, "switch_controller timed out"
        return bool(fut.result().ok), f"activate {act}, deactivate {deact}: ok={fut.result().ok}"

    def controller_ok(self):
        """Read-only check that the trajectory controller is active (controller_manager)."""
        try:
            from controller_manager_msgs.srv import ListControllers
        except ImportError as exc:
            return False, f"controller_manager_msgs unavailable: {exc}"
        cli = self._node.create_client(ListControllers, "/controller_manager/list_controllers")
        if not cli.wait_for_service(timeout_sec=2.0):
            return False, "controller_manager not available"
        fut = cli.call_async(ListControllers.Request())
        deadline = time.monotonic() + 3.0
        while not fut.done() and time.monotonic() < deadline:
            time.sleep(0.02)
        if not fut.done():
            return False, "list_controllers timed out"
        states = {c.name: c.state for c in fut.result().controller}
        st = states.get(self.controller_name)
        return st == "active", f"{self.controller_name}: {st or 'not loaded'}"


def _safety_name(mode: int) -> str:
    return {1: "NORMAL", 2: "REDUCED", 3: "PROTECTIVE_STOP", 4: "RECOVERY", 5: "SAFEGUARD_STOP",
            6: "SYSTEM_EMERGENCY_STOP", 7: "ROBOT_EMERGENCY_STOP", 8: "VIOLATION", 9: "FAULT",
            10: "VALIDATE_JOINT_ID", 11: "UNDEFINED_SAFETY_MODE", 12: "AUTOMATIC_MODE_SAFEGUARD_STOP",
            13: "SYSTEM_THREE_POSITION_ENABLING_STOP"}.get(mode, f"MODE_{mode}")
