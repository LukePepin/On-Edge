#!/usr/bin/env python3
"""Plan and supervise ONE taught Hanoi transfer. No automatic retries or resumes.

Plan uses calibrated Cartesian paths. Execute pick stops after jaw closure for
operator grasp confirmation. Lift stops at source clearance for manual teaching.
Transfer finishes release/retreat. All arm commands use the passthrough controller.
"""
import argparse
from datetime import datetime, timezone
import json
import math
import os
from pathlib import Path
import socket
import time
import urllib.request

from hanoi_hardware_state import read_hardware_state
from hanoi_teach import JOINTS


def dashboard(command):
    if command not in ("stop", "safetymode", "running"):
        raise ValueError("Unsupported dashboard command")
    with socket.create_connection(("192.168.0.149", 29999), timeout=2) as stream:
        f = stream.makefile("rwb")
        f.readline()
        f.write((command + "\n").encode())
        f.flush()
        return f.readline().decode().strip()


def health():
    with urllib.request.urlopen("http://127.0.0.1:8765/api/status", timeout=2) as response:
        state = json.load(response)
    if state["runner"]["state"] not in ("IDLE", "ABORTED", "COMPLETED"):
        raise RuntimeError("V8 campaign is active")
    if state["link"]["freshness"] != "fresh" or state["link"]["state"]["d12"] != 1:
        raise RuntimeError("Nano unavailable or safeguard output low")
    safety = dashboard("safetymode")
    if safety != "Safetymode: NORMAL":
        raise RuntimeError("Robot safety mode changed: " + safety)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=("plan", "pick", "lift", "transfer"))
    parser.add_argument("--file", type=Path, required=True)
    parser.add_argument("--grasp-confirmed", action="store_true")
    parser.add_argument("--pickup-only", action="store_true", help="Plan pickup and source lift only; no destination motion")
    args = parser.parse_args()
    if os.environ.get("ROS_LOCALHOST_ONLY") != "1":
        parser.error("Set ROS_LOCALHOST_ONLY=1")
    if args.action in ("transfer", "lift") and not args.grasp_confirmed:
        parser.error("Physical grasp confirmation is required before lifting")
    import numpy as np
    from scipy.spatial.transform import Rotation
    import rclpy
    from rclpy.node import Node
    from rclpy.action import ActionClient
    from rclpy.qos import qos_profile_sensor_data
    from geometry_msgs.msg import Pose
    from moveit_msgs.srv import GetCartesianPath
    from control_msgs.action import FollowJointTrajectory
    from trajectory_msgs.msg import JointTrajectoryPoint
    from controller_manager_msgs.srv import SwitchController, ListControllers
    from std_srvs.srv import Trigger
    from ur_msgs.msg import IOStates
    from ur_msgs.srv import SetIO
    from hanoi_kinematics import Kinematics

    rclpy.init()
    node = Node("hanoi_single_transfer")
    io = {}
    goal_handle = None
    executing = args.action != "plan"
    events_path = args.file.with_suffix(".events.jsonl")
    def event(event_name, **fields):
        record = dict(utc=datetime.now(timezone.utc).isoformat(), event=event_name, **fields)
        with events_path.open("a", encoding="utf-8") as stream:
            stream.write(json.dumps(record, allow_nan=False) + "\n")
            stream.flush(); os.fsync(stream.fileno())
        print(json.dumps(record, allow_nan=False), flush=True)

    def io_cb(msg):
        io.update(time=time.monotonic(), outputs={p.pin: bool(p.state) for p in msg.digital_out_states})
    node.create_subscription(IOStates, "/io_and_status_controller/io_states", io_cb, qos_profile_sensor_data)

    def wait(future, timeout=8, monitor=False):
        end = time.monotonic() + timeout
        last_check = 0
        while not future.done() and time.monotonic() < end:
            rclpy.spin_once(node, timeout_sec=0.03)
            if monitor and time.monotonic() - last_check > 0.5:
                health()
                hardware = read_hardware_state(timeout=2)
                if hardware["emergency_stopped"] or hardware["protective_stopped"] or not hardware["program_running"]:
                    raise RuntimeError("Robot interrupted; cancel rather than resume")
                last_check = time.monotonic()
        if not future.done() or future.exception():
            raise RuntimeError("ROS request timeout/failure; no automatic retry")
        return future.result()

    def service(kind, name, request, timeout=8):
        client = node.create_client(kind, name)
        try:
            if not client.wait_for_service(timeout_sec=5):
                raise RuntimeError("Service unavailable: " + name)
            return wait(client.call_async(request), timeout)
        finally:
            node.destroy_client(client)

    def stationary(expected=None):
        health()
        hardware = read_hardware_state()
        if max(abs(v) for v in hardware["joint_velocities_rad_s"]) > 0.01:
            raise RuntimeError("Arm is not stationary")
        if expected and max(abs(a-b) for a,b in zip(expected, hardware["joint_positions_rad"])) > 0.01:
            raise RuntimeError("Arm differs from planned start; replan, do not replay")
        return hardware

    def gripper(command):
        stationary()
        event('gripper_requested', command=command)
        target = 16 if command == "open" else 17
        for pin, value in ((16, 0.), (17, 0.), (target, 1.)):
            request = SetIO.Request(); request.fun, request.pin, request.state = 1, pin, value
            response = service(SetIO, "/io_and_status_controller/set_io", request)
            if not response.success:
                raise RuntimeError("Gripper command failed; physical state uncertain")
            sent = time.monotonic(); deadline = sent + 3
            while time.monotonic() < deadline:
                rclpy.spin_once(node, timeout_sec=0.03)
                if io.get("time", 0) > sent and io["outputs"].get(pin) == bool(value):
                    break
            else:
                raise RuntimeError("Gripper output not acknowledged")
            time.sleep(0.05)
        time.sleep(0.5)
        event("gripper_output_acknowledged", command=command, physical_result="operator_confirmation_required")

    try:
        hardware = stationary()
        if args.action == "plan":
            if args.file.exists():
                raise RuntimeError("Existing plan preserved; choose new filename")
            import xacro
            from ament_index_python.packages import get_package_share_directory
            root = Path(__file__).resolve().parents[2]
            xml = xacro.process_file(str(Path(get_package_share_directory("ur_description")) / "urdf/ur.urdf.xacro"), mappings={
                "name": "ur", "ur_type": "ur5", "kinematics_params": str(root / "audit/calibration/ur5_factory_2026-09-30.yaml"),
                "safety_limits": "true", "tf_prefix": ""}).toxml()
            offset = hardware["active_tcp_offset_m_rotvec_rad"]
            model = Kinematics(xml, offset)
            current = model.tcp(JOINTS, hardware["joint_positions_rad"])
            if math.dist(current[:3,3], hardware["tcp_pose_m_rotvec_rad"][:3]) > 0.002:
                raise RuntimeError("Local calibrated FK disagrees with live robot")
            captures = {}
            for line in (root / "data/hanoi_teaching/2026-09-29.jsonl").read_text().splitlines():
                item = json.loads(line)
                if item.get("event") == "pose_capture": captures[item["name"]] = item
            def pose_for(name):
                item = captures[name]
                if item["tcp_frame"] != "base": raise RuntimeError("Expected base frame")
                transform = np.eye(4)
                transform[:3,:3] = Rotation.from_quat(item["tcp_quaternion_xyzw"]).as_matrix()
                transform[:3,3] = item["tcp_position_m"]
                measured = model.tcp(item['joint_names'],item['joint_positions_rad'])
                if math.dist(measured[:3,3],transform[:3,3])>0.002:
                    raise RuntimeError('Recorded joint/TCP mismatch: '+name)
                return transform
            source = pose_for("peg4_location6_source_approach")
            destination_name = 'peg1_location1_place' if 'peg1_location1_place' in captures else 'peg1_location1_source_approach'
            if not args.pickup_only and destination_name!='peg1_location1_place':
                raise RuntimeError('Prior destination descent missed the post; teach peg1_location1_place before another full transfer')
            destination = pose_for(destination_name)
            entry_name = next((name for name in ('peg4_location6_pickup_entry', 'peg8_location6_pickup_entry',
                                                 'peg8_location6_side_approach', 'peg8_location6_source_approach') if name in captures), None)
            if entry_name is None:
                raise RuntimeError('Teach the side approach for peg 4 level 6 before planning')
            entry_raw = pose_for(entry_name)
            entry = source.copy()
            entry[:2,3] = entry_raw[:2,3]
            if math.dist(entry[:2,3],source[:2,3])<0.02:
                raise RuntimeError('Pickup entry is too close to the grasp to establish a clear side approach')
            # Derived entry retains grasp height and orientation. Recompute IK;
            # never combine adjusted TCP with old recorded joint positions.
            entry_high = entry.copy()
            withdrawal_name = next((name for name in ('peg1_location1_place_withdrawal', 'peg5_location1_side_approach',
                                                       'peg5_location1_pickup_entry', 'peg5_location1_source_approach') if name in captures), None)
            if withdrawal_name is None:
                raise RuntimeError('Teach the side withdrawal for peg 1 level 1 before planning')
            withdrawal_raw = pose_for(withdrawal_name)
            withdrawal = destination.copy()
            withdrawal[:2,3] = withdrawal_raw[:2,3]
            if math.dist(withdrawal[:2,3],destination[:2,3])<0.02:
                raise RuntimeError('Withdrawal point too close to placement to establish a clear retreat')
            withdrawal_high = withdrawal.copy()
            height = max(captures["peg4_location6_clearance"]["tcp_position_m"][2], captures["peg1_location7_source_approach"]["tcp_position_m"][2], current[2,3])
            source_high, destination_high, current_high = source.copy(), destination.copy(), current.copy()
            source_high[2,3] = destination_high[2,3] = current_high[2,3] = height
            entry_high[2,3] = height
            withdrawal_high[2,3] = height
            route = [("rise_current", current_high, "pick", "vertical"),
                     ("travel_pickup_entry_high", entry_high, "pick", "high"),
                     ("descend_pickup_entry", entry, "pick", "vertical"),
                     ("insert_source", source, "pick", "horizontal"),
                     ("lift_source", source_high, "transfer", "vertical"),
                     ("travel_destination_high", destination_high, "transfer", "high"),
                     ("descend_destination", destination, "transfer", "vertical"),
                     ("withdraw_destination", withdrawal, "retreat", "horizontal"),
                     ("rise_withdrawal", withdrawal_high, "retreat", "vertical")]
            if args.pickup_only:
                route = [segment for segment in route if segment[2]=='pick' or segment[0]=='lift_source']
            seed = list(hardware["joint_positions_rad"])
            segments = []
            for name, target, phase, constraint in route:
                start_tcp = model.tcp(JOINTS, seed)
                if np.linalg.norm(target-start_tcp) < 0.0001:
                    continue
                flange = target @ np.linalg.inv(model.offset)
                q = Rotation.from_matrix(flange[:3,:3]).as_quat()
                pose = Pose(); pose.position.x, pose.position.y, pose.position.z = map(float, flange[:3,3])
                pose.orientation.x, pose.orientation.y, pose.orientation.z, pose.orientation.w = map(float, q)
                request = GetCartesianPath.Request()
                request.header.frame_id, request.group_name, request.link_name = "base", "ur_manipulator", "tool0"
                request.start_state.joint_state.name, request.start_state.joint_state.position = JOINTS, seed
                request.max_step, request.jump_threshold, request.avoid_collisions = 0.001, 0., True
                request.waypoints = [pose]
                response = service(GetCartesianPath, "/compute_cartesian_path", request, timeout=45)
                traj = response.solution.joint_trajectory
                if response.error_code.val != 1 or response.fraction < 0.999999 or len(traj.points)<2:
                    raise RuntimeError(f"Incomplete {name}: {response.fraction}, code {response.error_code.val}")
                if set(traj.joint_names)!=set(JOINTS): raise RuntimeError("Unexpected joint names")
                indices=[traj.joint_names.index(j) for j in JOINTS]
                points=[]; previous=seed; worst_xy=0.; worst_z=0.; lowest=float('inf')
                for pt in traj.points:
                    positions=[pt.positions[i] for i in indices]
                    if not all(math.isfinite(v) for v in positions): raise RuntimeError("Nonfinite trajectory")
                    if max(abs(a-b) for a,b in zip(previous,positions))>0.05: raise RuntimeError("Joint step too large: "+name)
                    tcp=model.tcp(JOINTS,positions); lowest=min(lowest,float(tcp[2,3]))
                    if constraint=="vertical":
                        worst_xy=max(worst_xy,math.dist(tcp[:2,3],target[:2,3]))
                        orientation_error=(Rotation.from_matrix(tcp[:3,:3]).inv()*Rotation.from_matrix(target[:3,:3])).magnitude()
                        if orientation_error>0.002: raise RuntimeError("Vertical orientation changed: "+name)
                    if constraint=='horizontal':
                        worst_z=max(worst_z,abs(float(tcp[2,3]-target[2,3])))
                        orientation_error=(Rotation.from_matrix(tcp[:3,:3]).inv()*Rotation.from_matrix(target[:3,:3])).magnitude()
                        if orientation_error>0.002: raise RuntimeError('Horizontal insertion orientation changed')
                    seconds=pt.time_from_start.sec+pt.time_from_start.nanosec/1e9
                    points.append(dict(positions=positions, velocities=[pt.velocities[i] for i in indices] if pt.velocities else [],
                                       accelerations=[pt.accelerations[i] for i in indices] if pt.accelerations else [],time_s=seconds*2))
                    previous=positions
                if worst_xy>0.002: raise RuntimeError(f"Vertical path drift {worst_xy} m: {name}")
                if worst_z>0.002: raise RuntimeError(f'Horizontal path height drift {worst_z} m: {name}')
                if constraint=="high" and lowest<height-0.002: raise RuntimeError("Travel dipped below clearance: "+name)
                if math.dist(model.tcp(JOINTS,previous)[:3,3],target[:3,3])>0.002: raise RuntimeError("Endpoint mismatch")
                if any(b['time_s']<=a['time_s'] for a,b in zip(points,points[1:])): raise RuntimeError("Nonincreasing trajectory time")
                if max(abs(v) for p in points for v in p['velocities'])>0.065: raise RuntimeError("Planner exceeded conservative velocity limit")
                segment=dict(name=name,phase=phase,start_joint_positions_rad=seed,points=points,
                             target_tcp_position_m=target[:3,3].tolist(), vertical_xy_error_mm=worst_xy*1000,
                             horizontal_z_error_mm=worst_z*1000,minimum_tcp_z_m=lowest)
                segments.append(segment);seed=previous
                event("segment_planned",name=name,duration_s=points[-1]['time_s'],points=len(points),vertical_xy_error_mm=worst_xy*1000)
            plan=dict(schema=1,mode='pickup_only' if args.pickup_only else 'transfer',
                      source=[4,6],destination=None if args.pickup_only else [1,1],initial_joints=hardware['joint_positions_rad'],
                      destination_capture=None if args.pickup_only else destination_name,
                      active_tcp_offset=offset,clearance_z_m=height,segments=segments,
                      pickup_entry_capture=entry_name,
                      approach_label_mapping={str(peg+4): f'side approach/withdrawal for physical peg {peg}' for peg in range(1,5)},
                      derived_pickup_entry_tcp_m=entry[:3,3].tolist(),
                      place_withdrawal_capture=withdrawal_name,
                      derived_withdrawal_tcp_m=withdrawal[:3,3].tolist(),
                      fixture_collision_model_present=False,physical_result="not_executed")
            with args.file.open('x',encoding='utf-8') as stream: stream.write(json.dumps(plan,indent=2,allow_nan=False)+'\n')
            event("plan_complete",file=str(args.file),segments=len(segments),no_robot_motion=True)
            return

        plan=json.loads(args.file.read_text())
        if plan['source']!=[4,6] or plan['destination'] not in ([1,1],None): raise RuntimeError("Unexpected job")
        if args.action=='transfer' and (plan.get('mode')=='pickup_only' or plan.get('destination_capture')!='peg1_location1_place'):
            raise RuntimeError('Destination is unvalidated; pickup-only or old placement plan cannot transfer')
        if plan.get('pickup_entry_capture') not in ('peg4_location6_pickup_entry','peg8_location6_pickup_entry','peg8_location6_side_approach','peg8_location6_source_approach') or not any(s['name']=='insert_source' for s in plan['segments']):
            raise RuntimeError('Superseded top-down pickup plan rejected; teach entry and create a corrected plan')
        if args.action=='transfer' and (plan.get('place_withdrawal_capture') not in ('peg1_location1_place_withdrawal','peg5_location1_side_approach','peg5_location1_pickup_entry','peg5_location1_source_approach') or not any(s['name']=='withdraw_destination' for s in plan['segments'])):
            raise RuntimeError('Teach horizontal destination withdrawal and create a corrected plan')
        records=[json.loads(line) for line in events_path.read_text().splitlines()]
        if args.action=='pick' and any(r['event'] in ('segment_started','gripper_requested','gripper_output_acknowledged','pick_outputs_complete') for r in records):
            raise RuntimeError("Pick already attempted; inspect physical state, do not replay")
        if args.action in ('transfer','lift') and (not any(r['event']=='pick_outputs_complete' for r in records)
                                     or any(r['event'] in ('transfer_started','lift_started') for r in records)):
            raise RuntimeError("Lifting requires one completed pick and must not be replayed")
        selected=[s for s in plan['segments'] if (s['name']=='lift_source' if args.action=='lift' else
                  s['phase']==args.action or (args.action=='transfer' and s['phase']=='retreat'))]
        stationary(selected[0]['start_joint_positions_rad'])
        if max(abs(a-b) for a,b in zip(hardware['active_tcp_offset_m_rotvec_rad'],plan['active_tcp_offset']))>1e-5:
            raise RuntimeError("Tool offset changed; replan")
        event('execution_started' if args.action=='pick' else 'lift_started' if args.action=='lift' else 'transfer_started',phase=args.action)
        if not hardware['program_running']:
            response=service(Trigger,'/io_and_status_controller/resend_robot_program',Trigger.Request())
            if not response.success: raise RuntimeError("Cannot start ROS control program: "+response.message)
            end=time.monotonic()+5
            while time.monotonic()<end:
                if read_hardware_state()['program_running']: break
                rclpy.spin_once(node,timeout_sec=.1)
            else: raise RuntimeError("ROS control program did not start")
        controller='passthrough_trajectory_controller'
        def controller_states():
            return {c.name:c.state for c in service(ListControllers,'/controller_manager/list_controllers',ListControllers.Request()).controller}
        states=controller_states()
        competing=('scaled_joint_trajectory_controller','joint_trajectory_controller','forward_position_controller',
                   'forward_velocity_controller','forward_effort_controller','freedrive_mode_controller','force_mode_controller')
        if any(states.get(c)=='active' for c in competing): raise RuntimeError('Another arm controller is active')
        if states.get(controller)!='active':
            switch=SwitchController.Request();switch.activate_controllers=[controller]
            switch.strictness=SwitchController.Request.STRICT;switch.activate_asap=True;switch.timeout.sec=5
            response=service(SwitchController,'/controller_manager/switch_controller',switch)
            # controller_stopper may restore it automatically on program startup.
            # A failed duplicate activation is acceptable only after readback
            # establishes that the requested controller is already active.
            if not response.ok and controller_states().get(controller)!='active':
                raise RuntimeError('Controller activation failed')
        event('controller_ready',controller=controller)
        action=ActionClient(node,FollowJointTrajectory,'/passthrough_trajectory_controller/follow_joint_trajectory')
        if not action.wait_for_server(timeout_sec=5): raise RuntimeError("Trajectory action unavailable")
        if args.action=='pick': gripper('open')
        for segment in selected:
            stationary(segment['start_joint_positions_rad'])
            goal=FollowJointTrajectory.Goal();goal.trajectory.joint_names=JOINTS
            for point in segment['points']:
                if point['time_s']<=0: continue  # omit p0; controller uses live start
                pt=JointTrajectoryPoint();pt.positions=point['positions']
                pt.velocities=[v/2 for v in point['velocities']]
                pt.accelerations=[v/4 for v in point['accelerations']]
                pt.time_from_start.sec=int(point['time_s']);pt.time_from_start.nanosec=int((point['time_s']%1)*1e9)
                goal.trajectory.points.append(pt)
            event('segment_started',name=segment['name'],duration_s=segment['points'][-1]['time_s'])
            goal_handle=wait(action.send_goal_async(goal),timeout=5)
            if not goal_handle.accepted: raise RuntimeError("Trajectory goal rejected")
            response=wait(goal_handle.get_result_async(),timeout=segment['points'][-1]['time_s']*3+15,monitor=True)
            goal_handle=None
            if response.status!=4 or response.result.error_code!=0: raise RuntimeError("Trajectory aborted: "+response.result.error_string)
            endpoint=stationary(segment['points'][-1]['positions'])
            if math.dist(endpoint['tcp_pose_m_rotvec_rad'][:3],segment['target_tcp_position_m'])>0.002:
                raise RuntimeError('Actual TCP missed planned endpoint; inspect before gripper command')
            event('segment_completed',name=segment['name'],actual_joint_positions_rad=endpoint['joint_positions_rad'],
                  actual_tcp_pose_m_rotvec_rad=endpoint['tcp_pose_m_rotvec_rad'])
            if segment['name']=='insert_source': gripper('close')
            if segment['name']=='descend_destination': gripper('open')
        event('pick_outputs_complete' if args.action=='pick' else 'source_lift_complete' if args.action=='lift' else 'transfer_motion_complete',physical_result='operator_confirmation_required')
    except BaseException as exc:
        event('test_error',phase=args.action,error=str(exc))
        if goal_handle is not None:
            try: wait(goal_handle.cancel_goal_async(),timeout=2)
            except Exception: pass
        raise
    finally:
        if executing:
            try: event('robot_program_stopped',response=dashboard('stop'))
            except Exception as exc: print('STOP status unknown: '+str(exc),flush=True)
        node.destroy_node();rclpy.shutdown()


if __name__=='__main__': main()
