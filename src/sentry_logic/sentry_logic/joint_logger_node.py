#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState, Imu
from std_srvs.srv import Trigger
import csv
import time
import requests
import os
import serial
import threading
import json

class JointLoggerNode(Node):
    def __init__(self):
        super().__init__('joint_logger_node')
        
        self.declare_parameter('trial', 0)
        self.declare_parameter('algo', 'UNKNOWN')
        self.declare_parameter('nodes', 0)
        self.declare_parameter('loss', 0)
        self.declare_parameter('iteration', 1)
        
        trial = self.get_parameter('trial').value
        algo = self.get_parameter('algo').value
        nodes = self.get_parameter('nodes').value
        loss = self.get_parameter('loss').value
        iter_num = self.get_parameter('iteration').value
        
        self.latest_trust_score = 100.00
        self.serial_port = None
        self.serial_lock = threading.Lock()
        self.running = True
        self.attack_active = False
        
        # EMA Filter State Variables for IMU (ax, ay, az)
        self.alpha = 0.2  # Smoothing factor
        self.ema_accel = [0.0, 0.0, 0.0]
        self.first_imu_reading = True
        
        try:
            # ISO-13849 Compliance: Non-blocking serial read to prevent OS buffer lag at 50Hz
            self.serial_port = serial.Serial('/dev/ttyACM0', 115200, timeout=0)
            self.get_logger().info("Connected to Arduino on /dev/ttyACM0 (Non-Blocking Mode)")
            
            self.serial_thread = threading.Thread(target=self.serial_read_loop, daemon=True)
            self.serial_thread.start()
        except Exception as e:
            self.get_logger().error(f"Failed to connect to Arduino: {e}")

        self.attack_service = self.create_service(Trigger, '/inject_attack', self.inject_attack_callback)
        
        self.subscription_joints = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )
        
        # Subscribe to UR5 Wrist IMU to capture Mechanical Deceleration
        self.subscription_imu = self.create_subscription(
            Imu,
            '/io_and_status_controller/ur_imu',
            self.imu_callback,
            10
        )
        
        workspace_dir = os.path.abspath(os.getcwd())
        data_dir = os.path.join(workspace_dir, "data")
        os.makedirs(data_dir, exist_ok=True)
        self.filename = os.path.join(data_dir, f"trial_{trial}_{algo}_n{nodes}_loss{loss}_iter{iter_num}_{int(time.time())}.csv")
        
        try:
            self.file = open(self.filename, mode='w', newline='')
            self.csv_writer = csv.writer(self.file)
            self.csv_writer.writerow([
                'timestamp_sec', 'timestamp_nanosec', 'trust_score',
                'shoulder_pan_pos', 'shoulder_lift_pos', 'elbow_pos', 'wrist_1_pos', 'wrist_2_pos', 'wrist_3_pos',
                'shoulder_pan_vel', 'shoulder_lift_vel', 'elbow_vel', 'wrist_1_vel', 'wrist_2_vel', 'wrist_3_vel',
                'imu_ax_raw', 'imu_ay_raw', 'imu_az_raw',
                'imu_ax_ema', 'imu_ay_ema', 'imu_az_ema',
                'attack_active'
            ])
            self.get_logger().info(f"Started logging Joint States and EMA IMU to: {os.path.abspath(self.filename)}")
        except Exception as e:
            self.get_logger().error(f"Failed to open file for logging: {e}")
            self.file = None

        # State storage to sync IMU with JointStates
        self.latest_raw_accel = [0.0, 0.0, 0.0]
        self.latest_joint_state_msg = None
        
        # 50Hz Independent PC-Time Logging Loop
        self.log_timer = self.create_timer(1.0 / 50.0, self.log_timer_callback)

    def serial_read_loop(self):
        while self.running and self.serial_port and self.serial_port.is_open:
            try:
                # Flush the buffer to guarantee we parse only the absolute freshest 50Hz telemetry
                self.serial_port.reset_input_buffer()
                time.sleep(0.01) # Wait briefly for a new full line to arrive
                line = self.serial_port.readline().decode('utf-8').strip()
                if line.startswith('{') and line.endswith('}'):
                    data = json.loads(line)
                    if 'trust_score' in data:
                        self.latest_trust_score = float(data['trust_score'])
            except Exception as e:
                pass 
            time.sleep(0.005) # Prevent CPU pegging in non-blocking loop

    def inject_attack_callback(self, request, response):
        self.get_logger().info("Attack requested! Spawning injection thread...")
        self.attack_active = True
        threading.Thread(target=self._execute_attack_sequence, daemon=True).start()
        response.success = True
        response.message = "Attack sequence initiated."
        return response
        
    def _execute_attack_sequence(self):
        if not self.serial_port or not self.serial_port.is_open:
            self.get_logger().error("Cannot attack: Serial port not open.")
            return
            
        algo = self.get_parameter('algo').value
        
        if algo == 'CLOUD':
            self.get_logger().warn("☁️ CLOUD MODE: Simulating Network Dependency...")
            cloud_timeout = 5.0
            start_time = time.time()
            idp_url = 'http://192.168.0.161:8080/api/auth/lease'
            
            while time.time() - start_time < cloud_timeout:
                try:
                    response = requests.get(idp_url, timeout=1.0)
                    if response.status_code == 200:
                        self.get_logger().info("☁️ Cloud Auth OK.")
                except requests.exceptions.RequestException as e:
                    self.get_logger().error(f"⚠️ Cloud Request Failed: {e}")
                
                time.sleep(0.1)
                
            self.get_logger().error("🚨 CLOUD LEASE EXPIRED! Hardware Kill Switch Triggered!")
        else:
            self.get_logger().warn("🛡️ ZKP MODE: Local Cryptographic Mesh (Instant Severance)")
            
        self.get_logger().warn("INJECTING 10-SECOND CRYPTOGRAPHIC PAYLOAD...")
        with self.serial_lock:
            # 14 iterations * 0.75s = ~10.5 seconds.
            for i in range(14):
                try:
                    self.serial_port.write(b"ATTACK\n")
                    self.serial_port.flush()
                except Exception as e:
                    self.get_logger().error(f"Write failed: {e}")
                time.sleep(0.75)
        self.get_logger().warn("PAYLOAD INJECTION COMPLETE. Hardware should auto-recover.")

    def imu_callback(self, msg):
        ax = msg.linear_acceleration.x
        ay = msg.linear_acceleration.y
        az = msg.linear_acceleration.z
        
        self.latest_raw_accel = [ax, ay, az]
        
        # Apply Exponential Moving Average (EMA) to suppress high-frequency vibrational noise
        if self.first_imu_reading:
            self.ema_accel = [ax, ay, az]
            self.first_imu_reading = False
        else:
            self.ema_accel[0] = (self.alpha * ax) + ((1 - self.alpha) * self.ema_accel[0])
            self.ema_accel[1] = (self.alpha * ay) + ((1 - self.alpha) * self.ema_accel[1])
            self.ema_accel[2] = (self.alpha * az) + ((1 - self.alpha) * self.ema_accel[2])

    def joint_state_callback(self, msg):
        if len(msg.position) >= 6 and len(msg.velocity) >= 6:
            self.latest_joint_state_msg = msg
            self.last_msg_rx_time = time.time()

    def log_timer_callback(self):
        if self.file is None or self.latest_joint_state_msg is None:
            return
            
        # Use absolute PC-time to guarantee continuous timeline even if the robot controller pauses
        now = time.time()
        t_sec = int(now)
        t_nano = int((now - t_sec) * 1e9)
        
        velocity = list(self.latest_joint_state_msg.velocity[:6])
        
        # If the RTDE stream halts (e.g. Safeguard Stop pauses the URCap), we assume physical standstill
        if hasattr(self, 'last_msg_rx_time') and (now - self.last_msg_rx_time) > 0.1:
            velocity = [0.0] * 6
        
        row = [t_sec, t_nano, self.latest_trust_score]
        row.extend(self.latest_joint_state_msg.position[:6])
        row.extend(velocity)
        row.extend(self.latest_raw_accel)
        row.extend(self.ema_accel)
        row.append(1 if self.attack_active else 0)
        
        self.csv_writer.writerow(row)

    def destroy_node(self):
        self.running = False
        if self.file:
            self.file.close()
            self.get_logger().info("Finished logging. File saved.")
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
