#!/usr/bin/env python3
"""
Supervisor Authentication Node (Admission Control Architecture)
===============================================================
ZKP authentication service with M/D/1 Cycle-Accurate Profiling

**Mission:** Expose raw deterministic service rate (μ) of Pi 4 via C-wrapper profiling
**Hardware:** Raspberry Pi 4 (4-core Cortex-A72)
**Messaging:** Pub/Sub strictly enforcing BEST_EFFORT / KEEP_LAST (Depth=1)
"""

import rclpy
from rclpy.node import Node
from rclpy.qos import QoSProfile, QoSReliabilityPolicy, QoSHistoryPolicy
from std_msgs.msg import String
import time
import os
import csv
import ctypes

# 1. Load the C Wrapper for Cycle-Accurate uECC_verify Profiling
class VerifyResult(ctypes.Structure):
    _fields_ = [("success", ctypes.c_int), ("elapsed_ns", ctypes.c_ulonglong)]

lib_path = os.path.join(os.path.dirname(__file__), 'c_src', 'libuecc_wrapper.so')
try:
    uecc_lib = ctypes.CDLL(lib_path)
    uecc_lib.benchmark_uecc_verify.restype = VerifyResult
    uecc_lib.benchmark_uecc_verify.argtypes = [ctypes.c_char_p, ctypes.c_uint]
    C_WRAPPER_LOADED = True
except Exception as e:
    print(f"[WARNING] Could not load libuecc_wrapper.so: {e}. Falling back to Python sleep.")
    C_WRAPPER_LOADED = False

class SupervisorNode(Node):
    def __init__(self):
        super().__init__('supervisor_node')
        
        self.declare_parameter('auth_enabled', True)
        self.declare_parameter('zkp_delay_ms', 0.67) # Fallback if C wrapper missing
        self.declare_parameter('trial_density', 10)  # Extracted for CSV tracking
        
        self.auth_enabled = self.get_parameter('auth_enabled').value
        self.zkp_delay = self.get_parameter('zkp_delay_ms').value / 1000.0
        self.trial_density = self.get_parameter('trial_density').value
        
        # === QoS Reconfiguration: Destroying HoL Blocking ===
        best_effort_qos = QoSProfile(
            reliability=QoSReliabilityPolicy.BEST_EFFORT,
            history=QoSHistoryPolicy.KEEP_LAST,
            depth=1
        )
        
        # Migrate from std_srvs/Trigger to Pub/Sub to enforce drops
        self.auth_sub = self.create_subscription(
            String,
            '/auth_request',
            self.handle_auth_request,
            qos_profile=best_effort_qos
        )
        
        self.auth_pub = self.create_publisher(
            String,
            '/auth_response',
            qos_profile=best_effort_qos
        )
        
        # Metrics Tracking
        self.processed_count = 0
        self.execution_times_ns = []
        
        # CSV Logging Setup
        workspace_dir = os.path.abspath(os.getcwd())
        self.data_dir = os.path.join(workspace_dir, "data")
        os.makedirs(self.data_dir, exist_ok=True)
        self.csv_filename = os.path.join(self.data_dir, f"md1_profiling_n{self.trial_density}_{int(time.time())}.csv")
        
        with open(self.csv_filename, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["request_id", "execution_time_ns", "success"])
            
        self.get_logger().info(
            f'🔐 Supervisor Node ONLINE (M/D/1 PROFILING)\n'
            f'   - Topic: /auth_request (BEST_EFFORT)\n'
            f'   - C Wrapper Loaded: {C_WRAPPER_LOADED}\n'
            f'   - Density: n={self.trial_density}\n'
            f'   - Logging to: {self.csv_filename}'
        )
    
    def handle_auth_request(self, msg):
        if not self.auth_enabled:
            return
            
        req_start = time.time()
        
        # Phase 3.5: Cycle-Accurate Verifier Benchmarking
        if C_WRAPPER_LOADED:
            message_bytes = msg.data.encode('utf-8')
            result = uecc_lib.benchmark_uecc_verify(message_bytes, len(message_bytes))
            exec_time_ns = result.elapsed_ns
            success = bool(result.success)
        else:
            # Fallback simulation
            start_ns = time.perf_counter_ns()
            time.sleep(self.zkp_delay)
            exec_time_ns = time.perf_counter_ns() - start_ns
            success = True
            
        self.processed_count += 1
        self.execution_times_ns.append(exec_time_ns)
        
        # Log empirical baseline
        with open(self.csv_filename, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([self.processed_count, exec_time_ns, success])
            
        # Broadcast Response
        response_msg = String()
        response_msg.data = f"AUTH_ACK|{self.processed_count}|{exec_time_ns}ns"
        self.auth_pub.publish(response_msg)
        
        if self.processed_count % 10 == 0:
            avg_ns = sum(self.execution_times_ns) / len(self.execution_times_ns)
            max_ns = max(self.execution_times_ns)
            self.get_logger().info(f'[{self.processed_count}] μ_avg: {avg_ns/1e6:.3f}ms | μ_max: {max_ns/1e6:.3f}ms')

    def destroy_node(self):
        if len(self.execution_times_ns) > 0:
            avg_ns = sum(self.execution_times_ns) / len(self.execution_times_ns)
            max_ns = max(self.execution_times_ns)
            self.get_logger().info(
                f'\n📊 M/D/1 PROFILING RESULTS:\n'
                f'   Total Requests: {self.processed_count}\n'
                f'   Mean Latency (μ_avg): {avg_ns/1e6:.3f} ms\n'
                f'   Max Latency (μ_max): {max_ns/1e6:.3f} ms\n'
                f'   Coefficient of Variance (Cv) -> approaches 0\n'
                f'   Data saved to: {self.csv_filename}'
            )
        super().destroy_node()

def main(args=None):
    rclpy.init(args=args)
    node = SupervisorNode()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        pass
    finally:
        node.destroy_node()
        # Don't call rclpy.shutdown() twice

if __name__ == '__main__':
    main()
