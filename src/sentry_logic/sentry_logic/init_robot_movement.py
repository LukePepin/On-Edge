#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Duration
from trajectory_msgs.msg import JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient

class InitRobotMovement(Node):
    def __init__(self):
        super().__init__('init_robot_movement')
        self.get_logger().info('Connecting to ROS 2 Action Server...')
        self.client = ActionClient(
            self, 
            FollowJointTrajectory, 
            '/scaled_joint_trajectory_controller/follow_joint_trajectory'
        )
        self.client.wait_for_server()
        self.get_logger().info('Server found. Sending absolute canonical home trajectory...')
        
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
        ]
        
        # We DO NOT provide a t=0 start point. We only provide the final destination!
        # The UR controller will automatically interpolate from its true hardware state.
        point = JointTrajectoryPoint()
        # A perfectly safe, neutral pose for a UR5 (straight up / L-shape)
        point.positions = [0.0, -1.57, 0.0, -1.57, 0.0, 0.0]
        point.time_from_start = Duration(sec=10, nanosec=0)
        
        goal.trajectory.points.append(point)
        
        self.future = self.client.send_goal_async(goal)
        self.future.add_done_callback(self.goal_cb)

    def goal_cb(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Goal rejected by controller!')
            return
        self.get_logger().info('Goal mathematically accepted! Moving slowly to neutral pose...')
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f"Trajectory finished with error code: {result.error_code}")
        import sys
        sys.exit(0)

def main(args=None):
    rclpy.init(args=args)
    node = InitRobotMovement()
    try:
        rclpy.spin(node)
    except SystemExit:
        pass
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
