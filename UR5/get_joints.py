#!/usr/bin/env python3
"""
Tower of Hanoi Position Recorder - Disks 4 & 5
Records joint angles AND TCP poses for D4 and D5 operations
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
    print('TOWER OF HANOI POSITION RECORDER - DISKS 4 & 5')
    print('='*70)
    print('\nRecords joint angles AND TCP position for D4 and D5 operations')
    print('\nDISK CONFIGURATION (5-DISK TOWER):')
    print('  D1 (Disk 1): LARGEST     - At P1 (bottom level only)')
    print('  D2 (Disk 2): 2nd LARGEST - At P1 or P2')
    print('  D3 (Disk 3): MIDDLE      - At P1, P2, or P3')
    print('  D4 (Disk 4): 2nd SMALLEST- At P1, P2, P3, or P4')
    print('  D5 (Disk 5): SMALLEST    - At P1, P2, P3, P4, or P5')
    print('\nNEW POSITIONS TO RECORD:')
    print('  D4: 12 pickups + 3 dropoffs = 15 positions')
    print('  D5: 15 pickups + 3 dropoffs = 18 positions')
    print('  TOTAL: 33 positions')
    print('='*70)
    
    # Define all positions to record
    positions = [
        # DISK 4 - PICKUPS (12)
        ('D4 Pickup from Tower 1 P1 (on base)', 'd4_pickup_t1_p1'),
        ('D4 Pickup from Tower 1 P2 (on D1)', 'd4_pickup_t1_p2'),
        ('D4 Pickup from Tower 1 P3 (on D2)', 'd4_pickup_t1_p3'),
        ('D4 Pickup from Tower 1 P4 (on D3)', 'd4_pickup_t1_p4'),
        ('D4 Pickup from Tower 2 P1 (on base)', 'd4_pickup_t2_p1'),
        ('D4 Pickup from Tower 2 P2 (on D1)', 'd4_pickup_t2_p2'),
        ('D4 Pickup from Tower 2 P3 (on D2)', 'd4_pickup_t2_p3'),
        ('D4 Pickup from Tower 2 P4 (on D3)', 'd4_pickup_t2_p4'),
        ('D4 Pickup from Tower 3 P1 (on base)', 'd4_pickup_t3_p1'),
        ('D4 Pickup from Tower 3 P2 (on D1)', 'd4_pickup_t3_p2'),
        ('D4 Pickup from Tower 3 P3 (on D2)', 'd4_pickup_t3_p3'),
        ('D4 Pickup from Tower 3 P4 (on D3)', 'd4_pickup_t3_p4'),
        
        # DISK 4 - DROPOFFS (3)
        ('D4 Dropoff to Tower 1 (clearance)', 'd4_dropoff_t1'),
        ('D4 Dropoff to Tower 2 (clearance)', 'd4_dropoff_t2'),
        ('D4 Dropoff to Tower 3 (clearance)', 'd4_dropoff_t3'),
        
        # DISK 5 - PICKUPS (15)
        ('D5 Pickup from Tower 1 P1 (on base)', 'd5_pickup_t1_p1'),
        ('D5 Pickup from Tower 1 P2 (on D1)', 'd5_pickup_t1_p2'),
        ('D5 Pickup from Tower 1 P3 (on D2)', 'd5_pickup_t1_p3'),
        ('D5 Pickup from Tower 1 P4 (on D3)', 'd5_pickup_t1_p4'),
        ('D5 Pickup from Tower 1 P5 (on D4)', 'd5_pickup_t1_p5'),
        ('D5 Pickup from Tower 2 P1 (on base)', 'd5_pickup_t2_p1'),
        ('D5 Pickup from Tower 2 P2 (on D1)', 'd5_pickup_t2_p2'),
        ('D5 Pickup from Tower 2 P3 (on D2)', 'd5_pickup_t2_p3'),
        ('D5 Pickup from Tower 2 P4 (on D3)', 'd5_pickup_t2_p4'),
        ('D5 Pickup from Tower 2 P5 (on D4)', 'd5_pickup_t2_p5'),
        ('D5 Pickup from Tower 3 P1 (on base)', 'd5_pickup_t3_p1'),
        ('D5 Pickup from Tower 3 P2 (on D1)', 'd5_pickup_t3_p2'),
        ('D5 Pickup from Tower 3 P3 (on D2)', 'd5_pickup_t3_p3'),
        ('D5 Pickup from Tower 3 P4 (on D3)', 'd5_pickup_t3_p4'),
        ('D5 Pickup from Tower 3 P5 (on D4)', 'd5_pickup_t3_p5'),
        
        # DISK 5 - DROPOFFS (3)
        ('D5 Dropoff to Tower 1 (clearance)', 'd5_dropoff_t1'),
        ('D5 Dropoff to Tower 2 (clearance)', 'd5_dropoff_t2'),
        ('D5 Dropoff to Tower 3 (clearance)', 'd5_dropoff_t3'),
    ]
    
    print(f'\n\nREADY TO RECORD {len(positions)} POSITIONS')
    print('='*70)
    input('\nPress Enter when ready to start...')
    
    # Storage for all recorded positions
    recorded_data = {}
    
    try:
        for description, var_name in positions:
            print('\n' + '-'*70)
            print(f'NEXT: {description}')
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
        print('\n\n⚠  Recording interrupted by user')
    
    # Print all recorded positions in code format
    print('\n\n' + '='*70)
    print('RECORDED POSITIONS - COPY TO YOUR SCRIPT')
    print('='*70)
    print('\n# Paste these into your Tower of Hanoi script:')
    print('='*70)
    
    for var_name, data in recorded_data.items():
        joints_str = '[' + ', '.join([f'{j:.6f}' for j in data['joints']]) + ']'
        joints_deg = [math.degrees(j) for j in data['joints']]
        joints_deg_str = '[' + ', '.join([f'{j:.2f}' for j in joints_deg]) + ']'
        
        print(f'\n# {data["description"]}')
        print(f'self.{var_name} = {joints_str}')
        print(f'#   Joints (degrees): {joints_deg_str}')
        
        if data['tcp']:
            tcp = data['tcp']
            print(f'#   TCP: X={tcp["x"]:.2f}mm, Y={tcp["y"]:.2f}mm, Z={tcp["z"]:.2f}mm')
            print(f'#   Orientation: RX={tcp["rx"]:.3f}, RY={tcp["ry"]:.3f}, RZ={tcp["rz"]:.3f} rad')
            # Also print TCP in meters for direct use
            print(f'self.{var_name}_tcp = ({tcp["x"]/1000:.5f}, {tcp["y"]/1000:.5f}, {tcp["z"]/1000:.5f})')
        else:
            print('#   TCP: (not available)')
    
    print('\n' + '='*70)
    print('RECORDING COMPLETE!')
    print('='*70)
    print(f'\nRecorded {len(recorded_data)} of {len(positions)} positions')
    print('\nVARIABLE NAMING:')
    print('  d4_pickup_t1_p1, d4_pickup_t1_p2, ..., d4_pickup_t1_p4')
    print('  d4_pickup_t2_p1, ..., d4_pickup_t3_p4')
    print('  d4_dropoff_t1, d4_dropoff_t2, d4_dropoff_t3')
    print('  d5_pickup_t1_p1, d5_pickup_t1_p2, ..., d5_pickup_t1_p5')
    print('  d5_pickup_t2_p1, ..., d5_pickup_t3_p5')
    print('  d5_dropoff_t1, d5_dropoff_t2, d5_dropoff_t3')
    print('\nNOTE: Dropoff positions are at clearance height above each tower.')
    print('='*70)
    
    recorder.destroy_node()
    rclpy.shutdown()


if __name__ == '__main__':
    main()
