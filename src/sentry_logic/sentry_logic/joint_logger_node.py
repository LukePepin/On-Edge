#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import csv
import time
import os

class JointLoggerNode(Node):
    def __init__(self):
        super().__init__('joint_logger_node')
        
        # Subscribe to high-frequency joint states
        self.subscription = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )
        
        # Prepare CSV file in the data/ directory
        # The workspace root is one level up from src, but the node is typically run from the root.
        # So we'll use an absolute path relative to the current working directory, or just 'data/'.
        # Since 'data' is at the root of the On-Edge folder, 'data/filename' is correct when run from the root.
        
        # Determine the absolute path to the data folder
        workspace_dir = os.path.abspath(os.getcwd())
        data_dir = os.path.join(workspace_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.filename = os.path.join(data_dir, f"deceleration_data_{int(time.time())}.csv")
        
        try:
            self.file = open(self.filename, mode='w', newline='')
            self.csv_writer = csv.writer(self.file)
            # Write Header
            self.csv_writer.writerow([
                'timestamp_sec', 'timestamp_nanosec', 
                'shoulder_pan_pos', 'shoulder_lift_pos', 'elbow_pos', 'wrist_1_pos', 'wrist_2_pos', 'wrist_3_pos',
                'shoulder_pan_vel', 'shoulder_lift_vel', 'elbow_vel', 'wrist_1_vel', 'wrist_2_vel', 'wrist_3_vel'
            ])
            self.get_logger().info(f"Started logging Joint States to: {os.path.abspath(self.filename)}")
        except Exception as e:
            self.get_logger().error(f"Failed to open file for logging: {e}")
            self.file = None

    def joint_state_callback(self, msg):
        if self.file is None:
            return
            
        # Extract time
        t_sec = msg.header.stamp.sec
        t_nano = msg.header.stamp.nanosec
        
        # Ensure we capture all 6 joints
        if len(msg.position) >= 6 and len(msg.velocity) >= 6:
            row = [t_sec, t_nano]
            row.extend(msg.position[:6])
            row.extend(msg.velocity[:6])
            
            self.csv_writer.writerow(row)

    def destroy_node(self):
        if self.file:
            self.file.close()
            self.get_logger().info("Finished logging Joint States. File saved.")
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = JointLoggerNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
