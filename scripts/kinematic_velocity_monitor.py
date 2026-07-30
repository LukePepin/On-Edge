#!/usr/bin/env python3
"""
SentryC2 Kinematic Velocity Monitor Node
================================================================================
Author: SentryC2 Systems Engineering
Description: Non-blocking ROS 2 node designed to monitor real-time joint-space 
             velocities from /joint_states at 125 Hz. It tracks peak joint 
             velocities, evaluates them against physical hardware limits (3.14 rad/s), 
             and provides a real-time console dashboard to assist in debugging 
             spline overshoots or preemption performance.
================================================================================
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import time
import os

# ANSI escape codes for clean CLI rendering
CLEAR_SCREEN = "\033[H\033[J"
COLOR_RESET = "\033[0m"
COLOR_BOLD = "\033[1m"
COLOR_GREEN = "\033[32m"
COLOR_YELLOW = "\033[33m"
COLOR_RED = "\033[31m"
COLOR_CYAN = "\033[36m"

class KinematicVelocityMonitor(Node):
    def __init__(self):
        super().__init__('kinematic_velocity_monitor')
        
        # Subscribe to high-frequency /joint_states (125 Hz on CB3)
        self.subscription = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )
        
        # Canonical UR5 joint ordering
        self.joint_names = [
            'shoulder_pan_joint',
            'shoulder_lift_joint',
            'elbow_joint',
            'wrist_1_joint',
            'wrist_2_joint',
            'wrist_3_joint'
        ]
        
        # State tracking parameters
        self.prev_positions = None
        self.prev_time = None
        
        # Analytical tracking fields
        self.peak_velocities = [0.0] * 6
        self.joint_limit = 3.14159  # Hard physical limit of UR5 joints in rad/s
        self.warning_threshold = 0.90  # Alert at 90% of physical limit (2.82 rad/s)
        
        # Throttle dashboard updates to 10 Hz to prevent terminal flickering
        self.last_render_time = time.time()
        self.render_interval = 0.100  # 100ms
        
        self.get_logger().info("SentryC2 Kinematic Velocity Monitor successfully initialized.")

    def joint_state_callback(self, msg):
        current_time = time.time()
        
        # Verify joint states name list and match index mapping
        joint_idx_map = {}
        for idx, name in enumerate(msg.name):
            if name in self.joint_names:
                joint_idx_map[name] = idx
                
        # If the expected joint names are not fully populated, skip the cycle
        if len(joint_idx_map) < 6:
            return
            
        # Extract positions and velocities aligned to canonical joint ordering
        positions = [msg.position[joint_idx_map[name]] for name in self.joint_names]
        
        # Extract reported velocities if populated
        reported_velocities = None
        if len(msg.velocity) >= len(msg.name):
            reported_velocities = [msg.velocity[joint_idx_map[name]] for name in self.joint_names]

        # Calculate numerical derivative as a fallback/validation mechanism
        calculated_velocities = [0.0] * 6
        if self.prev_positions is not None and self.prev_time is not None:
            dt = current_time - self.prev_time
            if dt > 0.001:  # Prevent divide-by-zero or micro-step noise
                for i in range(6):
                    # Direct first-order backward difference
                    calculated_velocities[i] = (positions[i] - self.prev_positions[i]) / dt

        # Update historical state
        self.prev_positions = positions
        self.prev_time = current_time

        # Select primary velocity source (prefer filtered reported velocity, fallback to derived)
        active_velocities = [0.0] * 6
        for i in range(6):
            val = abs(reported_velocities[i]) if reported_velocities else abs(calculated_velocities[i])
            active_velocities[i] = val
            # Update running peak hold
            if val > self.peak_velocities[i]:
                self.peak_velocities[i] = val

        # Throttle terminal rendering
        if current_time - self.last_render_time >= self.render_interval:
            self.render_dashboard(active_velocities)
            self.last_render_time = current_time

    def render_dashboard(self, current_vels):
        # Refresh stdout and clear screen
        sys_out = CLEAR_SCREEN
        sys_out += f"{COLOR_BOLD}{COLOR_CYAN}================================================================================{COLOR_RESET}\n"
        sys_out += f"{COLOR_BOLD} SENTRYC2 ROBOTIC TESTBED: REAL-TIME JOINT VELOCITY TELEMETRY MONITOR{COLOR_RESET}\n"
        sys_out += f"{COLOR_BOLD}{COLOR_CYAN}================================================================================{COLOR_RESET}\n"
        sys_out += f"Hardware Joint Speed Limit: {COLOR_BOLD}{self.joint_limit:.3f} rad/s{COLOR_RESET} | Safety Margin: {COLOR_YELLOW}90% ({(self.joint_limit * self.warning_threshold):.3f} rad/s){COLOR_RESET}\n\n"
        
        sys_out += f"{COLOR_BOLD}{'Joint Name':<22} | {'Current (rad/s)':<14} | {'Peak (rad/s)':<12} | {'Load %':<8} | {'Status':<12}{COLOR_RESET}\n"
        sys_out += f"-----------------------|----------------|--------------|----------|-------------\n"
        
        for i, name in enumerate(self.joint_names):
            curr = current_vels[i]
            peak = self.peak_velocities[i]
            load_pct = (curr / self.joint_limit) * 100.0
            
            # Formulate color-coded status based on hardware thresholds
            if curr >= self.joint_limit:
                status = f"{COLOR_BOLD}{COLOR_RED}EXCEEDED [!] {COLOR_RESET}"
                curr_color = COLOR_RED
            elif curr >= (self.joint_limit * self.warning_threshold):
                status = f"{COLOR_BOLD}{COLOR_YELLOW}ALERT [WARN]{COLOR_RESET}"
                curr_color = COLOR_YELLOW
            else:
                status = f"{COLOR_GREEN}NOMINAL     {COLOR_RESET}"
                curr_color = COLOR_GREEN
                
            sys_out += f"{name:<22} | {curr_color}{curr:>14.4f}{COLOR_RESET} | {COLOR_BOLD}{peak:>12.4f}{COLOR_RESET} | {load_pct:>7.1f}% | {status}\n"
            
        sys_out += f"{COLOR_BOLD}{COLOR_CYAN}================================================================================{COLOR_RESET}\n"
        sys_out += "Press Ctrl+C to terminate the monitor node gracefully.\n"
        
        # Write clean stream directly to standard output
        os.system('clear') if os.name == 'posix' else None
        print(sys_out, flush=True)

def main(args=None):
    import sys
    rclpy.init(args=args)
    
    # Expose global system variables to let stdout print cleanly
    global sys
    
    node = KinematicVelocityMonitor()
    try:
        rclpy.spin(node)
    except KeyboardInterrupt:
        node.get_logger().info("Keyboard Interrupt detected. Exiting velocity monitor...")
    finally:
        node.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
