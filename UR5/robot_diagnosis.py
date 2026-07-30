#!/usr/bin/env python3
"""
Test Cartesian Linear Motion for Tower of Hanoi
Implements proper linear lifting using compute_cartesian_path and execute_trajectory
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup, ExecuteTrajectory
from moveit_msgs.srv import GetCartesianPath
from moveit_msgs.msg import PlanningScene, CollisionObject, JointConstraint, Constraints, RobotTrajectory
from geometry_msgs.msg import Pose
from shape_msgs.msg import SolidPrimitive
from sensor_msgs.msg import JointState
import tf2_ros
import time
import math


class CartesianMotionTest(Node):
    def __init__(self):
        super().__init__('cartesian_test')
        
        # Joint state subscriber
        self.joint_states = None
        self.joint_sub = self.create_subscription(JointState, '/joint_states', self.joint_callback, 10)
        
        # TF2 for TCP pose
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # Planning scene publisher
        self.planning_scene_pub = self.create_publisher(PlanningScene, '/planning_scene', 10)
        time.sleep(0.5)
        
        # Cartesian path service
        self.cartesian_client = self.create_client(GetCartesianPath, '/compute_cartesian_path')
        
        # Execute trajectory action
        self.execute_client = ActionClient(self, ExecuteTrajectory, '/execute_trajectory')
        
        # Pickup position
        self.pickup_joints = [1.021712, -1.348473, 1.876637, -3.651326, -1.856198, 1.080549]
        
        self.get_logger().info('Waiting for services...')
        if not self.cartesian_client.wait_for_service(timeout_sec=5.0):
            self.get_logger().error('Cartesian service not available')
        if not self.execute_client.wait_for_server(timeout_sec=5.0):
            self.get_logger().error('Execute trajectory not available')
        self.get_logger().info('✓ Services ready')
        
    def joint_callback(self, msg):
        self.joint_states = msg
        
    def add_ground_plane(self):
        """Add ground plane"""
        planning_scene = PlanningScene()
        planning_scene.is_diff = True
        
        ground = CollisionObject()
        ground.id = 'ground'
        ground.header.frame_id = 'world'
        
        box = SolidPrimitive()
        box.type = SolidPrimitive.BOX
        box.dimensions = [5.0, 5.0, 0.01]
        
        pose = Pose()
        pose.position.z = -0.005
        pose.orientation.w = 1.0
        
        ground.primitives.append(box)
        ground.primitive_poses.append(pose)
        ground.operation = CollisionObject.ADD
        
        planning_scene.world.collision_objects.append(ground)
        self.planning_scene_pub.publish(planning_scene)
        time.sleep(0.5)
        
    def move_to_joint_position(self, joint_values, velocity_scale=0.05, accel_scale=0.05):
        """Move to joint position"""
        
        joint_names = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
                      'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
        
        goal_msg = MoveGroup.Goal()
        goal_msg.request.group_name = 'ur_manipulator'
        
        constraints = Constraints()
        for name, value in zip(joint_names, joint_values):
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = value
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)
        
        goal_msg.request.goal_constraints.append(constraints)
        goal_msg.request.allowed_planning_time = 5.0
        goal_msg.request.max_velocity_scaling_factor = velocity_scale
        goal_msg.request.max_acceleration_scaling_factor = accel_scale
        goal_msg.planning_options.plan_only = False
        
        move_client = ActionClient(self, MoveGroup, '/move_action')
        
        if not move_client.wait_for_server(timeout_sec=5.0):
            return False
        
        send_goal_future = move_client.send_goal_async(goal_msg)
        rclpy.spin_until_future_complete(self, send_goal_future, timeout_sec=10.0)
        
        if not send_goal_future.done():
            return False
            
        goal_handle = send_goal_future.result()
        if not goal_handle.accepted:
            return False
        
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=30.0)
        
        return result_future.done() and result_future.result().status == 4
    
    def get_current_tcp_pose(self):
        """Get current TCP pose from TF"""
        try:
            transform = self.tf_buffer.lookup_transform(
                'world',
                'tool0',
                rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=1.0)
            )
            
            pose = Pose()
            pose.position.x = transform.transform.translation.x
            pose.position.y = transform.transform.translation.y
            pose.position.z = transform.transform.translation.z
            pose.orientation.x = transform.transform.rotation.x
            pose.orientation.y = transform.transform.rotation.y
            pose.orientation.z = transform.transform.rotation.z
            pose.orientation.w = transform.transform.rotation.w
            
            return pose
        except Exception as e:
            self.get_logger().error(f'Failed to get TCP pose: {e}')
            return None
    
    def lift_cartesian(self, delta_z_meters):
        """Lift straight up using Cartesian path"""
        
        self.get_logger().info(f'\n{"="*60}')
        self.get_logger().info(f'CARTESIAN LIFT: +{delta_z_meters*1000:.0f}mm')
        self.get_logger().info(f'{"="*60}')
        
        # Get current pose
        current_pose = self.get_current_tcp_pose()
        if current_pose is None:
            return False
        
        self.get_logger().info(f'Current TCP: ({current_pose.position.x:.3f}, {current_pose.position.y:.3f}, {current_pose.position.z:.3f})')
        
        # Create target pose (only change Z)
        target_pose = Pose()
        target_pose.position.x = current_pose.position.x
        target_pose.position.y = current_pose.position.y
        target_pose.position.z = current_pose.position.z + delta_z_meters
        target_pose.orientation = current_pose.orientation
        
        self.get_logger().info(f'Target TCP:  ({target_pose.position.x:.3f}, {target_pose.position.y:.3f}, {target_pose.position.z:.3f})')
        
        # Compute Cartesian path
        request = GetCartesianPath.Request()
        request.header.frame_id = 'world'
        request.header.stamp = self.get_clock().now().to_msg()
        request.group_name = 'ur_manipulator'
        request.link_name = 'tool0'
        request.waypoints = [target_pose]
        request.max_step = 0.005  # 5mm resolution for smooth path
        request.jump_threshold = 0.0  # No joint space jumps
        request.avoid_collisions = True
        
        self.get_logger().info('Computing Cartesian path...')
        future = self.cartesian_client.call_async(request)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        
        if not future.done():
            self.get_logger().error('Cartesian service timeout')
            return False
        
        response = future.result()
        
        if response.fraction < 0.99:
            self.get_logger().error(f'Path only {response.fraction*100:.1f}% complete')
            return False
        
        self.get_logger().info(f'✓ Path computed: {len(response.solution.joint_trajectory.points)} waypoints')
        
        # Scale trajectory for slow, smooth motion
        trajectory = response.solution
        num_points = len(trajectory.joint_trajectory.points)
        
        # Time scaling: slow and steady
        time_per_point = 0.05  # 50ms per waypoint
        for i, point in enumerate(trajectory.joint_trajectory.points):
            point.time_from_start.sec = int((i + 1) * time_per_point)
            point.time_from_start.nanosec = int(((i + 1) * time_per_point % 1) * 1e9)
        
        self.get_logger().info(f'Trajectory duration: {num_points * time_per_point:.2f}s')
        
        # Execute trajectory
        self.get_logger().info('Executing trajectory...')
        execute_goal = ExecuteTrajectory.Goal()
        execute_goal.trajectory = trajectory
        
        execute_future = self.execute_client.send_goal_async(execute_goal)
        rclpy.spin_until_future_complete(self, execute_future, timeout_sec=10.0)
        
        if not execute_future.done():
            self.get_logger().error('Execute goal timeout')
            return False
        
        goal_handle = execute_future.result()
        if not goal_handle.accepted:
            self.get_logger().error('Execute goal rejected')
            return False
        
        self.get_logger().info('Trajectory executing...')
        result_future = goal_handle.get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=num_points * time_per_point + 10.0)
        
        if not result_future.done():
            self.get_logger().error('Execute timeout')
            return False
        
        result = result_future.result()
        if result.status == 4:
            self.get_logger().info('✓ Cartesian lift complete!')
            
            # Verify final position
            time.sleep(0.5)
            final_pose = self.get_current_tcp_pose()
            if final_pose:
                self.get_logger().info(f'Final TCP: ({final_pose.position.x:.3f}, {final_pose.position.y:.3f}, {final_pose.position.z:.3f})')
                actual_lift = (final_pose.position.z - current_pose.position.z) * 1000
                self.get_logger().info(f'Actual Z lift: {actual_lift:.1f}mm')
            
            return True
        else:
            self.get_logger().error(f'Execute failed: status {result.status}')
            return False
    
    def run_test(self):
        """Run test"""
        self.get_logger().info('\n' + '='*60)
        self.get_logger().info('CARTESIAN LINEAR MOTION TEST')
        self.get_logger().info('='*60 + '\n')
        
        self.add_ground_plane()
        
        # Wait for joint states
        self.get_logger().info('Waiting for joint states...')
        for _ in range(20):
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.joint_states is not None:
                break
        
        if self.joint_states is None:
            self.get_logger().error('No joint states received')
            return False
        
        # Test 1: Move to pickup
        input('Press Enter to move to pickup position...')
        self.get_logger().info('Moving to pickup position...')
        if not self.move_to_joint_position(self.pickup_joints):
            self.get_logger().error('Failed to reach pickup')
            return False
        
        time.sleep(1.0)
        self.get_logger().info('✓ At pickup position')
        
        # Test 2: Cartesian lift
        input('\nPress Enter to lift +330mm using Cartesian path...')
        if not self.lift_cartesian(0.330):
            self.get_logger().error('Cartesian lift failed')
            return False
        
        self.get_logger().info('\n' + '='*60)
        self.get_logger().info('✓✓✓ CARTESIAN MOTION SUCCESS! ✓✓✓')
        self.get_logger().info('='*60)
        
        return True


def main(args=None):
    rclpy.init(args=args)
    
    test = CartesianMotionTest()
    
    try:
        print('\n' + '='*60)
        print('CARTESIAN LINEAR MOTION TEST')
        print('='*60)
        print('This will test linear lifting using Cartesian path planning')
        print('='*60 + '\n')
        
        test.run_test()
        
    except KeyboardInterrupt:
        print('\n\nInterrupted')
    except Exception as e:
        print(f'\n\nError: {str(e)}')
        import traceback
        traceback.print_exc()
    finally:
        test.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
