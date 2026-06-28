#!/usr/bin/env python3
import rclpy
from rclpy.node import Node
from trajectory_msgs.msg import JointTrajectory, JointTrajectoryPoint
from sensor_msgs.msg import JointState
from control_msgs.action import FollowJointTrajectory
from rclpy.action import ActionClient
import time

class UR5WristTestNode(Node):
    def __init__(self):
        super().__init__('ur5_wrist_test_node')
        
        self.action_client = ActionClient(
            self, 
            FollowJointTrajectory, 
            '/scaled_joint_trajectory_controller/follow_joint_trajectory'
        )
        
        self.current_positions = None
        self.sub = self.create_subscription(
            JointState,
            '/joint_states',
            self.state_cb,
            10
        )
        self.get_logger().info('Waiting for current joint states...')

    def state_cb(self, msg):
        if self.current_positions is None and len(msg.position) >= 6:
            names = msg.name
            positions = msg.position
            joint_map = dict(zip(names, positions))
            
            try:
                self.current_positions = [
                    joint_map['shoulder_pan_joint'],
                    joint_map['shoulder_lift_joint'],
                    joint_map['elbow_joint'],
                    joint_map['wrist_1_joint'],
                    joint_map['wrist_2_joint'],
                    joint_map['wrist_3_joint']
                ]
                self.get_logger().info("Successfully grabbed current joint states!")
                self.send_trajectory_goal()
            except KeyError:
                self.get_logger().error("Joint names do not match UR5 standard.")

    def send_trajectory_goal(self):
        self.get_logger().info("Waiting for action server to become available...")
        self.action_client.wait_for_server()
        self.get_logger().info("Action server is ACTIVE! Generating trajectory...")

        goal_msg = FollowJointTrajectory.Goal()
        msg = JointTrajectory()
        
        msg.joint_names = [
            'shoulder_pan_joint', 'shoulder_lift_joint', 'elbow_joint', 
            'wrist_1_joint', 'wrist_2_joint', 'wrist_3_joint'
        ]

        base_pos = list(self.current_positions)
        wrist_start = base_pos[5]
        zero_vel = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0]

        # Oscillate back and forth
        current_time = 0
        
        # Point 1: Gently hold current position for 1 second to anchor the spline
        point1 = JointTrajectoryPoint()
        point1.positions = list(base_pos)
        point1.time_from_start.sec = 1
        msg.points.append(point1)
        
        current_time = 1
        
        for i in range(4):
            current_time += 15
            p_pos = JointTrajectoryPoint()
            p_pos.positions = list(base_pos)
            p_pos.positions[5] = wrist_start + 3.0
            p_pos.time_from_start.sec = current_time
            msg.points.append(p_pos)

            current_time += 15
            p_neg = JointTrajectoryPoint()
            p_neg.positions = list(base_pos)
            p_neg.positions[5] = wrist_start - 3.0
            p_neg.time_from_start.sec = current_time
            msg.points.append(p_neg)

        # Final Return to start
        current_time += 15
        p_final = JointTrajectoryPoint()
        p_final.positions = list(base_pos)
        p_final.time_from_start.sec = current_time
        msg.points.append(p_final)

        goal_msg.trajectory = msg
        self.get_logger().info("Sending goal to action server...")
        
        self._send_goal_future = self.action_client.send_goal_async(goal_msg)
        self._send_goal_future.add_done_callback(self.goal_response_callback)

    def goal_response_callback(self, future):
        goal_handle = future.result()
        if not goal_handle.accepted:
            self.get_logger().error("⚠️ GOAL REJECTED BY UR5 CONTROLLER! (Check Terminal 1 for reason!)")
            import sys
            sys.exit(1)

        self.get_logger().info("✅ Goal perfectly ACCEPTED! Robot should be moving!")
        self._get_result_future = goal_handle.get_result_async()
        self._get_result_future.add_done_callback(self.get_result_callback)

    def get_result_callback(self, future):
        result = future.result().result
        self.get_logger().info(f"Trajectory finished with error code: {result.error_code}")
        import sys
        sys.exit(0)

def main(args=None):
    rclpy.init(args=args)
    node = UR5WristTestNode()
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
