#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
import requests
import time
import serial
import threading
import json

class TrustMonitorNode(Node):
    def __init__(self):
        super().__init__('trust_monitor_node')
        
        self.get_logger().info('Initializing Dynamic Run-Time Fail-Over Monitor (Swap PoC)')
        
        # State Tracking
        self.cloud_active = True
        self.last_auth_time = time.time()
        self.auth_timeout_sec = 5.0 # Cloud Lease TTL
        
        # Cloud IdP Configuration
        self.idp_url = 'http://localhost:8080/api/auth/lease'
        
        # Serial ZKP Mesh Configuration
        self.serial_port = None
        self.serial_lock = threading.Lock()
        
        try:
            self.serial_port = serial.Serial('/dev/ttyACM0', 115200, timeout=0)
            self.get_logger().info("Connected to Edge ZKP Mesh on /dev/ttyACM0")
        except Exception as e:
            self.get_logger().error(f"Failed to connect to Serial: {e}")

        # Start the State Machine Loop
        self.timer = self.create_timer(1.0, self.monitor_loop)

    def monitor_loop(self):
        current_time = time.time()
        
        if self.cloud_active:
            # STATE A: Cloud Nominal
            try:
                # 1.0s timeout to detect EW Jamming quickly
                response = requests.get(self.idp_url, timeout=1.0) 
                if response.status_code == 200:
                    data = response.json()
                    self.last_auth_time = current_time
                    self.get_logger().info(f"☁️ Cloud Auth OK. TTL: {data.get('expires_in')}s")
            except requests.exceptions.RequestException as e:
                # STATE B: Partition Detect
                self.get_logger().warn(f"⚠️ Cloud Request Failed: {e}")
                
            # Check Lease Expiry
            if current_time - self.last_auth_time > self.auth_timeout_sec:
                self.get_logger().error(f"🚨 CLOUD LEASE EXPIRED! Initiating Dynamic Fail-Over...")
                self.fail_over_to_edge()
        else:
            # STATE C: Edge Mode (ZKP)
            self.poll_edge_auth()

    def fail_over_to_edge(self):
        # STATE C: Hot Swap
        self.cloud_active = False
        self.swap_start_time = time.time()
        self.get_logger().warn("🔄 Swapping Root-of-Trust to Local ZKP Mesh...")
        
        if self.serial_port:
            with self.serial_lock:
                self.serial_port.reset_input_buffer()
        else:
            self.get_logger().error("Cannot swap: Edge Serial Port unavailable.")
            # Trigger ROS 2 emergency stop here in real implementation

    def poll_edge_auth(self):
        if not self.serial_port or not self.serial_port.is_open:
            return
            
        try:
            time.sleep(0.01) # Buffer accumulation
            line = self.serial_port.readline().decode('utf-8').strip()
            if line.startswith('{') and line.endswith('}'):
                data = json.loads(line)
                if 'trust_score' in data:
                    score = float(data['trust_score'])
                    if hasattr(self, 'swap_start_time'):
                        latency = (time.time() - self.swap_start_time) * 1000
                        self.get_logger().info(f"✅ FAIL-OVER SUCCESS! ZKP Handshake established in {latency:.1f}ms")
                        self.get_logger().info(f"🛡️ Active Trust Score: {score}")
                        del self.swap_start_time # Only log latency once
                    else:
                        self.get_logger().info(f"🛡️ Edge Auth OK. Trust Score: {score}")
        except Exception as e:
            pass # Non-blocking read empty

def main(args=None):
    rclpy.init(args=args)
    node = TrustMonitorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
