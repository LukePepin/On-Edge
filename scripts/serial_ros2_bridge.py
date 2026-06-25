#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from std_msgs.msg import Int32
import serial
import json
import threading

class SerialBridge(Node):
    def __init__(self):
        super().__init__('serial_bridge')
        
        # Configure this based on what the Arduino enumerates as on the Pi
        self.serial_port = '/dev/ttyACM0'
        self.baud_rate = 115200
        
        try:
            self.ser = serial.Serial(self.serial_port, self.baud_rate, timeout=1)
            self.get_logger().info(f"Connected to Arduino on {self.serial_port}")
        except serial.SerialException as e:
            self.get_logger().error(f"Failed to connect to Arduino: {e}")
            raise SystemExit
            
        self.publisher_ = self.create_publisher(Int32, 'heartbeat', 10)
        
        # Start a background thread to continuously read the serial port
        self.read_thread = threading.Thread(target=self.read_serial)
        self.read_thread.daemon = True
        self.read_thread.start()

    def read_serial(self):
        while rclpy.ok():
            try:
                if self.ser.in_waiting > 0:
                    line = self.ser.readline().decode('utf-8').strip()
                    if line:
                        self.process_json(line)
            except Exception as e:
                self.get_logger().error(f"Error reading serial: {e}")

    def process_json(self, line):
        try:
            payload = json.loads(line)
            if payload.get("topic") == "heartbeat":
                msg = Int32()
                msg.data = payload.get("data", 0)
                self.publisher_.publish(msg)
                self.get_logger().info(f"Published heartbeat: {msg.data}")
        except json.JSONDecodeError:
            self.get_logger().warn(f"Received malformed JSON: {line}")

def main(args=None):
    rclpy.init(args=args)
    bridge = SerialBridge()
    try:
        rclpy.spin(bridge)
    except KeyboardInterrupt:
        pass
    finally:
        bridge.ser.close()
        bridge.destroy_node()
        rclpy.shutdown()

if __name__ == '__main__':
    main()
