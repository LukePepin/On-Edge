#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from controller_manager_msgs.srv import SwitchController
from std_srvs.srv import Trigger
from sensor_msgs.msg import JointState
import math
import time

class MockPickAndPlaceClient(Node):
    def __init__(self):
        super().__init__('mock_pick_and_place')
        self.get_logger().info('Initializing Mock Pick-and-Place State Machine...')

        self.current_joint_state = None
        self.joint_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )

        self.joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
        ]

        # Waypoints in degrees provided by the user
        self.poses_deg = {
            'Pick': [39.71, -98.55, -97.62, -64.90, -264.58, -280.20],
            'Transfer': [7.19, -80.56, -76.40, -64.90, -264.58, -280.20],
            'Place': [-18.46, -107.23, -101.08, -56.55, -269.20, -204.20]
        }
        
        # Convert to radians
        self.poses_rad = {k: [math.radians(deg) for deg in v] for k, v in self.poses_deg.items()}
        
        # Action Client for the Trajectory Controller
        self._action_client = ActionClient(self, FollowJointTrajectory, '/scaled_joint_trajectory_controller/follow_joint_trajectory')
        
        # Async Attack Service Client for the Strike Zone
        self.attack_client = self.create_client(Trigger, '/inject_attack')
        
        self.timer = self.create_timer(1.0, self.run_phase1)
        self.current_state = 0
        self.attack_fired = False
        self.is_standstill = False

    def joint_state_callback(self, msg):
        if self.current_joint_state is not None:
            diff = sum(abs(curr - prev) for curr, prev in zip(msg.position, self.current_joint_state.position))
            self.is_standstill = (diff < 1e-4)
        self.current_joint_state = msg

    def normalize_target(self, current_rad, target_rad):
        # Shortest-path angular normalization to prevent 360-degree quintic unwinds
        diff = (target_rad - current_rad + math.pi) % (2 * math.pi) - math.pi
        return current_rad + diff

    def build_point(self, pose_name, time_sec):
        point = JointTrajectoryPoint()
        point.positions = self.poses_rad[pose_name]
        # Purposefully not declaring velocities/accelerations to force the controller 
        # to calculate natural cubic splines, avoiding quintic whip-crack aborts.
        point.time_from_start.sec = int(time_sec)
        point.time_from_start.nanosec = int((time_sec - int(time_sec)) * 1e9)
        return point

    def trigger_strike_zone(self, delay_sec):
        """Asynchronous delay thread to trigger the attack exactly at 50% kinematic progress"""
        self.get_logger().info(f"💣 Strike Zone Hook Armed: Detonating in {delay_sec} seconds...")
        time.sleep(delay_sec)
        if not self.attack_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().error("Inject Attack service not available!")
            return
        
        self.get_logger().warn("🚀 TRIGGERING 50% TRANSFER LEG STRIKE!")
        req = Trigger.Request()
        self.attack_client.call_async(req)
        self.attack_fired = True

    def run_phase1(self):
        if self.current_joint_state is None:
            self.get_logger().info('Waiting for /joint_states for Phase 1 p0 injection...')
            return
            
        self.timer.cancel() # Stop timer, we will drive execution via action futures
        
        while not self._action_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info('Waiting for trajectory action server...')
            
        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = self.joint_names
        
        # We still need p0_positions for the normalization math
        p0_positions = []
        for name in self.joint_names:
            idx = self.current_joint_state.name.index(name)
            p0_positions.append(self.current_joint_state.position[idx])
            
        # 0. Dynamic p0 (Current Physical State)
        p0 = JointTrajectoryPoint()
        p0.positions = p0_positions
        p0.velocities = [0.0] * 6
        p0.accelerations = [0.0] * 6
        p0.time_from_start.sec = 0
        p0.time_from_start.nanosec = 0
        
        # 1. Approach Pick (5.0s total)
        p1 = JointTrajectoryPoint()
        norm_pos = []
        for i in range(6):
            norm_pos.append(self.normalize_target(p0_positions[i], self.poses_rad['Pick'][i]))
        p1.positions = norm_pos
        p1.velocities = [0.0] * 6
        p1.accelerations = [0.0] * 6
        p1.time_from_start.sec = 5
        p1.time_from_start.nanosec = 0
        
        goal_msg.trajectory.points = [p0, p1]
        
        self.get_logger().info('--- DEEP KINEMATIC TELEMETRY: PHASE 1 ---')
        self.get_logger().info(f'p0 (Current) : {[round(x, 4) for x in p0.positions]}')
        self.get_logger().info(f'p1 (Pick)    : {[round(x, 4) for x in p1.positions]}')
        self.get_logger().info('-----------------------------------------')
        
        self.get_logger().info('Phase 1: Safe Initialization to Pick boundary (5.0s)...')
        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.phase1_response_callback)

    def phase1_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Phase 1 Trajectory rejected by controller!')
            raise SystemExit

        self.get_logger().info('Phase 1 accepted. Moving to perfect start boundary...')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.phase1_result_callback)

    def phase1_result_callback(self, future):
        result = future.result().result
        self.get_logger().info('Phase 1 complete! Entering 0.5s mechanical settling window...')
        self.settle_timer = self.create_timer(0.5, self.settling_callback)
        
    def settling_callback(self):
        if self.is_standstill:
            self.settle_timer.cancel()
            self.get_logger().info('Standstill confirmed! Proceeding to Phase 2.')
            self.run_phase2()
        else:
            self.get_logger().info('Waiting for absolute mechanical standstill...')

    def run_phase2(self):
        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = self.joint_names
        
        p0_positions = []
        for name in self.joint_names:
            idx = self.current_joint_state.name.index(name)
            p0_positions.append(self.current_joint_state.position[idx])
            
        # 0. Dynamic p0 (Current Physical State)
        p0 = JointTrajectoryPoint()
        p0.positions = p0_positions
        p0.velocities = [0.0] * 6
        p0.accelerations = [0.0] * 6
        p0.time_from_start.sec = 0
        p0.time_from_start.nanosec = 0
        
        normalized_poses = {}
        for pose_name in ['Place']:
            norm_pos = []
            for i in range(6):
                norm_pos.append(self.normalize_target(p0_positions[i], self.poses_rad[pose_name][i]))
            normalized_poses[pose_name] = norm_pos
            
        def build_normalized_point(pose_name, time_sec):
            point = JointTrajectoryPoint()
            point.positions = normalized_poses[pose_name]
            point.time_from_start.sec = int(time_sec)
            point.time_from_start.nanosec = int((time_sec - int(time_sec)) * 1e9)
            return point
            
        p1 = build_normalized_point('Place', 5.0)
        p1.velocities = [0.0] * 6
        p1.accelerations = [0.0] * 6
        
        goal_msg.trajectory.points = [p0, p1]
        
        self.get_logger().info('--- DEEP KINEMATIC TELEMETRY: PHASE 2 ---')
        self.get_logger().info(f'p0 (Pick)  : {[round(x, 4) for x in p0.positions]}')
        self.get_logger().info(f'p1 (Place) : {[round(x, 4) for x in p1.positions]}')
        self.get_logger().info('-----------------------------------------')
        
        self.get_logger().info('🚀 Phase 2: Executing High-Speed 2-Point Spline Sweep...')
        self.get_logger().info('State 2: High-Speed Sweep (5.0s duration)')
        
        # The sweep runs from 0.0s to 5.0s. 
        # We fire the attack at 50% progress (2.5s total time).
        if not self.attack_fired:
            import threading
            threading.Thread(target=self.trigger_strike_zone, args=(2.5,), daemon=True).start()
            
        self._send_goal_future2 = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future2.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Trajectory rejected by controller! (Likely a path deviation or unconfigured state)')
            raise SystemExit

        self.get_logger().info('Trajectory accepted. Waiting for physical completion...')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'Cycle complete! Result Code: {result.error_code}')
        
        # Exit cleanly to maintain functional safety (ISO 10218-1). 
        # We never autonomously retry. The operator must manually verify safety and re-run.
        self.get_logger().info('Exiting node to yield control.')
        raise SystemExit

def main(args=None):
    rclpy.init(args=args)
    node = MockPickAndPlaceClient()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
