# Implementation Plan: Edge-Computed Kinematic Streaming

## Goal Description
Overhaul the ROS 2 architecture to completely abandon the UR5's internal `scaled_joint_trajectory_controller` (which causes CycloneDDS memory corruption during Action Server discovery and mathematically explodes during Topic routing). Instead, we will transition to an **Edge-Computed Kinematic Stream** using the `forward_position_controller`. 

By calculating the trajectory on the Raspberry Pi and streaming the exact positions at 50Hz, we mathematically prove your thesis: The edge node is capable of real-time control, bypassing the robot's internal path solver while avoiding all DDS string serialization crashes!

## User Review Required
> [!IMPORTANT]
> This is a major architectural pivot. Instead of sending one command and letting the robot figure out how to get there, the Raspberry Pi will manually calculate every millimeter of the sweep and stream it at 50Hz over your Wi-Fi network. This heavily stresses the edge-node topology (which is exactly what your thesis is designed to test).

## Proposed Changes

### Controller Management
The `forward_position_controller` must be activated. This controller listens to a raw `Float64MultiArray` and passes it directly to the robot's hardware interface.

### New Script: `stream_wrist_kinematics.py`
We will create a new Python node that:
1. Automatically calls the `/controller_manager/switch_controller` service to stop `scaled_joint_trajectory_controller` and start `forward_position_controller`.
2. Reads the initial `/joint_states` to lock the starting position.
3. Initiates a 50Hz control loop (`0.02s` ticks).
4. Calculates a mathematically perfect `sine` wave for the wrist joint over time to guarantee ultra-smooth acceleration and deceleration.
5. Continuously publishes these precise positions to the `/forward_position_controller/commands` topic.

#### [NEW] [stream_wrist_kinematics.py](file:///C:/Users/lukep/Documents/On-Edge/src/sentry_logic/sentry_logic/stream_wrist_kinematics.py)
A Python script that generates a sine-wave trajectory and streams it.

#### [MODIFY] [setup.py](file:///C:/Users/lukep/Documents/On-Edge/src/sentry_logic/setup.py)
Add `stream_wrist_kinematics` to the entry points.

## Verification Plan
### Automated Verification
The script will internally log its sine-wave state. If the DDS string bugs were triggered, the script would crash during the controller switch.

### Manual Verification
1. You will start the UR5 External Control program.
2. You will run `ros2 run sentry_logic stream_wrist_kinematics`.
3. We will watch the wrist oscillate flawlessly, completely controlled by the Pi's math.
