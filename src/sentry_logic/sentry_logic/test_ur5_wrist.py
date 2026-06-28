#!/usr/bin/env python3
# Updated to force git sync for Pi
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from sensor_msgs.msg import JointState
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
            names = msg.name
            positions = msg.position
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
                self.get_logger().info(f"Successfully grabbed current joint states:\n{self.current_positions}")
                self.move_wrist()
            except KeyError:
                self.get_logger().error("Joint names do not match UR5 standard.")

    def move_wrist(self):
        # WAIT FOR CONTROLLER TO BE ACTIVE
        while self.publisher_.get_subscription_count() == 0:
            self.get_logger().warn("Waiting for scaled_joint_trajectory_controller to become active... (Are you playing the External Control program on the pendant?)")
            time.sleep(1.0)
            
        self.get_logger().info("Trajectory controller is active! Generating trajectory...")

        msg = JointTrajectory()
        # Leaving header.stamp empty (0) tells ROS 2 to execute IMMEDIATELY. 
        # (If we set it to 'now()', network latency causes it to arrive in the past and get rejected!)
        
        msg.joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
        ]

        # Use current positions as base
        base_pos = list(self.current_positions)
        wrist_start = base_pos[5]
        zero_vel = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # Point 1: Current position
        point1 = JointTrajectoryPoint()
        point1.positions = list(base_pos)
        point1.time_from_start.sec = 0
        point1.time_from_start.nanosec = 0

        msg.points.append(point1)

        # Oscillate back and forth 4 times, taking 15 seconds per swing (120 seconds total)
        current_time = 1
        for i in range(4):
            # Swing +3.0 radians
            current_time += 15
            p_pos = JointTrajectoryPoint()
            p_pos.positions = list(base_pos)
            p_pos.positions[5] = wrist_start + 3.0
            p_pos.time_from_start.sec = current_time
            msg.points.append(p_pos)

            # Swing -3.0 radians
            current_time += 15
            p_neg = JointTrajectoryPoint()
            p_neg.positions = list(base_pos)
            p_neg.positions[5] = wrist_start - 3.0
            p_neg.time_from_start.sec = current_time
            msg.points.append(p_neg)

        # Final Return to start
        current_time += 15
        p_final = JointTrajectoryPoint()
        p_final.positions = list(base_pos)
        p_final.time_from_start.sec = current_time
        msg.points.append(p_final)

        self.get_logger().info(f"Publishing 2-MINUTE slow trajectory to oscillate wrist...")
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
