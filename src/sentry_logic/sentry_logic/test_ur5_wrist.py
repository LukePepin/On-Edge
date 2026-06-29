#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class UR5WristOscillationNode(Node):
    def __init__(self):
        super().__init__('ur5_wrist_oscillation_node')
        self.publisher_ = self.create_publisher(String, '/urscript_interface/script_command', 10)
        
        # Toggle state: True = Move to +1.5, False = Move to -1.5
        self.toggle_state = True
        
        # Run the timer every 8 seconds. 
        # The movement will take ~3 seconds, leaving a 5-second dwell time where the robot is stationary.
        self.timer = self.create_timer(8.0, self.oscillate_wrist)
        
        self.get_logger().info('Wrist Oscillation Node Initialized.')
        self.get_logger().info('Waiting 8 seconds before beginning the first sweep...')

    def oscillate_wrist(self):
        msg = String()
        
        # Base neutral pose (exactly where init_robot_movement left it)
        # We only alter the 6th element (wrist_3_joint)
        if self.toggle_state:
            target_wrist = 1.5
            direction = "POSITIVE (+1.5)"
        else:
            target_wrist = -1.5
            direction = "NEGATIVE (-1.5)"
            
        # Format the URScript command
        # movej takes joint positions in radians, acceleration (rad/s^2), and velocity (rad/s)
        msg.data = f"movej([0.0, -1.57, 0.0, -1.57, 0.0, {target_wrist}], a=0.5, v=0.5)\n"
        
        self.publisher_.publish(msg)
        self.get_logger().info(f'🔄 Sweeping wrist to {direction}')
        
        # Flip the toggle for the next timer tick
        self.toggle_state = not self.toggle_state

def main(args=None):
    rclpy.init(args=args)
    node = UR5WristOscillationNode()
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
