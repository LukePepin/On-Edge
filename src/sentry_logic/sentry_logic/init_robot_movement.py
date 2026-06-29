#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String

class URScriptTestNode(Node):
    def __init__(self):
        super().__init__('urscript_test_node')
        self.publisher_ = self.create_publisher(String, '/urscript_interface/script_command', 10)
        
        # Give the publisher a second to connect to the DDS network
        self.timer = self.create_timer(1.0, self.send_command)
        self.get_logger().info('Node initialized. Waiting for DDS discovery before sending URScript...')
        self.command_sent = False

    def send_command(self):
        if not self.command_sent:
            msg = String()
            # movej([base, shoulder, elbow, wrist1, wrist2, wrist3], acceleration, velocity)
            # This rotates the wrist 1.0 radians (relative to standard 0) slowly and safely
            msg.data = "movej([0.0, -1.57, 0.0, -1.57, 0.0, 1.0], a=0.1, v=0.1)\n"
            self.publisher_.publish(msg)
            self.get_logger().info(f'✅ Sent raw URScript via ROS 2: {msg.data.strip()}')
            self.command_sent = True
            
            # Shut down after sending
            self.get_logger().info('Command sent. Shutting down node.')
            import sys
            sys.exit(0)

def main(args=None):
    rclpy.init(args=args)
    node = URScriptTestNode()
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
