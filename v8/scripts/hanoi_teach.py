#!/usr/bin/env python3
"""Stationary gripper checks and named pose capture. NEVER commands arm motion.

Run on the Pi with ROS Humble sourced and ROS_LOCALHOST_ONLY=1.
Records are appended; old captures are never silently replaced. TCP values are
the driver's reported active TCP, not an independently calibrated jaw position.
"""
import argparse
from collections import deque
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import time
import urllib.request

JOINTS = ["shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
          "wrist_1_joint", "wrist_2_joint", "wrist_3_joint"]


def ordered_joints(msg):
    indices = [list(msg.name).index(n) for n in JOINTS]
    q = [float(msg.position[i]) for i in indices]
    v = [float(msg.velocity[i]) for i in indices]
    if not all(math.isfinite(x) for x in q + v):
        raise ValueError("nonfinite joint telemetry")
    return q, v


def stationary(history, now):
    recent = [(t, q, v) for t, q, v in history if now - t <= 0.8]
    if len(recent) < 5 or now - recent[-1][0] > 0.2:
        return False
    if recent[-1][0] - recent[0][0] < 0.5:
        return False
    if any(b[0] - a[0] > 0.2 for a, b in zip(recent, recent[1:])):
        return False
    if any(abs(x) > 0.01 for _, _, v in recent for x in v):
        return False
    return all(max(q[i] for _, q, _ in recent) - min(q[i] for _, q, _ in recent) < 0.005
               for i in range(6))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["status", "open", "close", "capture"])
    parser.add_argument("--name", default="")
    parser.add_argument("--note", default="")
    parser.add_argument("--output", default="data/hanoi_teaching/2026-09-29.jsonl")
    parser.add_argument("--robot-host", default="192.168.0.149")
    args = parser.parse_args()
    if args.action == "capture" and not args.name:
        parser.error("capture requires --name")
    if os.environ.get("ROS_LOCALHOST_ONLY") != "1":
        parser.error("Set ROS_LOCALHOST_ONLY=1 to isolate this Pi from other lab robots")

    import rclpy
    from rclpy.node import Node
    from rclpy.qos import qos_profile_sensor_data
    from sensor_msgs.msg import JointState
    from geometry_msgs.msg import PoseStamped
    from ur_msgs.msg import IOStates
    from ur_msgs.srv import SetIO

    rclpy.init()
    node = Node("hanoi_teach_helper")
    history = deque(maxlen=300)
    latest = {}

    def joint_cb(msg):
        try:
            q, v = ordered_joints(msg)
            history.append((time.monotonic(), q, v))
        except (ValueError, IndexError):
            history.clear()

    def remember(key, msg):
        latest[key] = (time.monotonic(), msg)

    node.create_subscription(JointState, "/joint_states", joint_cb, qos_profile_sensor_data)
    node.create_subscription(PoseStamped, "/tcp_pose_broadcaster/pose",
                             lambda m: remember("tcp", m), qos_profile_sensor_data)
    node.create_subscription(IOStates, "/io_and_status_controller/io_states",
                             lambda m: remember("io", m), qos_profile_sensor_data)

    def spin_until(predicate, seconds=8):
        deadline = time.monotonic() + seconds
        while time.monotonic() < deadline:
            rclpy.spin_once(node, timeout_sec=0.03)
            if predicate():
                return
        raise RuntimeError("Timed out waiting for fresh telemetry / stationary arm / output acknowledgement")

    def fresh(key):
        return key in latest and time.monotonic() - latest[key][0] < 0.2

    def outputs():
        return {x.pin: bool(x.state) for x in latest["io"][1].digital_out_states}

    def record(event):
        event.update(utc=datetime.now(timezone.utc).isoformat(), name=args.name,
                     note=args.note, schema=1, source="live_ros_hardware")
        path = Path(args.output)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(event, allow_nan=False) + "\n")
            stream.flush()
            os.fsync(stream.fileno())
        print(json.dumps(event, allow_nan=False), flush=True)

    try:
        spin_until(lambda: fresh("tcp") and fresh("io") and stationary(history, time.monotonic()))
        # ROS can continue publishing cached values after the driver's hardware
        # reader fails. Require an advancing direct controller clock and agreement.
        from hanoi_hardware_state import read_hardware_state
        hardware = read_hardware_state(args.robot_host)
        spin_until(lambda: fresh("tcp") and fresh("io") and stationary(history, time.monotonic()))
        if any(abs(value) > 0.01 for value in hardware["joint_velocities_rad_s"]):
            raise RuntimeError("Direct robot feedback reports arm motion")
        if max(abs(a - b) for a, b in zip(history[-1][1], hardware["joint_positions_rad"])) > 0.005:
            raise RuntimeError("ROS joints disagree with direct robot feedback; reject cached or inconsistent telemetry")
        tcp_position = latest["tcp"][1].pose.position
        if math.dist([tcp_position.x, tcp_position.y, tcp_position.z], hardware["tcp_pose_m_rotvec_rad"][:3]) > 0.002:
            raise RuntimeError("ROS TCP disagrees with direct robot feedback")
        if args.action in ("open", "close"):
            # The previous experiment must be finished, not merely paused.
            with urllib.request.urlopen("http://127.0.0.1:8765/api/status", timeout=3) as response:
                state = json.load(response)
            if state["runner"]["state"] not in ("IDLE", "COMPLETED", "ABORTED"):
                raise RuntimeError("Finish/abort the V8 campaign before gripper teaching")
            if state["robot"].get("program_running") is not False:
                raise RuntimeError("Stop the External Control program on the pendant before stationary gripper teaching")
            client = node.create_client(SetIO, "/io_and_status_controller/set_io")
            if not client.wait_for_service(timeout_sec=3):
                raise RuntimeError("Gripper IO service unavailable")
            target = 16 if args.action == "open" else 17
            record({"event": "gripper_requested", "command": args.action,
                    "outputs_before": outputs(), "physical_result": "unconfirmed"})
            for pin, value in ((16, 0.0), (17, 0.0), (target, 1.0)):
                spin_until(lambda: stationary(history, time.monotonic()), seconds=2)
                req = SetIO.Request()
                req.fun, req.pin, req.state = 1, pin, value
                future = client.call_async(req)
                rclpy.spin_until_future_complete(node, future, timeout_sec=2)
                if not future.done() or future.exception() or not future.result().success:
                    raise RuntimeError(f"SetIO failed/unknown for output {pin}; inspect physical state, do not retry blindly")
                sent = time.monotonic()
                spin_until(lambda: fresh("io") and latest["io"][0] > sent
                           and outputs().get(pin) == bool(value), seconds=2)
                time.sleep(0.05)
            record({"event": "gripper_output_acknowledged", "command": args.action,
                    "outputs_after": outputs(), "physical_result": "operator_confirmation_required"})
        else:
            tcp = latest["tcp"][1]
            p, q = tcp.pose.position, tcp.pose.orientation
            values = [p.x, p.y, p.z, q.x, q.y, q.z, q.w]
            if not all(math.isfinite(x) for x in values) or not tcp.header.frame_id:
                raise RuntimeError("Invalid TCP pose")
            event = {"event": "pose_capture" if args.action == "capture" else "stationary_status",
                     "joint_names": JOINTS, "joint_positions_rad": history[-1][1],
                     "joint_velocities_rad_s": history[-1][2],
                     "tcp_frame": tcp.header.frame_id,
                     "tcp_position_m": values[:3], "tcp_quaternion_xyzw": values[3:],
                     "tcp_source": "/tcp_pose_broadcaster/pose",
                     "tcp_stamp": {"sec": tcp.header.stamp.sec, "nanosec": tcp.header.stamp.nanosec},
                     "tool_outputs": {p: outputs().get(p) for p in (16, 17)},
                     "tool_offset_and_fixture_calibration": "operator_to_document",
                     "hardware_state_check": hardware,
                     "replay_validated": False}
            record(event)
    except Exception as exc:
        record({"event": "helper_error", "action": args.action, "error": str(exc)})
        raise SystemExit(str(exc))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
