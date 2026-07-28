#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from std_msgs.msg import String
import argparse
import time
import asyncio

class AsyncBootStormInjector(Node):
    def __init__(self):
        super().__init__('async_boot_storm_injector')
        
        # STRICT QoS ENFORCEMENT: BEST_EFFORT and KEEP_LAST(1)
        # Without this, HoL blocking will crash the DDS middleware
        self.best_effort_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        self.get_logger().info("🔥 EXPLICIT QoS ENFORCEMENT 🔥")
        self.get_logger().info(f"Reliability: {self.best_effort_qos.reliability}")
        self.get_logger().info(f"History: {self.best_effort_qos.history}")
        self.get_logger().info(f"Depth: {self.best_effort_qos.depth}")
        
        self.pub = self.create_publisher(String, '/auth_request', qos_profile=self.best_effort_qos)

    async def blast_packet(self, node_id):
        msg = String()
        msg.data = f"BOOT_STORM_REQ_{node_id}_{time.time()}"
        self.pub.publish(msg)
        # Removed per-packet logging to prevent IO bottlenecking during the burst

    async def execute_storm(self, num_nodes):
        self.get_logger().info(f"🌪️ INITIATING ASYNC BOOT STORM (n={num_nodes}) 🌪️")
        
        # Give DDS Discovery a moment to link publishers and subscribers
        await asyncio.sleep(1.0)
        
        tasks = []
        # Asynchronously schedule all 1000 packets for true concurrent execution
        for i in range(num_nodes):
            tasks.append(self.blast_packet(i))
            
        await asyncio.gather(*tasks)
        self.get_logger().info(f"✅ Boot storm of {num_nodes} packets injected successfully.")

def main():
    parser = argparse.ArgumentParser()
    # Enforcing minimum n=1000 statistical sample size
    parser.add_argument('-n', '--nodes', type=int, default=1000, help="Number of concurrent nodes (Default: 1000 for stat validity)")
    args = parser.parse_args()

    if args.nodes < 1000:
        print("⚠️ WARNING: A sample size below 1000 is statistically invalid for Pollaczek-Khinchine profiling. Overriding to n=1000.")
        args.nodes = 1000

    rclpy.init(args=None)
    
    injector = AsyncBootStormInjector()
    
    # Run the asyncio event loop
    loop = asyncio.get_event_loop()
    loop.run_until_complete(injector.execute_storm(args.nodes))
    
    injector.destroy_node()
    rclpy.shutdown()

if __name__ == '__main__':
    main()
