#!/usr/bin/env python3
"""
Add Wood Base STL as Collision Object
This makes MoveIt avoid the towers during trajectory planning
"""

import rclpy
from rclpy.node import Node
from moveit_msgs.msg import PlanningScene, CollisionObject
from geometry_msgs.msg import Pose
from shape_msgs.msg import Mesh, MeshTriangle
from geometry_msgs.msg import Point
import time


class CollisionObjectManager(Node):
    def __init__(self):
        super().__init__('collision_object_manager')
        
        self.planning_scene_pub = self.create_publisher(PlanningScene, '/planning_scene', 10)
        time.sleep(1.0)
        
    def load_stl(self, filename):
        """Load STL file and convert to Mesh message"""
        self.get_logger().info(f'Loading STL: {filename}')
        
        try:
            # Read STL file (binary format)
            with open(filename, 'rb') as f:
                # Skip header (80 bytes)
                f.read(80)
                
                # Read number of triangles (4 bytes, little endian)
                num_triangles = int.from_bytes(f.read(4), byteorder='little')
                self.get_logger().info(f'  STL contains {num_triangles} triangles')
                
                mesh = Mesh()
                
                # Read each triangle
                for i in range(num_triangles):
                    # Normal vector (3 floats, 12 bytes) - skip for now
                    f.read(12)
                    
                    # Three vertices (3 floats each, 36 bytes total)
                    triangle = MeshTriangle()
                    
                    for v_idx in range(3):
                        # Read as 32-bit floats
                        import struct
                        x_bytes = f.read(4)
                        y_bytes = f.read(4)
                        z_bytes = f.read(4)
                        
                        x = struct.unpack('<f', x_bytes)[0]  # Little endian float
                        y = struct.unpack('<f', y_bytes)[0]
                        z = struct.unpack('<f', z_bytes)[0]
                        
                        # Convert to meters (STL likely in mm)
                        point = Point()
                        point.x = x / 1000.0
                        point.y = y / 1000.0
                        point.z = z / 1000.0
                        
                        mesh.vertices.append(point)
                        triangle.vertex_indices[v_idx] = len(mesh.vertices) - 1
                    
                    mesh.triangles.append(triangle)
                    
                    # Attribute byte count (2 bytes) - skip
                    f.read(2)
                
                self.get_logger().info(f'  ✓ Loaded {len(mesh.vertices)} vertices, {len(mesh.triangles)} triangles')
                return mesh
                
        except Exception as e:
            self.get_logger().error(f'Failed to load STL: {e}')
            return None
    
    def add_wood_base(self, stl_file, x=0.0, y=0.0, z=0.0, roll=0.0, pitch=0.0, yaw=0.0):
        """Add wood base as collision object"""
        
        self.get_logger().info('\nAdding wood base to planning scene...')
        self.get_logger().info(f'  Position: x={x}, y={y}, z={z}')
        self.get_logger().info(f'  Orientation: roll={roll}, pitch={pitch}, yaw={yaw}')
        
        # Load mesh
        mesh = self.load_stl(stl_file)
        if mesh is None:
            return False
        
        # Create collision object
        collision_object = CollisionObject()
        collision_object.id = 'wood_base_and_towers'
        collision_object.header.frame_id = 'world'
        
        # Set pose
        pose = Pose()
        pose.position.x = x
        pose.position.y = y
        pose.position.z = z
        
        # Convert roll/pitch/yaw to quaternion
        import math
        cy = math.cos(yaw * 0.5)
        sy = math.sin(yaw * 0.5)
        cp = math.cos(pitch * 0.5)
        sp = math.sin(pitch * 0.5)
        cr = math.cos(roll * 0.5)
        sr = math.sin(roll * 0.5)
        
        pose.orientation.w = cr * cp * cy + sr * sp * sy
        pose.orientation.x = sr * cp * cy - cr * sp * sy
        pose.orientation.y = cr * sp * cy + sr * cp * sy
        pose.orientation.z = cr * cp * sy - sr * sp * cy
        
        collision_object.meshes.append(mesh)
        collision_object.mesh_poses.append(pose)
        collision_object.operation = CollisionObject.ADD
        
        # Publish to planning scene
        planning_scene = PlanningScene()
        planning_scene.is_diff = True
        planning_scene.world.collision_objects.append(collision_object)
        
        self.planning_scene_pub.publish(planning_scene)
        time.sleep(1.0)
        
        self.get_logger().info('✓ Wood base added to planning scene!')
        self.get_logger().info('  MoveIt will now avoid the towers during planning')
        
        return True
    
    def remove_wood_base(self):
        """Remove wood base collision object"""
        
        self.get_logger().info('Removing wood base from planning scene...')
        
        collision_object = CollisionObject()
        collision_object.id = 'wood_base_and_towers'
        collision_object.header.frame_id = 'world'
        collision_object.operation = CollisionObject.REMOVE
        
        planning_scene = PlanningScene()
        planning_scene.is_diff = True
        planning_scene.world.collision_objects.append(collision_object)
        
        self.planning_scene_pub.publish(planning_scene)
        time.sleep(1.0)
        
        self.get_logger().info('✓ Wood base removed')


def main(args=None):
    rclpy.init(args=args)
    
    manager = CollisionObjectManager()
    
    try:
        print('\n' + '='*70)
        print('WOOD BASE COLLISION OBJECT MANAGER')
        print('='*70)
        print('This adds the wood base and towers to the planning scene')
        print('='*70 + '\n')
        
        stl_file = '/home/labfab/Documents/wood_base.stl'
        
        print('You need to specify where the wood base is positioned')
        print('relative to the robot base (world frame).\n')
        print('Typical values might be:')
        print('  x = 0.0 (centered)')
        print('  y = 0.0 (centered)')
        print('  z = -0.01 (slightly below robot base)')
        print('  roll, pitch, yaw = 0.0, 0.0, 0.0 (no rotation)\n')
        
        # Get position from user
        x = float(input('Enter X position (meters): ') or '0.0')
        y = float(input('Enter Y position (meters): ') or '0.0')
        z = float(input('Enter Z position (meters): ') or '-0.01')
        
        roll = float(input('Enter roll (radians): ') or '0.0')
        pitch = float(input('Enter pitch (radians): ') or '0.0')
        yaw = float(input('Enter yaw (radians): ') or '0.0')
        
        # Add collision object
        if manager.add_wood_base(stl_file, x, y, z, roll, pitch, yaw):
            print('\n' + '='*70)
            print('SUCCESS!')
            print('='*70)
            print('The wood base is now in the planning scene.')
            print('MoveIt will automatically avoid it when planning.')
            print('\nThe collision object will persist until you:')
            print('  1. Restart MoveIt, or')
            print('  2. Run this script again with "remove" option')
            print('='*70)
        
        # Keep node alive
        print('\nPress Ctrl+C to exit...')
        rclpy.spin(manager)
        
    except KeyboardInterrupt:
        print('\n\nExiting...')
    except Exception as e:
        print(f'\n\nError: {str(e)}')
        import traceback
        traceback.print_exc()
    finally:
        manager.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
