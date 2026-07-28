#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from std_msgs.msg import String
import argparse
import time
import threading

class BootStormInjector(Node):
    def __init__(self, node_id):
        super().__init__(f'boot_storm_injector_{node_id}')
        
        # Must match Supervisor's BEST_EFFORT profile
        best_effort_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        self.pub = self.create_publisher(String, '/auth_request', qos_profile=best_effort_qos)
        self.node_id = node_id

    def blast(self):
        msg = String()
        msg.data = f"BOOT_STORM_REQ_{self.node_id}_{time.time()}"
        self.pub.publish(msg)
        self.get_logger().info(f"[Node {self.node_id}] Published request.")

def run_node(node_id):
    node = BootStormInjector(node_id)
    # Give DDS Discovery a moment to link publishers and subscribers
    time.sleep(1.0)
    node.blast()
    node.destroy_node()

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('-n', '--nodes', type=int, required=True, help="Number of concurrent nodes (e.g. 10)")
    args = parser.parse_args()

    print(f"🌪️ INITIATING BOOT STORM (n={args.nodes}) 🌪️")
    
    rclpy.init(args=None)
    
    threads = []
    # Launch concurrent threads to simulate simultaneous hardware boot
    for i in range(args.nodes):
        t = threading.Thread(target=run_node, args=(i,))
        threads.append(t)
        t.start()
        
    for t in threads:
        t.join()
        
    rclpy.shutdown()
    print("✅ Boot storm injected successfully.")
