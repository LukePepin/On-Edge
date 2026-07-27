#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
from std_srvs.srv import Trigger
import csv
import time
import os
import serial
import threading
import json

class JointLoggerNode(Node):
    def __init__(self):
        super().__init__('joint_logger_node')
        
        self.latest_trust_score = 100.00
        self.serial_port = None
        self.serial_lock = threading.Lock()
        self.running = True
        
        # Connect to Arduino
        try:
            self.serial_port = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
            self.get_logger().info("Connected to Arduino on /dev/ttyACM0")
            
            # Start background thread to constantly read JSON from Arduino
            self.serial_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
            self.serial_thread.start()
        except Exception as e:
            self.get_logger().error(f"Failed to connect to Arduino: {e}")

        # Provide a ROS 2 Service to inject the attack without port conflicts
        self.attack_service = self.create_service(Trigger, '/inject_attack', self.inject_attack_callback)
        
        # Subscribe to high-frequency joint states
        self.subscription = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )
        
        workspace_dir = os.path.abspath(os.getcwd())
        data_dir = os.path.join(workspace_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.filename = os.path.join(data_dir, f"deceleration_data_{int(time.time())}.csv")
        
        try:
            self.file = open(self.filename, mode='w', newline='')
            self.csv_writer = csv.writer(self.file)
            # Write Header
            self.csv_writer.writerow([
                'timestamp_sec', 'timestamp_nanosec', 'trust_score',
                'shoulder_pan_pos', 'shoulder_lift_pos', 'elbow_pos', 'wrist_1_pos', 'wrist_2_pos', 'wrist_3_pos',
                'shoulder_pan_vel', 'shoulder_lift_vel', 'elbow_vel', 'wrist_1_vel', 'wrist_2_vel', 'wrist_3_vel'
            ])
            self.get_logger().info(f"Started logging Joint States and Trust Score to: {os.path.abspath(self.filename)}")
        except Exception as e:
            self.get_logger().error(f"Failed to open file for logging: {e}")
            self.file = None

    def serial_read_loop(self):
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                line = self.serial_port.readline().decode('utf-8').strip()
                if line.startswith('{') and line.endswith('}'):
                    data = json.loads(line)
                    if 'trust_score' in data:
                        self.latest_trust_score = float(data['trust_score'])
            except Exception as e:
                pass # Ignore occasional JSON parse errors or timeouts

    def inject_attack_callback(self, request, response):
        self.get_logger().info("Attack requested! Spawning injection thread...")
        # Spawn a thread so we don't block the ROS 2 Executor (which would drop joint telemetry)
        threading.Thread(target=self._execute_attack_sequence, daemon=True).start()
        response.success = True
        response.message = "Attack sequence initiated."
        return response
        
    def _execute_attack_sequence(self):
        if not self.serial_port or not self.serial_port.is_open:
            self.get_logger().error("Cannot attack: Serial port not open.")
            return
            
        self.get_logger().warn("INJECTING 5-SHOT CRYPTOGRAPHIC PAYLOAD...")
        with self.serial_lock:
            for i in range(5):
                try:
                    self.serial_port.write(b"ATTACK\n")
                    self.serial_port.flush()
                except Exception as e:
                    self.get_logger().error(f"Write failed: {e}")
                time.sleep(0.1)
        self.get_logger().warn("PAYLOAD INJECTION COMPLETE.")

    def joint_state_callback(self, msg):
        if self.file is None:
            return
            
        t_sec = msg.header.stamp.sec
        t_nano = msg.header.stamp.nanosec
        
        if len(msg.position) >= 6 and len(msg.velocity) >= 6:
            row = [t_sec, t_nano, self.latest_trust_score]
            row.extend(msg.position[:6])
            row.extend(msg.velocity[:6])
            
            self.csv_writer.writerow(row)

    def destroy_node(self):
        self.running = False
        if self.file:
            self.file.close()
            self.get_logger().info("Finished logging Joint States. File saved.")
        if self.serial_port:
            self.serial_port.close()
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
