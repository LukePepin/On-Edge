#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from builtin_interfaces.msg import Duration
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint

class UR5WristOscillationNode(Node):
    def __init__(self):
        super().__init__('ur5_wrist_oscillation_node')
        
        self.get_logger().info('Creating direct JointTrajectory Publisher (bypassing buggy Action Server)...')
        self.publisher_ = self.create_publisher(
            JointTrajectory, 
            '/scaled_joint_trajectory_controller/joint_trajectory', 
            10
        )
        
        self.toggle_state = True
        # Give CycloneDDS a few seconds to discover the topic before blasting
        self.timer = self.create_timer(8.0, self.oscillate_wrist)
        self.get_logger().info('Initialized! Waiting 8 seconds for first sweep...')
        
    def oscillate_wrist(self):
        msg = JointTrajectory()
        msg.joint_names = [
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
        
        # CRITICAL: Do NOT specify velocities or accelerations! 
        # Forces the controller to use relaxed position-only interpolation.
        point.time_from_start = Duration(sec=3, nanosec=0)
        
        msg.points.append(point)
        
        self.get_logger().info(f'🔄 Publishing JointTrajectory sweep to {direction} (Topic Mode)...')
        self.publisher_.publish(msg)
        
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
