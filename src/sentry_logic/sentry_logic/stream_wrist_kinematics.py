#!/usr/bin/env python3
import math
import time
import rclpy
from rclpy.node import Node
from std_msgs.msg import Float64MultiArray
from sensor_msgs.msg import JointState
from controller_manager_msgs.srv import SwitchController

class EdgeKinematicStreamer(Node):
    def __init__(self):
        super().__init__('edge_kinematic_streamer')
        self.get_logger().info('Initializing Edge-Computed Kinematic Streamer...')

        # 1. Switch Controllers: Deactivate scaled_joint_trajectory, Activate forward_position
        self.switch_client = self.create_client(SwitchController, '/controller_manager/switch_controller')
        self._switch_to_forward_position()

        # 2. Publisher for the forward position commands
        self.publisher_ = self.create_publisher(Float64MultiArray, '/forward_position_controller/commands', 10)

        # 3. Subscriber to capture the initial starting state (one-shot)
        self.initial_positions = None
        self.joint_map = {}
        self.subscription = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_state_callback,
            10
        )
        self.get_logger().info('Waiting to capture initial hardware joint states...')

    def _switch_to_forward_position(self):
        while not self.switch_client.wait_for_service(timeout_sec=1.0):
            self.get_logger().info('Waiting for /controller_manager/switch_controller service...')

        req = SwitchController.Request()
        if hasattr(req, 'start_controllers'):
            req.start_controllers = ['forward_position_controller']
            req.stop_controllers = ['scaled_joint_trajectory_controller']
        else:
            req.activate_controllers = ['forward_position_controller']
            req.deactivate_controllers = ['scaled_joint_trajectory_controller']
        req.strictness = 1 # SwitchController.Request.BEST_EFFORT

        future = self.switch_client.call_async(req)
        rclpy.spin_until_future_complete(self, future)
        
        if future.result() is not None and future.result().ok:
            self.get_logger().info('✅ Successfully activated forward_position_controller!')
        else:
            self.get_logger().error('❌ Failed to switch controllers. Make sure UR driver is running.')
            raise RuntimeError("Controller switch failed.")

    def joint_state_callback(self, msg):
        if self.initial_positions is None:
            # Safely map the incoming joint states to the canonical order
            canonical_order = [
                'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 
                'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
            ]
            
            try:
                # Build a dictionary of current positions
                current_map = dict(zip(msg.name, msg.position))
                # Extract them in the exact order required by the controller
                self.initial_positions = [current_map[joint] for joint in canonical_order]
                
                self.get_logger().info(f'✅ Captured Initial State: {self.initial_positions}')
                
                # We have what we need, destroy the subscriber so we don't process further
                self.destroy_subscription(self.subscription)
                
                # Start the 50Hz Control Loop
                self.start_time = time.time()
                self.timer = self.create_timer(0.02, self.control_loop) # 50Hz = 0.02s
                self.get_logger().info('🚀 Starting 50Hz Kinematic Edge Stream!')
            
            except KeyError as e:
                self.get_logger().warning(f'Waiting for full joint state message... Missing: {e}')

    def control_loop(self):
        if self.initial_positions is None:
            return

        # Calculate elapsed time
        t = time.time() - self.start_time
        
        # Calculate sine wave for wrist_3_joint (6th element)
        # Formula: A * sin(2 * pi * f * t)
        # Amplitude = 1.5 radians, Frequency = 0.05 Hz (1 sweep every 10 seconds)
        amplitude = 1.5
        frequency = 0.05 
        wrist_offset = amplitude * math.sin(2 * math.pi * frequency * t)

        # Build the command array
        cmd = Float64MultiArray()
        cmd.data = list(self.initial_positions)
        cmd.data[5] += wrist_offset # Apply offset to wrist_3_joint

        # Publish the raw positions at 50Hz
        self.publisher_.publish(cmd)

        # Log occasionally to prevent terminal flood
        if int(t * 50) % 100 == 0:
            self.get_logger().info(f'🌊 Streaming Sine Wave... Elapsed: {t:.1f}s | Wrist Target: {cmd.data[5]:.3f} rad')

def main(args=None):
    rclpy.init(args=args)
    node = EdgeKinematicStreamer()
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
