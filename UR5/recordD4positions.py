#!/usr/bin/env python3
"""
Tower of Hanoi Position Recorder - DISK 4 ONLY
Records joint angles AND TCP poses for D4 operations
Output format matches define_positions() exactly
"""

import rclpy
from rclpy.node import Node
from sensor_msgs.msg import JointState
import tf2_ros
import math


class HanoiPositionRecorder(Node):
    def __init__(self):
        super().__init__('hanoi_position_recorder')
        
        self.joint_states = None
        
        # Subscribe to joint states
        self.joint_sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.joint_callback,
            10
        )
        
        # Create TF2 buffer and listener for TCP pose
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        self.get_logger().info('Hanoi Position Recorder Started')
        
    def joint_callback(self, msg):
        """Receive joint states"""
        self.joint_states = msg
    
    def get_current_joints(self):
        """Get current joint positions in correct order"""
        if self.joint_states is None:
            return None
        
        joint_names = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
                      'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
        
        positions = []
        for name in joint_names:
            try:
                idx = self.joint_states.name.index(name)
                positions.append(self.joint_states.position[idx])
            except (ValueError, IndexError):
                return None
        
        return positions
    
    def get_tcp_pose(self):
        """Get TCP pose from TF2"""
        try:
            # Spin to get latest TF data
            for _ in range(30):
                rclpy.spin_once(self, timeout_sec=0.05)
            
            transform = self.tf_buffer.lookup_transform(
                'world',
                'tool0',
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=2.0)
            )
            
            # Extract position (convert to mm)
            x = transform.transform.translation.x * 1000.0
            y = transform.transform.translation.y * 1000.0
            z = transform.transform.translation.z * 1000.0
            
            # Extract orientation (quaternion -> rotation vector)
            qx = transform.transform.rotation.x
            qy = transform.transform.rotation.y
            qz = transform.transform.rotation.z
            qw = transform.transform.rotation.w
            
            # Convert quaternion to axis-angle representation
            angle = 2 * math.acos(min(1.0, max(-1.0, qw)))
            if abs(angle) < 1e-6:
                rx, ry, rz = 0.0, 0.0, 0.0
            else:
                s = math.sqrt(1 - qw * qw)
                if s < 1e-6:
                    rx, ry, rz = 0.0, 0.0, 0.0
                else:
                    rx = qx / s * angle
                    ry = qy / s * angle
                    rz = qz / s * angle
            
            return {'x': x, 'y': y, 'z': z, 'rx': rx, 'ry': ry, 'rz': rz}
        except Exception as e:
            self.get_logger().warn(f'Could not get TCP pose: {e}')
            return None


def main():
    rclpy.init()
    
    recorder = HanoiPositionRecorder()
    
    print('\n' + '='*70)
    print('TOWER OF HANOI POSITION RECORDER - DISK 4 ONLY')
    print('='*70)
    print('\nRecords joint angles AND TCP position for D4 operations')
    print('\nDISK 4 (2nd SMALLEST):')
    print('  - Can be on base (P1)')
    print('  - Can be on D1 (P2)')
    print('  - Can be on D2 (P3)')
    print('  - Can be on D3 (P4)')
    print('\nPOSITIONS TO RECORD:')
    print('  D4 Pickups: 12 positions (T1,T2,T3 at P1,P2,P3,P4)')
    print('  D4 Dropoffs: 3 positions (T1,T2,T3 clearance)')
    print('  TOTAL: 15 positions')
    print('='*70)
    
    # Define all D4 positions to record
    positions = [
        # DISK 4 - PICKUPS FROM TOWER 1 (4)
        ('D4 Pickup from Tower 1 P1 (on base)', 'd4_pickup_t1_p1'),
        ('D4 Pickup from Tower 1 P2 (on D1)', 'd4_pickup_t1_p2'),
        ('D4 Pickup from Tower 1 P3 (on D2)', 'd4_pickup_t1_p3'),
        ('D4 Pickup from Tower 1 P4 (on D3)', 'd4_pickup_t1_p4'),
        
        # DISK 4 - PICKUPS FROM TOWER 2 (4)
        ('D4 Pickup from Tower 2 P1 (on base)', 'd4_pickup_t2_p1'),
        ('D4 Pickup from Tower 2 P2 (on D1)', 'd4_pickup_t2_p2'),
        ('D4 Pickup from Tower 2 P3 (on D2)', 'd4_pickup_t2_p3'),
        ('D4 Pickup from Tower 2 P4 (on D3)', 'd4_pickup_t2_p4'),
        
        # DISK 4 - PICKUPS FROM TOWER 3 (4)
        ('D4 Pickup from Tower 3 P1 (on base)', 'd4_pickup_t3_p1'),
        ('D4 Pickup from Tower 3 P2 (on D1)', 'd4_pickup_t3_p2'),
        ('D4 Pickup from Tower 3 P3 (on D2)', 'd4_pickup_t3_p3'),
        ('D4 Pickup from Tower 3 P4 (on D3)', 'd4_pickup_t3_p4'),
        
        # DISK 4 - DROPOFFS (3)
        ('D4 Dropoff to Tower 1 (clearance)', 'd4_dropoff_t1'),
        ('D4 Dropoff to Tower 2 (clearance)', 'd4_dropoff_t2'),
        ('D4 Dropoff to Tower 3 (clearance)', 'd4_dropoff_t3'),
    ]
    
    print(f'\n\nREADY TO RECORD {len(positions)} POSITIONS')
    print('='*70)
    print('\nTIPS:')
    print('  - Move robot manually to each position')
    print('  - Center gripper over disk')
    print('  - Dropoffs: Position at safe clearance height')
    print('  - Press Enter to record each position')
    print('='*70)
    input('\nPress Enter when ready to start...')
    
    # Storage for all recorded positions
    recorded_data = {}
    
    try:
        for i, (description, var_name) in enumerate(positions, 1):
            print('\n' + '-'*70)
            print(f'POSITION {i}/{len(positions)}: {description}')
            print('-'*70)
            input('Move robot to position, then press Enter to record...')
            
            # Spin to get latest data
            for _ in range(10):
                rclpy.spin_once(recorder, timeout_sec=0.1)
            
            joints = recorder.get_current_joints()
            tcp = recorder.get_tcp_pose()
            
            if joints is None:
                print('❌ ERROR: Could not read joint states!')
                continue
            
            # Store data
            recorded_data[var_name] = {
                'description': description,
                'joints': joints,
                'tcp': tcp
            }
            
            # Display immediately
            joints_deg = [math.degrees(j) for j in joints]
            print(f'✓ Recorded: {var_name}')
            print(f'  Joints (deg): [{", ".join([f"{j:.2f}" for j in joints_deg])}]')
            if tcp:
                print(f'  TCP: X={tcp["x"]:.2f}, Y={tcp["y"]:.2f}, Z={tcp["z"]:.2f}mm')
            
    except KeyboardInterrupt:
        print('\n\n⚠ Recording interrupted by user')
    
    # Print all recorded positions in EXACT define_positions() format
    print('\n\n' + '='*70)
    print('COPY-PASTE OUTPUT FOR define_positions()')
    print('='*70)
    print('\n# ========== D4 POSITIONS ==========')
    
    for var_name, data in recorded_data.items():
        joints_str = '[' + ', '.join([f'{j:.6f}' for j in data['joints']]) + ']'
        
        print(f'self.{var_name} = {joints_str}')
        
        if data['tcp']:
            tcp = data['tcp']
            # Convert mm to meters with 5 decimal places
            tcp_str = f"({tcp['x']/1000:.5f}, {tcp['y']/1000:.5f}, {tcp['z']/1000:.5f})"
            print(f'self.{var_name}_tcp = {tcp_str}')
        else:
            print(f'self.{var_name}_tcp = (0.0, 0.0, 0.0)  # ERROR: TCP not available')
        
        print()  # Blank line between positions
    
    print('='*70)
    print('RECORDING COMPLETE!')
    print('='*70)
    print(f'\nRecorded: {len(recorded_data)}/{len(positions)} positions')
    print('\nINSTRUCTIONS:')
    print('  1. Copy the output above (starting from # ========== D4 POSITIONS)')
    print('  2. Paste into your hanoi solver script in define_positions()')
    print('  3. Replace the existing D4 positions')
    print('\nFORMAT:')
    print('  self.d4_pickup_t1_p1 = [joint angles in radians]')
    print('  self.d4_pickup_t1_p1_tcp = (x, y, z in meters)')
    print('='*70)
    
    recorder.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
