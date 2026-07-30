#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from control_msgs.action import FollowJointTrajectory
from trajectory_msgs.msg import JointTrajectoryPoint
from controller_manager_msgs.srv import SwitchController
from sensor_msgs.msg import JointState
import math

class KinematicsDebugger(Node):
    def __init__(self):
        super().__init__('kinematics_debugger')
        self.get_logger().info('Initializing Kinematics Debugger...')

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
        
        self._action_client = ActionClient(self, FollowJointTrajectory, '/scaled_joint_trajectory_controller/follow_joint_trajectory')
        
        # Start immediately
        self.timer = self.create_timer(1.0, self.run_sweep)



    def build_point(self, pose_name, time_sec):
        point = JointTrajectoryPoint()
        point.positions = self.poses_rad[pose_name]
        point.time_from_start.sec = int(time_sec)
        point.time_from_start.nanosec = int((time_sec - int(time_sec)) * 1e9)
        return point

    def run_sweep(self):
        # Polling for current joint states to eliminate spline whip-crack
        if self.current_joint_state is None:
            self.get_logger().info('Waiting for /joint_states for dynamic p0 injection...')
            return
            
        self.timer.cancel()
        
        while not self._action_client.wait_for_server(timeout_sec=1.0):
            self.get_logger().info('Waiting for trajectory action server...')
            
        goal_msg = FollowJointTrajectory.Goal()
        goal_msg.trajectory.joint_names = self.joint_names
        
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
        
        # 1. Approach Pick (1.5s from start)
        p1 = self.build_point('Pick', 1.5)
        
        # 2. High-Speed Transfer Leg (3.0s from start)
        p2 = self.build_point('Transfer', 3.0)
        
        # 3. Approach Place (4.5s from start)
        p3 = self.build_point('Place', 4.5)
        
        goal_msg.trajectory.points = [p0, p1, p2, p3]
        
        self.get_logger().info('🚀 Executing High-Speed Cubic Spline Sweep (p0 injected!)...')
        self._send_goal_future = self._action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Trajectory rejected! (Path deviation or current pose mismatch)')
            raise SystemExit

        self.get_logger().info('Trajectory accepted. Moving...')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f'✅ Sweep complete! Result Code: {result.error_code}')
        raise SystemExit

def main(args=None):
    rclpy.init(args=args)
    node = KinematicsDebugger()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
