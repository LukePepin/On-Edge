#!/usr/bin/env python3
"""Compare calibrated forward kinematics with live and taught TCP poses. No motion."""
import argparse
import json
import math
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw", type=Path, default=Path("data/hanoi_teaching/2026-09-29.jsonl"))
    args = parser.parse_args()
    if os.environ.get("ROS_LOCALHOST_ONLY") != "1":
        parser.error("Set ROS_LOCALHOST_ONLY=1")
    import numpy as np
    from scipy.spatial.transform import Rotation
    import rclpy
    from rclpy.node import Node
    from moveit_msgs.srv import GetPositionFK
    from hanoi_hardware_state import read_hardware_state
    from hanoi_teach import JOINTS

    hardware = read_hardware_state()
    offset = hardware["active_tcp_offset_m_rotvec_rad"]
    offset_rotation = Rotation.from_rotvec(offset[3:])
    requested = ["peg4_location6_source_approach", "peg3_location1_source_approach"]
    captures = {}
    for line in args.raw.read_text().splitlines():
        item = json.loads(line)
        if item.get("event") == "pose_capture" and item.get("name") in requested:
            captures[item["name"]] = item
    if set(captures) != set(requested):
        parser.error("Missing source or destination capture")
    rclpy.init()
    node = Node("hanoi_check_poses")
    client = node.create_client(GetPositionFK, "/compute_fk")
    results = []
    try:
        if not client.wait_for_service(timeout_sec=20):
            raise RuntimeError("Calibrated planning FK service unavailable")
        targets = [("live", hardware["joint_positions_rad"], hardware["tcp_pose_m_rotvec_rad"][:3],
                    Rotation.from_rotvec(hardware["tcp_pose_m_rotvec_rad"][3:]))]
        for name in requested:
            item = captures[name]
            if item["tcp_frame"] != "base":
                raise RuntimeError("Taught TCP frame is not base")
            ordered = [item["joint_positions_rad"][item["joint_names"].index(j)] for j in JOINTS]
            targets.append((name, ordered, item["tcp_position_m"], Rotation.from_quat(item["tcp_quaternion_xyzw"])))
        for name, joints, expected_position, expected_rotation in targets:
            request = GetPositionFK.Request()
            request.header.frame_id = "base"
            request.fk_link_names = ["tool0"]
            request.robot_state.joint_state.name = JOINTS
            request.robot_state.joint_state.position = joints
            future = client.call_async(request)
            rclpy.spin_until_future_complete(node, future, timeout_sec=5)
            if not future.done() or future.exception():
                raise RuntimeError("FK call did not complete")
            response = future.result()
            if response.error_code.val != 1 or len(response.pose_stamped) != 1:
                raise RuntimeError("FK calculation failed")
            pose = response.pose_stamped[0].pose
            rotation = Rotation.from_quat([pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w])
            tcp_position = np.array([pose.position.x, pose.position.y, pose.position.z]) + rotation.apply(offset[:3])
            position_error = math.dist(tcp_position, expected_position)
            angle_error = ((rotation * offset_rotation).inv() * expected_rotation).magnitude()
            result = dict(name=name, position_error_mm=position_error * 1000,
                          orientation_error_rad=angle_error, passed=position_error <= 0.002 and angle_error <= 0.01)
            results.append(result)
        print(json.dumps(dict(active_tcp_offset=offset, checks=results, no_robot_motion=True)), flush=True)
        if not all(result["passed"] for result in results):
            raise RuntimeError("Calibrated model/tool offset does not match recorded TCP; do not plan motion")
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
