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

    def joint_state_callback(self, msg):
        self.current_joint_state = msg

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
        
        self.switch_client = self.create_client(SwitchController, '/controller_manager/switch_controller')
        self._switch_to_joint_trajectory()
        
        self._action_client = ActionClient(self, FollowJointTrajectory, '/scaled_joint_trajectory_controller/follow_joint_trajectory')
        
        # Async Attack Service Client for the Strike Zone
        self.attack_client = self.create_client(Trigger, '/inject_attack')
        
        self.timer = self.create_timer(1.0, self.run_state_machine)
        self.current_state = 0
        self.attack_fired = False

    def _switch_to_joint_trajectory(self):
        while not self.switch_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /controller_manager/switch_controller service...')

        req = SwitchController.Request()
        if hasattr(req, 'start_controllers'):
            req.start_controllers = ['scaled_joint_trajectory_controller']
            req.stop_controllers = ['forward_position_controller']
        else:
            req.activate_controllers = ['scaled_joint_trajectory_controller']
            req.deactivate_controllers = ['forward_position_controller']
        req.strictness = 1

        future = self.switch_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        self.get_logger().info('✅ Successfully activated scaled_joint_trajectory_controller!')

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

    def run_state_machine(self):
        self.timer.cancel() # Stop timer, we will drive execution via action futures
        
        # Wait for current joint states to eliminate spline whip-crack
        self.get_logger().info('Querying /joint_states for dynamic p0 injection...')
        while self.current_joint_state is None:
            rclpy.spin_once(self, timeout_sec=0.1)
            
        while not self._action_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info('Waiting for trajectory action server...')
            
        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = self.joint_names
        
        # State Machine Pathing (Unified Multi-Point Cubic Spline)
        # Omit velocities to force the controller path planner to naturally interpolate
        
        # Extract physical positions aligned with joint_names
        p0_positions = []
        for name in self.joint_names:
            idx = self.current_joint_state.name.index(name)
            p0_positions.append(self.current_joint_state.position[idx])
            
        # 0. Dynamic p0 (Current Physical State)
        p0 = JointTrajectoryPoint()
        p0.positions = p0_positions
        p0.time_from_start.sec = 0
        p0.time_from_start.nanosec = 0
        
        # 1. Approach Pick (1.5s total)
        p1 = self.build_point('Pick', 1.5)
        
        # 2. High-Speed Transfer Leg (3.0s total)
        p2 = self.build_point('Transfer', 3.0)
        
        # 3. Approach Place (4.5s total)
        p3 = self.build_point('Place', 4.5)
        
        goal_msg.trajectory.points = [p0, p1, p2, p3]
        
        self.get_logger().info('Executing High-Speed Kinematic Sweep...')
        self.get_logger().info('State 1: Approach Pick (1.5s)')
        self.get_logger().info('State 2: High-Speed Transfer (1.5s duration)')
        self.get_logger().info('State 3: Approach Place (1.5s duration)')
        
        # The Transfer leg runs from 1.5s to 3.0s. 
        # We fire the attack at 0.75s into the Transfer leg (2.25s total time).
        if not self.attack_fired:
            import threading
            threading.Thread(target=self.trigger_strike_zone, args=(2.25,), daemon=True).start()
            
        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

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
