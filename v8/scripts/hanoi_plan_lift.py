#!/usr/bin/env python3
"""Plan a strictly vertical lift using a taught clearance height. NEVER executes."""
import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--grasp", default="peg4_location6_source_approach")
    parser.add_argument("--clearance", default="peg4_location6_clearance")
    parser.add_argument("--raw", type=Path, default=Path("data/hanoi_teaching/2026-09-29.jsonl"))
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--step", type=float, default=0.002, help="Cartesian sampling step in metres")
    args = parser.parse_args()
    if not 0.0005 <= args.step <= 0.005:
        parser.error("--step must be between 0.0005 and 0.005 metres")
    if os.environ.get("ROS_LOCALHOST_ONLY") != "1":
        parser.error("Set ROS_LOCALHOST_ONLY=1")
    if args.output.exists():
        parser.error("Existing output preserved; select a new filename")
    import numpy as np
    from scipy.spatial.transform import Rotation
    import rclpy
    from rclpy.node import Node
    from geometry_msgs.msg import Pose
    from moveit_msgs.srv import GetCartesianPath
    from hanoi_hardware_state import read_hardware_state
    from hanoi_teach import JOINTS

    captures = {}
    for line in args.raw.read_text().splitlines():
        item = json.loads(line)
        if item.get("event") == "pose_capture":
            captures[item["name"]] = item
    grasp, clearance = captures[args.grasp], captures[args.clearance]
    if grasp["tcp_frame"] != "base" or clearance["tcp_frame"] != "base":
        raise RuntimeError("Expected taught poses in base frame")
    target = list(grasp["tcp_position_m"])
    target[2] = clearance["tcp_position_m"][2]
    if target[2] <= grasp["tcp_position_m"][2]:
        raise RuntimeError("Clearance is not above the grasp")
    hardware = read_hardware_state()
    offset = hardware["active_tcp_offset_m_rotvec_rad"]
    tcp_rotation = Rotation.from_quat(grasp["tcp_quaternion_xyzw"])
    flange_rotation = tcp_rotation * Rotation.from_rotvec(offset[3:]).inv()
    flange_position = np.array(target) - flange_rotation.apply(offset[:3])
    quaternion = flange_rotation.as_quat()
    rclpy.init()
    node = Node("hanoi_plan_lift")
    try:
        client = node.create_client(GetCartesianPath, "/compute_cartesian_path")
        if not client.wait_for_service(timeout_sec=5):
            raise RuntimeError("Planning service unavailable")
        request = GetCartesianPath.Request()
        request.header.frame_id = "base"
        request.group_name = "ur_manipulator"
        request.link_name = "tool0"
        request.start_state.joint_state.name = JOINTS
        request.start_state.joint_state.position = [grasp["joint_positions_rad"][grasp["joint_names"].index(j)] for j in JOINTS]
        request.max_step = args.step
        request.jump_threshold = 0.0  # explicit per-point joint jump check below
        request.avoid_collisions = True
        pose = Pose()
        pose.position.x, pose.position.y, pose.position.z = map(float, flange_position)
        pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w = map(float, quaternion)
        request.waypoints = [pose]
        future = client.call_async(request)
        rclpy.spin_until_future_complete(node, future, timeout_sec=45)
        if not future.done() or future.exception():
            raise RuntimeError("Planning call failed or timed out")
        response = future.result()
        trajectory = response.solution.joint_trajectory
        if response.error_code.val != 1 or response.fraction < 0.999999 or len(trajectory.points) < 2:
            raise RuntimeError(f"Incomplete lift path: fraction={response.fraction}, code={response.error_code.val}")
        if set(trajectory.joint_names) != set(JOINTS):
            raise RuntimeError("Unexpected planned joints")
        points = [[point.positions[trajectory.joint_names.index(j)] for j in JOINTS] for point in trajectory.points]
        all_points = [list(request.start_state.joint_state.position)] + points
        largest_jump = max(abs(b - a) for before, after in zip(all_points, all_points[1:]) for a, b in zip(before, after))
        if largest_jump > 0.05:
            worst = max(((abs(b-a), i, j) for i, (before, after) in enumerate(zip(all_points, all_points[1:]))
                         for j, (a, b) in enumerate(zip(before, after))), key=lambda item: item[0])
            print(json.dumps(dict(rejected=True, points=len(points), worst_step=worst,
                                  before=all_points[worst[1]], after=all_points[worst[1]+1],
                                  trajectory_times_s=[p.time_from_start.sec+p.time_from_start.nanosec/1e9 for p in trajectory.points])))
            raise RuntimeError(f"Excessive joint step {largest_jump} rad")
        result = {
            "mode": "candidate_only_no_robot_motion", "grasp_capture": args.grasp,
            "clearance_height_capture": args.clearance,
            "raw_grasp_utc": grasp["utc"], "raw_clearance_utc": clearance["utc"],
            "derived_tcp_position_m": target,
            "derived_tcp_quaternion_xyzw": grasp["tcp_quaternion_xyzw"],
            "derivation": "Retain raw grasp XY and orientation; use raw clearance Z; compute new Cartesian path and joint positions.",
            "active_tcp_offset_m_rotvec_rad": offset, "fraction": response.fraction,
            "joint_names": JOINTS, "joint_positions_rad": points,
            "largest_joint_step_rad": largest_jump,
            "fixture_and_held_disk_collision_model_present": False,
            "physical_path_validated": False,
            "timing_validated_for_execution": False,
        }
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(json.dumps(result, indent=2, allow_nan=False) + "\n")
        print(json.dumps(dict(output=str(args.output), fraction=response.fraction, points=len(points),
                              largest_joint_step_rad=largest_jump, no_robot_motion=True)))
    finally:
        node.destroy_node()
        rclpy.shutdown()


if __name__ == "__main__":
    main()
