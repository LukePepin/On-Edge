#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import time

class UR5WristTestNode(Node):
    def __init__(self):
        super().__init__('ur5_wrist_test_node')
        
        # Publish to the UR5 scaled trajectory controller
        self.publisher_ = self.create_publisher(
            JointTrajectory, 
            '/scaled_joint_trajectory_controller/joint_trajectory', 
            10
        )
        
        # Give the publisher a second to connect
        time.sleep(1.0)
        self.move_wrist()

    def move_wrist(self):
        msg = JointTrajectory()
        
        # Standard UR5 joint names
        msg.joint_names = [
            'shoulder_pan_joint', 
            'shoulder_lift_joint', 
            'elbow_joint', 
            'wrist_1_joint', 
            'wrist_2_joint', 
            'wrist_3_joint'
        ]

        # We will only oscillate wrist_3_joint (the final wrist rotation) 
        # from -3.0 radians to 3.0 radians over 20 seconds.
        # This keeps the dangerous heavy joints perfectly still!

        # Point 1: Start point
        point1 = JointTrajectoryPoint()
        point1.positions = [0.0, -1.57, 0.0, -1.57, 0.0, -3.0]
        point1.time_from_start.sec = 2

        # Point 2: Full positive swing
        point2 = JointTrajectoryPoint()
        point2.positions = [0.0, -1.57, 0.0, -1.57, 0.0, 3.0]
        point2.time_from_start.sec = 10

        # Point 3: Full negative swing
        point3 = JointTrajectoryPoint()
        point3.positions = [0.0, -1.57, 0.0, -1.57, 0.0, -3.0]
        point3.time_from_start.sec = 18

        msg.points = [point1, point2, point3]

        self.get_logger().info('Sending safe Wrist-3 oscillation test to the UR5...')
        self.publisher_.publish(msg)

def main(args=None):
    rclpy.init(args=args)
    node = UR5WristTestNode()
    
    # Sleep to allow the message to be published, then exit
    time.sleep(2)
    node.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
