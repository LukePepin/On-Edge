#!/usr/bin/env python3
"""
TF Frame Checker - Find the correct frame names for your robot
"""

import rclpy
from rclpy.node import Node
import tf2_ros
import sys


class TFFrameChecker(Node):
    def __init__(self):
        super().__init__('tf_frame_checker')
        
        # Create TF2 buffer and listener
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        self.get_logger().info('TF Frame Checker Started')
        self.get_logger().info('Waiting for TF data...')


def main():
    rclpy.init()
    
    checker = TFFrameChecker()
    
    print('\n' + '='*70)
    print('TF FRAME CHECKER')
    print('='*70)
    print('This tool will help you find the correct frame names for TCP pose')
    print('='*70)
    
    # Wait a bit for TF data
    print('\nWaiting for TF frames to be published...')
    for i in range(5):
        rclpy.spin_once(checker, timeout_sec=1.0)
        print(f'  {i+1}/5 seconds...')
    
    print('\n' + '='*70)
    print('AVAILABLE TF FRAMES:')
    print('='*70)
    
    # Get all frames
    try:
        frames = checker.tf_buffer.all_frames_as_yaml()
        print(frames)
    except Exception as e:
        print(f'Could not get frames: {e}')
        print('\nThis usually means:')
        print('1. The UR driver is not running')
        print('2. The robot_state_publisher is not running')
        print('3. TF is not being published')
        checker.destroy_node()
        rclpy.shutdown()
        return
    
    print('\n' + '='*70)
    print('COMMON FRAME NAME COMBINATIONS TO TRY:')
    print('='*70)
    
    # Common base frame names
    base_frames = ['world', 'base_link', 'base', 'ur_base_link']
    
    # Common tool/TCP frame names
    tool_frames = ['tool0', 'wrist_3_link', 'flange', 'tcp', 'ee_link']
    
    print('\nTesting frame combinations...\n')
    
    working_combinations = []
    
    for base in base_frames:
        for tool in tool_frames:
            try:
                # Try to get transform
                transform = checker.tf_buffer.lookup_transform(
                    base,
                    tool,
                    rclpy.time.Time(),
                    timeout=rclpy.duration.Duration(seconds=0.5)
                )
                
                # If we get here, the transform exists!
                x = transform.transform.translation.x
                y = transform.transform.translation.y
                z = transform.transform.translation.z
                
                print(f'✓ WORKS: {base} -> {tool}')
                print(f'  Current TCP: x={x:.3f}m, y={y:.3f}m, z={z:.3f}m')
                working_combinations.append((base, tool))
                
            except Exception:
                # This combination doesn't work
                pass
    
    print('\n' + '='*70)
    print('RESULTS:')
    print('='*70)
    
    if working_combinations:
        print(f'\n✓ Found {len(working_combinations)} working frame combination(s)!\n')
        
        for i, (base, tool) in enumerate(working_combinations, 1):
            print(f'{i}. Base: "{base}" -> Tool: "{tool}"')
        
        print('\n' + '='*70)
        print('UPDATE YOUR RECORDER SCRIPT:')
        print('='*70)
        
        # Use the first working combination
        base, tool = working_combinations[0]
        
        print(f'\nIn record_joint_and_tcp.py, change the get_tcp_pose() function:')
        print(f'\n  transform = self.tf_buffer.lookup_transform(')
        print(f'      \'{base}\',  # Base frame')
        print(f'      \'{tool}\',  # Tool frame')
        print(f'      rclpy.time.Time(),')
        print(f'      timeout=rclpy.duration.Duration(seconds=1.0)')
        print(f'  )')
        
    else:
        print('\n❌ No working frame combinations found!')
        print('\nThis means TF is not publishing the transforms.')
        print('\nTroubleshooting:')
        print('1. Make sure UR driver is running')
        print('2. Check if robot_state_publisher is running:')
        print('   ros2 node list | grep robot_state')
        print('3. Check if TF is being published:')
        print('   ros2 topic echo /tf --once')
        print('4. Check if TF_static is being published:')
        print('   ros2 topic echo /tf_static --once')
    
    print('\n' + '='*70)
    
    checker.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
