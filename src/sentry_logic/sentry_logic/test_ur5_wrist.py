#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Duration
from trajectory_msgs.msg import JointTrajectoryPoint
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient

class UR5WristOscillationNode(Node):
    def __init__(self):
        super().__init__('ur5_wrist_oscillation_node')
        self.get_logger().info('Connecting to ROS 2 Action Server...')
        self.client = ActionClient(
            self, 
            FollowJointTrajectory, 
            '/scaled_joint_trajectory_controller/follow_joint_trajectory'
        )
        self.client.wait_for_server()
        self.get_logger().info('Server found. Initializing wrist oscillation...')
        
        self.toggle_state = True
        # Run every 8 seconds
        self.timer = self.create_timer(8.0, self.oscillate_wrist)
        
    def oscillate_wrist(self):
        goal = FollowJointTrajectory.Goal()
        goal.trajectory.joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
        ]
        
        if self.toggle_state:
            target_wrist = 1.5
            direction = "POSITIVE (+1.5)"
        else:
            target_wrist = -1.5
            direction = "NEGATIVE (-1.5)"
            
        point = JointTrajectoryPoint()
        point.positions = [0.0, -1.57, 0.0, -1.57, 0.0, target_wrist]
        # CRITICAL FIX: We DO NOT specify velocities or accelerations! 
        # Leaving them empty forces the controller to use relaxed position-only interpolation
        # which mathematically prevents the "whip-crack" spline explosion limit error!
        point.time_from_start = Duration(sec=3, nanosec=0)
        
        goal.trajectory.points.append(point)
        
        self.get_logger().info(f'🔄 Sweeping wrist to {direction} via Action Server...')
        self.client.send_goal_async(goal)
        
        self.toggle_state = not self.toggle_state

def main(args=None):
    rclpy.init(args=args)
    node = UR5WristOscillationNode()
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
