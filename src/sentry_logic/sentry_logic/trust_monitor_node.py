#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import String
import serial
import json
import threading

class TrustMonitorNode(Node):
    def __init__(self):
        super().__init__('trust_monitor_node')
        
        # Publisher to trigger URScript commands (fastest E-Stop method)
        self.script_pub = self.create_publisher(String, '/urscript_interface/script_command', 10)
        
        # Configure Serial Port (Adjust /dev/ttyACM0 as needed on the Pi)
        self.serial_port = self.declare_parameter('serial_port', '/dev/ttyACM0').value
        self.baud_rate = self.declare_parameter('baud_rate', 115200).value
        
        self.e_stop_triggered = False
        
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1.0)
            self.get_logger().info(f"Connected to Arduino Cryptographic Edge Node on {self.serial_port}")
            
            # Start background thread to monitor serial stream
            self.monitor_thread = threading.Thread(target=self.serial_monitor_loop)
            self.monitor_thread.daemon = True
            self.monitor_thread.start()
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to connect to Serial Port: {e}")

    def serial_monitor_loop(self):
        while rclpy.ok():
            if self.e_stop_triggered:
                continue # Halt processing if E-stop already active
                
            try:
                line = self.ser.readline().decode('utf-8').strip()
                if not line:
                    continue
                    
                # Example JSON from Arduino: {"cycle": 42, "execution_time_ms": 320, "trust_score": 98.5}
                data = json.loads(line)
                exec_time = data.get('execution_time_ms', 0)
                trust_score = data.get('trust_score', 100.0)
                
                self.get_logger().info(f"Cycle: {data.get('cycle', 0)} | Exec Time: {exec_time}ms | Trust Score: {trust_score:.2f}")
                
                # Evaluation Criteria for Cryptographic Sentry
                if trust_score < 30.0 or exec_time > 500.0:
                    self.trigger_e_stop(f"Trust Score critically low ({trust_score:.2f}) or Exec Time exceeded ({exec_time}ms)")
                    
            except json.JSONDecodeError:
                # Ignore partial serial lines
                pass
            except Exception as e:
                self.get_logger().warn(f"Serial reading error: {e}")
                
    def trigger_e_stop(self, reason):
        self.e_stop_triggered = True
        self.get_logger().fatal(f"🚨 E-STOP TRIGGERED: {reason} 🚨")
        
        # Issue a fast joint stop command with 5.0 rad/s^2 deceleration
        stop_cmd = String()
        stop_cmd.data = "stopj(5.0)"
        self.script_pub.publish(stop_cmd)
        
        self.get_logger().fatal("Injected stopj(5.0) into URScript interface!")

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
