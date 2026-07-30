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
        
        self._action_client = ActionClient(self, FollowJointTrajectory, '/scaled_joint_trajectory_controller/follow_joint_trajectory')
        
        # Async Attack Service Client for the Strike Zone
        self.attack_client = self.create_client(Trigger, '/inject_attack')
        
        self.timer = self.create_timer(1.0, self.run_phase1)
        self.current_state = 0
        self.attack_fired = False

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
        self.timer.cancel() # Stop timer, we will drive execution via action futures
        
        while not self._action_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info('Waiting for trajectory action server...')
            
        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = self.joint_names
        
        # Phase 1: Safe Initialization to Pick
        p_pick = self.build_point('Pick', 3.0)
        p_pick.velocities = [0.0] * 6
        p_pick.accelerations = [0.0] * 6
        
        goal_msg.trajectory.points = [p_pick]
        
        self.get_logger().info('Phase 1: Safe Initialization to Pick boundary (3.0s)...')
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
        self.get_logger().info(f'Phase 1 complete! Robot is perfectly aligned. Starting Phase 2...')
        self.run_phase2()

    def run_phase2(self):
        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = self.joint_names
        
        # Phase 2: High-Speed Sweep (Transfer -> Place)
        p_transfer = self.build_point('Transfer', 2.0)
        
        p_place = self.build_point('Place', 5.0)
        p_place.velocities = [0.0] * 6
        p_place.accelerations = [0.0] * 6
        
        goal_msg.trajectory.points = [p_transfer, p_place]
        
        self.get_logger().info('🚀 Phase 2: Executing High-Speed Cubic Spline Sweep...')
        self.get_logger().info('State 2: High-Speed Transfer (2.0s duration)')
        self.get_logger().info('State 3: Approach Place (3.0s duration)')
        
        # The Transfer leg runs from 0.0s to 2.0s in Phase 2. 
        # We fire the attack at 50% progress (1.0s total time relative to Phase 2 start).
        if not self.attack_fired:
            import threading
            threading.Thread(target=self.trigger_strike_zone, args=(1.0,), daemon=True).start()
            
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
