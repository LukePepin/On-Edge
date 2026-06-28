#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
import time

class UR5WristTestNode(Node):
    def __init__(self):
        super().__init__('ur5_wrist_test_node')
        
        self.publisher_ = self.create_publisher(
            JointTrajectory, 
            '/scaled_joint_trajectory_controller/joint_trajectory', 
            10
        )
        
        self.current_positions = None
        self.sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.state_cb,
            10
        )
        self.get_logger().info('Waiting for current joint states...')

    def state_cb(self, msg):
        if self.current_positions is None and len(msg.position) >= 6:
            # We must map the received joints correctly based on UR5 names
            # UR5 standard joint order: shoulder_pan, shoulder_lift, elbow, wrist_1, wrist_2, wrist_3
            names = msg.name
            positions = msg.position
            
            # Build a dictionary to map names to current values
            joint_map = dict(zip(names, positions))
            
            try:
                self.current_positions = [
                    joint_map['shoulder_pan_joint'],
                    joint_map['shoulder_lift_joint'],
                    joint_map['elbow_joint'],
                    joint_map['wrist_1_joint'],
                    joint_map['wrist_2_joint'],
                    joint_map['wrist_3_joint']
                ]
                self.move_wrist()
            except KeyError:
                self.get_logger().error("Joint names do not match UR5 standard.")

    def move_wrist(self):
        msg = JointTrajectory()
        msg.joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
        ]

        # Use current positions as base
        base_pos = list(self.current_positions)
        wrist_start = base_pos[5]

        # Point 1: Current position
        point1 = JointTrajectoryPoint()
        point1.positions = list(base_pos)
        point1.time_from_start.sec = 1

        # Point 2: Swing +3.0 radians
        point2 = JointTrajectoryPoint()
        point2.positions = list(base_pos)
        point2.positions[5] = wrist_start + 3.0
        point2.time_from_start.sec = 8

        # Point 3: Swing -3.0 radians
        point3 = JointTrajectoryPoint()
        point3.positions = list(base_pos)
        point3.positions[5] = wrist_start - 3.0
        point3.time_from_start.sec = 16
        
        # Point 4: Return to start
        point4 = JointTrajectoryPoint()
        point4.positions = list(base_pos)
        point4.time_from_start.sec = 24

        msg.points = [point1, point2, point3, point4]

        self.get_logger().info('Sending dynamic Wrist-3 oscillation test to the UR5...')
        self.publisher_.publish(msg)
        
        # Give it a moment to publish, then kill the script
        time.sleep(1.0)
        import sys
        sys.exit(0)

def main(args=None):
    rclpy.init(args=args)
    node = UR5WristTestNode()
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
