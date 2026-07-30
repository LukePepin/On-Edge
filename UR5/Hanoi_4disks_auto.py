#!/usr/bin/env python3
"""
Tower of Hanoi Solver - 4 Disks - ULTRA-OPTIMIZED MODE
10-step sequence (removed redundant lift-to-clearance)
Direct retreat to next tower position (saves extra joint motion)
Maximum speeds: 100% joint, 6% Cartesian (0.06s/waypoint)
15 moves total (2^4 - 1)
"""

import rclpy
from rclpy.node import Node
from rclpy.action import ActionClient
from moveit_msgs.action import MoveGroup, ExecuteTrajectory
from moveit_msgs.srv import GetCartesianPath
from moveit_msgs.msg import JointConstraint, Constraints
from geometry_msgs.msg import Pose
from sensor_msgs.msg import JointState
import ur_msgs.srv
import tf2_ros
import time


class HanoiSolver(Node):
    def __init__(self):
        super().__init__('hanoi_solver')
        
        self.setup_ros()
        self.define_positions()
        self.gripper_open = True
        
        self.get_logger().info('✓ Hanoi Solver Ready')
    
    def setup_ros(self):
        """Setup ROS2 interfaces"""
        
        # MoveGroup action
        self._move_client = ActionClient(self, MoveGroup, '/move_action')
        if not self._move_client.wait_for_server(timeout_sec=10.0):
            raise RuntimeError('MoveGroup not available')
        
        # Gripper IO
        self.io_client = self.create_client(ur_msgs.srv.SetIO, '/io_and_status_controller/set_io')
        if not self.io_client.wait_for_service(timeout_sec=5.0):
            raise RuntimeError('IO service not available')
        
        # Joint states
        self.joint_states = None
        self.joint_sub = self.create_subscription(
            JointState, '/joint_states',
            lambda msg: setattr(self, 'joint_states', msg), 10)
        
        # TF2
        self.tf_buffer = tf2_ros.Buffer()
        self.tf_listener = tf2_ros.TransformListener(self.tf_buffer, self)
        
        # Cartesian planning
        self.cartesian_client = self.create_client(GetCartesianPath, '/compute_cartesian_path')
        if not self.cartesian_client.wait_for_service(timeout_sec=5.0):
            raise RuntimeError('Cartesian service not available')
        
        # Execute trajectory
        self.execute_client = ActionClient(self, ExecuteTrajectory, '/execute_trajectory')
        if not self.execute_client.wait_for_server(timeout_sec=5.0):
            raise RuntimeError('Execute trajectory not available')
    
    def define_positions(self):
        """Define all recorded positions with TCP coordinates for 4-disk Tower of Hanoi
        
        Total positions: 49
        - Home + 3 tower fronts: 4
        - D1: 3 pickups + 3 dropoffs = 6
        - D2: 6 pickups + 3 dropoffs = 9
        - D3: 9 pickups + 3 dropoffs = 12
        - D4: 12 pickups + 3 dropoffs = 15
        - Missing: D4 P4 on T1,T2,T3 (3 positions)
        """
        
        # ========== HOME AND TOWER FRONT ==========
        self.home = [0.451393, -2.229160, 1.860002, 0.342343, 1.273064, -2.157974]
        self.home_tcp = (0.11013, 0.20151, 0.47436)
        
        self.t1f = [1.024095, -1.560400, 1.718295, -0.189088, 1.847764, -2.165603]
        self.t1f_tcp = (0.17229, 0.44985, 0.36034)
        
        self.t2f = [0.691657, -1.760931, 1.899039, -0.167903, 1.515223, -2.155339]
        self.t2f_tcp = (0.23029, 0.33834, 0.36034)
        
        self.t3f = [0.296277, -1.753591, 1.893261, -0.172260, 1.120068, -2.142656]
        self.t3f_tcp = (0.32906, 0.25205, 0.36027)
        
        # ========== D1 POSITIONS ==========
        self.d1_pickup_t1_p1 = [1.003397, -1.485043, 1.689462, -0.235874, 1.831769, -2.178946]
        self.d1_pickup_t1_p1_tcp = (0.19614, 0.47138, 0.34087)
        
        self.d1_pickup_t2_p1 = [0.673036, -1.599023, 1.809293, -0.241666, 1.467693, -2.080664]
        self.d1_pickup_t2_p1_tcp = (0.28359, 0.37646, 0.34008)
        
        self.d1_pickup_t3_p1 = [0.335979, -1.613532, 1.823183, -0.243892, 1.130752, -2.069262]
        self.d1_pickup_t3_p1_tcp = (0.37083, 0.28224, 0.34009)
        
        self.d1_dropoff_t1 = [0.996162, -1.427437, 0.943722, 0.451491, 1.790832, -2.089670]
        self.d1_dropoff_t1_tcp = (0.19051, 0.46193, 0.61521)
        
        self.d1_dropoff_t2 = [0.688889, -1.521576, 1.018037, 0.472083, 1.483728, -2.079909]
        self.d1_dropoff_t2_tcp = (0.27298, 0.37545, 0.61588)
        
        self.d1_dropoff_t3 = [0.337537, -1.524118, 1.008480, 0.480919, 1.132561, -2.067765]
        self.d1_dropoff_t3_tcp = (0.36636, 0.28125, 0.61511)
        
        # ========== D2 POSITIONS ==========
        self.d2_pickup_t1_p1 = [0.992305, -1.488281, 1.690050, -0.234090, 1.786828, -2.090832]
        self.d2_pickup_t1_p1_tcp = (0.19825, 0.47096, 0.34211)
        
        self.d2_pickup_t1_p2 = [0.999396, -1.496841, 1.581831, -0.104133, 1.812547, -2.179054]
        self.d2_pickup_t1_p2_tcp = (0.19726, 0.47227, 0.38662)
        
        self.d2_pickup_t2_p1 = [0.692771, -1.589694, 1.807518, -0.249255, 1.487251, -2.081322]
        self.d2_pickup_t2_p1_tcp = (0.27981, 0.38300, 0.33728)
        
        self.d2_pickup_t2_p2 = [0.677985, -1.607129, 1.712591, -0.136892, 1.472774, -2.080724]
        self.d2_pickup_t2_p2_tcp = (0.28432, 0.37948, 0.38055)
        
        self.d2_pickup_t3_p1 = [0.351358, -1.599683, 1.805745, -0.240086, 1.146191, -2.069777]
        self.d2_pickup_t3_p1_tcp = (0.37313, 0.28914, 0.34169)
        
        self.d2_pickup_t3_p2 = [0.352904, -1.615163, 1.711380, -0.130285, 1.147677, -2.069705]
        self.d2_pickup_t3_p2_tcp = (0.37268, 0.28959, 0.38403)
        
        self.d2_dropoff_t1 = [0.993191, -1.390357, 0.852417, 0.505930, 1.787919, -2.089479]
        self.d2_dropoff_t1_tcp = (0.19447, 0.46585, 0.61622)
        
        self.d2_dropoff_t2 = [0.688014, -1.496026, 0.969999, 0.494292, 1.482937, -2.079874]
        self.d2_dropoff_t2_tcp = (0.27826, 0.37940, 0.61797)
        
        self.d2_dropoff_t3 = [0.341937, -1.505869, 0.974897, 0.496148, 1.137028, -2.068028]
        self.d2_dropoff_t3_tcp = (0.36984, 0.28423, 0.61990)
        
        # ========== D3 POSITIONS ==========
        self.d3_pickup_t1_p1 = [0.989286, -1.474073, 1.676904, -0.235167, 1.783710, -2.090712]
        self.d3_pickup_t1_p1_tcp = (0.20275, 0.47549, 0.34113)
        
        self.d3_pickup_t1_p2 = [0.988651, -1.507871, 1.608612, -0.133098, 1.783170, -2.090772]
        self.d3_pickup_t1_p2_tcp = (0.19850, 0.46850, 0.38190)
        
        self.d3_pickup_t1_p3 = [0.990328, -1.499407, 1.497754, -0.030691, 1.784921, -2.090365]
        self.d3_pickup_t1_p3_tcp = (0.20087, 0.47338, 0.42173)
        
        self.d3_pickup_t2_p1 = [0.676068, -1.582259, 1.798230, -0.247483, 1.470677, -2.080844]
        self.d3_pickup_t2_p1_tcp = (0.29123, 0.38374, 0.34259)
        
        self.d3_pickup_t2_p2 = [0.683377, -1.599695, 1.708564, -0.140410, 1.478023, -2.080891]
        self.d3_pickup_t2_p2_tcp = (0.28497, 0.38259, 0.37936)
        
        self.d3_pickup_t2_p3 = [0.692364, -1.607009, 1.610589, -0.034988, 1.486964, -2.080880]
        self.d3_pickup_t2_p3_tcp = (0.28141, 0.38411, 0.42047)
        
        self.d3_pickup_t3_p1 = [0.347905, -1.596841, 1.806033, -0.243174, 1.142670, -2.069693]
        self.d3_pickup_t3_p1_tcp = (0.37481, 0.28838, 0.34052)
        
        self.d3_pickup_t3_p2 = [0.345005, -1.614036, 1.713861, -0.133911, 1.139771, -2.069418]
        self.d3_pickup_t3_p2_tcp = (0.37485, 0.28721, 0.38263)
        
        self.d3_pickup_t3_p3 = [0.349715, -1.610930, 1.608552, -0.031732, 1.144574, -2.069322]
        self.d3_pickup_t3_p3_tcp = (0.37683, 0.28983, 0.42269)
        
        self.d3_dropoff_t1 = [0.987502, -1.379030, 0.834633, 0.512132, 1.782271, -2.089371]
        self.d3_dropoff_t1_tcp = (0.19869, 0.46794, 0.61752)
        
        self.d3_dropoff_t2 = [0.682706, -1.482274, 0.956106, 0.494520, 1.477496, -2.079658]
        self.d3_dropoff_t2_tcp = (0.28447, 0.38186, 0.61750)
        
        self.d3_dropoff_t3 = [0.346491, -1.481315, 0.952765, 0.494017, 1.141568, -2.068137]
        self.d3_dropoff_t3_tcp = (0.37903, 0.28932, 0.61826)
        
        # ========== D4 POSITIONS ==========
        self.d4_pickup_t1_p1 = [1.008787, -1.452960, 1.637887, -0.194928, 1.843495, -2.176155]
        self.d4_pickup_t1_p1_tcp = (0.20125, 0.48274, 0.34519)

        self.d4_pickup_t1_p2 = [1.004642, -1.466652, 1.533567, -0.074917, 1.839622, -2.176047]
        self.d4_pickup_t1_p2_tcp = (0.20289, 0.48201, 0.39159)

        self.d4_pickup_t1_p3 = [1.001780, -1.469325, 1.445144, 0.016419, 1.836625, -2.175880]
        self.d4_pickup_t1_p3_tcp = (0.20399, 0.48128, 0.42743)

        self.d4_pickup_t1_p4 = [1.000223, -1.460670, 1.327450, 0.125498, 1.835210, -2.175652]
        self.d4_pickup_t1_p4_tcp = (0.20474, 0.48130, 0.46969)

        self.d4_pickup_t2_p1 = [0.702345, -1.557535, 1.755578, -0.205317, 1.537037, -2.174023]
        self.d4_pickup_t2_p1_tcp = (0.28887, 0.39111, 0.34287)

        self.d4_pickup_t2_p2 = [0.681280, -1.582523, 1.680535, -0.132463, 1.488678, -2.156633]
        self.d4_pickup_t2_p2_tcp = (0.29256, 0.38643, 0.38399)

        self.d4_pickup_t2_p3 = [0.702369, -1.576216, 1.565607, -0.011145, 1.541399, -2.178203]
        self.d4_pickup_t2_p3_tcp = (0.28992, 0.39154, 0.42542)

        self.d4_pickup_t2_p4 = [0.708049, -1.572691, 1.460995, 0.089972, 1.547092, -2.178024]
        self.d4_pickup_t2_p4_tcp = (0.28728, 0.39220, 0.46504)

        self.d4_pickup_t3_p1 = [0.380845, -1.577103, 1.780002, -0.225616, 1.219729, -2.171256]
        self.d4_pickup_t3_p1_tcp = (0.37681, 0.29892, 0.34224)

        self.d4_pickup_t3_p2 = [0.385363, -1.596037, 1.679288, -0.105940, 1.226294, -2.131326]
        self.d4_pickup_t3_p2_tcp = (0.37456, 0.29973, 0.38852)

        self.d4_pickup_t3_p3 = [0.379514, -1.596972, 1.580333, -0.006214, 1.220448, -2.131122]
        self.d4_pickup_t3_p3_tcp = (0.37684, 0.29824, 0.42772)

        self.d4_pickup_t3_p4 = [0.381516, -1.594993, 1.479949, 0.092138, 1.222521, -2.130858]
        self.d4_pickup_t3_p4_tcp = (0.37479, 0.29823, 0.46621)

        self.d4_dropoff_t1 = [1.004690, -1.303750, 0.695769, 0.585577, 1.845726, -2.144117]
        self.d4_dropoff_t1_tcp = (0.20316, 0.48154, 0.63037)

        self.d4_dropoff_t2 = [0.711991, -1.431717, 0.855196, 0.554804, 1.552929, -2.137518]
        self.d4_dropoff_t2_tcp = (0.28514, 0.39219, 0.63102)

        self.d4_dropoff_t3 = [0.380353, -1.444940, 0.871758, 0.549811, 1.221358, -2.129972]
        self.d4_dropoff_t3_tcp = (0.37842, 0.29917, 0.63071)

    
    def at_position(self, target_joints, tolerance=0.05):
        """Check if at position"""
        if not self.joint_states:
            return False
        
        joint_names = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
                      'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
        
        current = []
        for name in joint_names:
            try:
                idx = self.joint_states.name.index(name)
                current.append(self.joint_states.position[idx])
            except:
                return False
        
        return all(abs(c - t) < tolerance for c, t in zip(current, target_joints))
    
    def move_joints(self, joints, speed=1.00):
        """Move to joint position"""
        
        joint_names = ['shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint',
                      'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint']
        
        goal = MoveGroup.Goal()
        goal.request.group_name = 'ur_manipulator'
        
        constraints = Constraints()
        for name, value in zip(joint_names, joints):
            jc = JointConstraint()
            jc.joint_name = name
            jc.position = value
            jc.tolerance_above = 0.01
            jc.tolerance_below = 0.01
            jc.weight = 1.0
            constraints.joint_constraints.append(jc)
        
        goal.request.goal_constraints.append(constraints)
        goal.request.allowed_planning_time = 5.0
        goal.request.max_velocity_scaling_factor = speed
        goal.request.max_acceleration_scaling_factor = speed
        goal.planning_options.plan_only = False
        
        send_future = self._move_client.send_goal_async(goal)
        rclpy.spin_until_future_complete(self, send_future, timeout_sec=10.0)
        
        if not send_future.done() or not send_future.result().accepted:
            return False
        
        result_future = send_future.result().get_result_async()
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=30.0)
        
        return result_future.done() and result_future.result().status == 4
    
    def get_tcp_position(self):
        """Get current TCP position"""
        try:
            for _ in range(30):
                rclpy.spin_once(self, timeout_sec=0.05)
            
            transform = self.tf_buffer.lookup_transform(
                'world', 'tool0', rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=2.0))
            
            return (transform.transform.translation.x,
                   transform.transform.translation.y,
                   transform.transform.translation.z)
        except:
            return None
    
    def move_to_xyz(self, x, y, z, speed=0.06):
        """Move to X,Y,Z keeping orientation constant"""
        
        # Get current orientation
        try:
            for _ in range(30):
                rclpy.spin_once(self, timeout_sec=0.05)
            
            transform = self.tf_buffer.lookup_transform(
                'world', 'tool0', rclpy.time.Time(),
                timeout=rclpy.duration.Duration(seconds=2.0))
            
            orientation = transform.transform.rotation
        except:
            return False
        
        # Build target pose
        target = Pose()
        target.position.x = x
        target.position.y = y
        target.position.z = z
        target.orientation = orientation
        
        # Plan Cartesian path
        req = GetCartesianPath.Request()
        req.header.frame_id = 'world'
        req.header.stamp = self.get_clock().now().to_msg()
        req.group_name = 'ur_manipulator'
        req.link_name = 'tool0'
        req.waypoints = [target]
        req.max_step = 0.01  # 10mm steps for smoother motion
        req.jump_threshold = 0.0
        req.avoid_collisions = True
        
        future = self.cartesian_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=5.0)
        
        if not future.done():
            self.get_logger().error('Cartesian planning timeout')
            return False
        
        response = future.result()
        if response.fraction < 0.99:
            self.get_logger().error(f'Cartesian path only {response.fraction*100:.1f}%')
            return False
        
        # Time scale
        traj = response.solution
        for i, pt in enumerate(traj.joint_trajectory.points):
            t = (i + 1) * speed
            pt.time_from_start.sec = int(t)
            pt.time_from_start.nanosec = int((t % 1) * 1e9)
        
        # Execute
        exec_goal = ExecuteTrajectory.Goal()
        exec_goal.trajectory = traj
        
        exec_future = self.execute_client.send_goal_async(exec_goal)
        rclpy.spin_until_future_complete(self, exec_future, timeout_sec=10.0)
        
        if not exec_future.done() or not exec_future.result().accepted:
            return False
        
        result_future = exec_future.result().get_result_async()
        timeout = len(traj.joint_trajectory.points) * speed + 10.0
        rclpy.spin_until_future_complete(self, result_future, timeout_sec=timeout)
        
        return result_future.done() and result_future.result().status == 4
    
    def gripper(self, open_it):
        """Control gripper"""
        if open_it == self.gripper_open:
            return True
        
        self.get_logger().info(f'{"OPENING" if open_it else "CLOSING"} GRIPPER')
        
        # Reset pins
        for pin in [16, 17]:
            req = ur_msgs.srv.SetIO.Request()
            req.fun = 1
            req.pin = pin
            req.state = 0.0
            future = self.io_client.call_async(req)
            rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
            time.sleep(0.05)
        
        # Activate
        req = ur_msgs.srv.SetIO.Request()
        req.fun = 1
        req.pin = 16 if open_it else 17
        req.state = 1.0
        future = self.io_client.call_async(req)
        rclpy.spin_until_future_complete(self, future, timeout_sec=2.0)
        time.sleep(0.125)
        
        self.gripper_open = open_it
        self.get_logger().info(f'✓ Gripper {"OPENED" if open_it else "CLOSED"}')
        return True
    
    def move_disk(self, disk, from_tower, from_level, to_tower, next_from_tower=None):
        """Move one disk using Cartesian linear motion
        
        Args:
            next_from_tower: Tower number where next pickup occurs (for smart retreat)
        """
        
        self.get_logger().info(f'\n{"="*60}')
        self.get_logger().info(f'MOVE: {disk.upper()} T{from_tower} {from_level.upper()} → T{to_tower}')
        self.get_logger().info(f'{"="*60}')
        
        # Get joint positions
        from_front_joints = getattr(self, f't{from_tower}f')
        to_front_joints = getattr(self, f't{to_tower}f')
        pickup_joints = getattr(self, f'{disk}_pickup_t{from_tower}_{from_level}')
        dropoff_joints = getattr(self, f'{disk}_dropoff_t{to_tower}')
        
        # Determine retreat target (next pickup tower or current dropoff tower)
        if next_from_tower is not None:
            retreat_joints = getattr(self, f't{next_from_tower}f')
            retreat_label = f'T{next_from_tower}F (next pickup)'
        else:
            retreat_joints = to_front_joints
            retreat_label = f'T{to_tower}F'
        
        # Get TCP positions
        from_front_tcp = getattr(self, f't{from_tower}f_tcp')
        to_front_tcp = getattr(self, f't{to_tower}f_tcp')
        pickup_tcp = getattr(self, f'{disk}_pickup_t{from_tower}_{from_level}_tcp')
        dropoff_tcp = getattr(self, f'{disk}_dropoff_t{to_tower}_tcp')
        
        front_x, front_y, front_z = from_front_tcp
        pickup_x, pickup_y, pickup_z = pickup_tcp
        dropoff_x, dropoff_y, dropoff_z = dropoff_tcp
        
        # === PICKUP SEQUENCE ===
        self.get_logger().info(f'1. Moving to T{from_tower}F')
        if not self.move_joints(from_front_joints, speed=1.0):
            return False
        time.sleep(0.05)
        
        self.get_logger().info(f'2. Match Z height: {front_z:.4f}m → {pickup_z:.4f}m')
        if not self.move_to_xyz(front_x, front_y, pickup_z, speed=0.06):
            return False
        
        self.get_logger().info(f'3. Move forward to pickup (X,Y only, Z constant)')
        if not self.move_to_xyz(pickup_x, pickup_y, pickup_z, speed=0.06):
            return False
        
        self.get_logger().info(f'4. CLOSE GRIPPER')
        if not self.gripper(False):
            return False
        
        # === TRANSFER SEQUENCE ===
        self.get_logger().info(f'5. Lift straight up to clearance: Z={dropoff_z:.4f}m')
        if not self.move_to_xyz(pickup_x, pickup_y, dropoff_z, speed=0.06):
            return False
        
        self.get_logger().info(f'6. Move to dropoff X,Y (Z constant at clearance)')
        if not self.move_to_xyz(dropoff_x, dropoff_y, dropoff_z, speed=0.06):
            return False
        
        # === PLACEMENT SEQUENCE ===
        self.get_logger().info(f'7. Lower 50mm')
        if not self.move_to_xyz(dropoff_x, dropoff_y, dropoff_z - 0.050, speed=0.06):
            return False
        
        self.get_logger().info(f'8. OPEN GRIPPER')
        if not self.gripper(True):
            return False
        
        self.get_logger().info(f'9. Back away 40mm in Y direction (clear tower)')
        if not self.move_to_xyz(dropoff_x, dropoff_y - 0.040, dropoff_z - 0.050, speed=0.06):
            return False
        
        self.get_logger().info(f'10. Retreat to {retreat_label}')
        if not self.move_joints(retreat_joints, speed=1.00):
            return False
        time.sleep(0.05)
        
        self.get_logger().info(f'✓ Move complete\n')
        return True
    
    def solve(self):
        """Execute complete 4-disk Tower of Hanoi solution automatically"""
        
        self.get_logger().info('\n' + '='*60)
        self.get_logger().info('TOWER OF HANOI SOLVER - 4 DISKS - ULTRA-OPTIMIZED')
        self.get_logger().info('='*60)
        self.get_logger().info('Start: T1=[D1,D2,D3,D4]  Goal: T2=[D1,D2,D3,D4]')
        self.get_logger().info('Mode: AUTOMATIC (no manual pauses)')
        self.get_logger().info('Speed: MAXIMUM (100% joint, 6% Cartesian)')
        self.get_logger().info('Steps: 10 per move (removed redundant lift)')
        self.get_logger().info('Retreat: Direct to next tower (saves extra motion)')
        self.get_logger().info('Moves: 15 (2^4 - 1)')
        self.get_logger().info('='*60)
        
        # Wait for joint states
        for _ in range(20):
            rclpy.spin_once(self, timeout_sec=0.1)
            if self.joint_states:
                break
        
        # Go to home
        if not self.at_position(self.home):
            self.get_logger().info('Moving to HOME')
            if not self.move_joints(self.home):
                return False
            time.sleep(1.0)
        else:
            self.get_logger().info('✓ At HOME')
        
        # Open gripper
        if not self.gripper(True):
            return False
        
        # Define all 15 moves for 4-disk Tower of Hanoi
        moves = [
            ('d4', 1, 'p4', 3, '1. D4: T1→T3'),
            ('d3', 1, 'p3', 2, '2. D3: T1→T2'),
            ('d4', 3, 'p1', 2, '3. D4: T3→T2'),
            ('d2', 1, 'p2', 3, '4. D2: T1→T3'),
            ('d4', 2, 'p2', 1, '5. D4: T2→T1'),
            ('d3', 2, 'p1', 3, '6. D3: T2→T3'),
            ('d4', 1, 'p2', 3, '7. D4: T1→T3'),
            ('d1', 1, 'p1', 2, '8. D1: T1→T2 ★'),
            ('d4', 3, 'p3', 2, '9. D4: T3→T2'),
            ('d3', 3, 'p2', 1, '10. D3: T3→T1'),
            ('d4', 2, 'p2', 1, '11. D4: T2→T1'),
            ('d2', 3, 'p1', 2, '12. D2: T3→T2'),
            ('d4', 1, 'p2', 3, '13. D4: T1→T3'),
            ('d3', 1, 'p1', 2, '14. D3: T1→T2'),
            ('d4', 3, 'p1', 2, '15. D4: T3→T2 ✓'),
        ]
        
        input('\nPress Enter to start automatic 4-disk Tower of Hanoi solution (15 moves)...')
        start_time = time.time()
        
        for i, (disk, from_t, from_l, to_t, description) in enumerate(moves, 1):
            self.get_logger().info(f'\n\n{"#"*60}')
            self.get_logger().info(f'# MOVE {i}/15: {description}')
            self.get_logger().info(f'{"#"*60}\n')
            
            # Look ahead to next move to optimize retreat
            next_tower = None
            if i < len(moves):
                next_move = moves[i]  # i is 1-indexed, moves is 0-indexed
                next_tower = next_move[1]  # from_tower of next move
            
            if not self.move_disk(disk, from_t, from_l, to_t, next_tower):
                self.get_logger().error(f'❌ Move {i} failed!')
                return False
        
        elapsed = time.time() - start_time
        
        self.get_logger().info('\n\n' + '='*60)
        self.get_logger().info('✓✓✓ 4-DISK TOWER OF HANOI SOLVED! ✓✓✓')
        self.get_logger().info('='*60)
        self.get_logger().info(f'Total time: {elapsed:.1f} seconds')
        self.get_logger().info(f'Average per move: {elapsed/15:.1f} seconds')
        self.get_logger().info(f'Tower 2 now has: [D1, D2, D3, D4] (bottom to top)')
        self.get_logger().info('='*60)
        
        return True


def main():
    rclpy.init()
    solver = HanoiSolver()
    
    try:
        solver.solve()
    except KeyboardInterrupt:
        print('\n\nInterrupted')
    except Exception as e:
        print(f'\n\nError: {e}')
        import traceback
        traceback.print_exc()
    finally:
        solver.destroy_node()
        rclpy.shutdown()


if __name__ == '__main__':
    main()
