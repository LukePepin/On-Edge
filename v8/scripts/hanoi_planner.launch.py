"""Calibrated MoveIt planning services only; trajectory execution is disabled."""
from pathlib import Path

from ament_index_python.packages import get_package_share_directory
from launch import LaunchDescription
from launch_ros.actions import Node
import xacro
import yaml


def generate_launch_description():
    root = Path(__file__).resolve().parents[2]
    calibration = root / "audit/calibration/ur5_factory_2026-09-30.yaml"
    if not calibration.is_file():
        raise RuntimeError("Extracted robot calibration is missing")
    description = Path(get_package_share_directory("ur_description"))
    moveit = Path(get_package_share_directory("ur_moveit_config"))
    robot = xacro.process_file(str(description / "urdf/ur.urdf.xacro"), mappings={
        "name": "ur", "ur_type": "ur5", "kinematics_params": str(calibration),
        "safety_limits": "true", "tf_prefix": "",
    }).toxml()
    semantic = xacro.process_file(str(moveit / "srdf/ur.srdf.xacro"), mappings={
        "name": "ur", "prefix": "",
    }).toxml()
    kinematics = yaml.safe_load((moveit / "config/kinematics.yaml").read_text())
    kinematics = kinematics.get("/**", {}).get("ros__parameters", kinematics)
    ompl = yaml.safe_load((moveit / "config/ompl_planning.yaml").read_text())
    params = {
        "robot_description": robot,
        "robot_description_semantic": semantic,
        "publish_robot_description_semantic": True,
        "allow_trajectory_execution": False,
        "disable_capabilities": "move_group/MoveGroupExecuteTrajectoryAction",
        "robot_description_planning": {"joint_limits": {
            joint: {"has_velocity_limits": True, "max_velocity": 0.06,
                    "has_acceleration_limits": True, "max_acceleration": 0.06}
            for joint in ("shoulder_pan_joint", "shoulder_lift_joint", "elbow_joint",
                          "wrist_1_joint", "wrist_2_joint", "wrist_3_joint")
        }},
        "publish_planning_scene": True,
        "publish_geometry_updates": True,
        "publish_state_updates": True,
        "publish_transforms_updates": True,
        "use_sim_time": False,
        **kinematics,
        "move_group": {
            "planning_plugin": "ompl_interface/OMPLPlanner",
            "request_adapters": "default_planner_request_adapters/FixWorkspaceBounds default_planner_request_adapters/FixStartStateBounds default_planner_request_adapters/FixStartStateCollision default_planner_request_adapters/FixStartStatePathConstraints",
            "start_state_max_bounds_error": 0.1,
            **ompl,
        },
    }
    return LaunchDescription([Node(package="moveit_ros_move_group", executable="move_group",
                                   name="hanoi_move_group", output="screen", parameters=[params])])
