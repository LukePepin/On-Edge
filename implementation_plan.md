# Phase 3.5: Multi-Threaded Pick-and-Place & Preemption

This plan details the implementation of a simulated pick-and-place kinematic script, the integration of the Trust Monitor kill switch, and the telemetry logging pipeline for the final recorded test.

## Proposed Changes

### 1. `pick_and_place.py` [NEW]
- Create a new edge-computed kinematic streamer derived from `stream_wrist_kinematics.py`.
- **Trajectory:** Instead of just oscillating the wrist, this script will apply sinusoidal offsets to the `shoulder_pan`, `shoulder_lift`, and `elbow` joints to simulate a faster pick, move, and cut motion. 
- **Preemption Listener:** The node will subscribe to a new `/sentry/e_stop` topic. If an E-Stop is triggered by the Trust Monitor, the script will immediately cease publishing `Float64MultiArray` commands to the `forward_position_controller` to prevent fighting the E-Stop command.

### 2. `trust_monitor_node.py` [MODIFY]
- **Current Behavior:** Reads the Arduino serial stream and publishes `stopj(5.0)` directly to the URScript interface on auth failure.
- **New Behavior:** Additionally publish a `std_msgs/Bool` message to `/sentry/e_stop` to notify the `pick_and_place.py` script to halt its streaming loop simultaneously.

### 3. `joint_logger_node.py` [MODIFY]
- **Current Behavior:** Saves `deceleration_data_XYZ.csv` to the current working directory.
- **New Behavior:** Ensure all CSV files are saved directly to the `data/` directory to maintain the clean repository structure.

### 4. `setup.py` [MODIFY]
- Register the new `pick_and_place` script as a ROS 2 executable entry point.

## Verification Plan
1. **Build:** Run `colcon build --packages-select sentry_logic` on the Pi.
2. **Launch Node 1 (Logger):** `ros2 run sentry_logic joint_logger`
3. **Launch Node 2 (Trust Monitor):** `ros2 run sentry_logic trust_monitor`
4. **Launch Node 3 (Kinematics):** `ros2 run sentry_logic pick_and_place`
5. **Physical Test:** Ensure the robot executes the pick-and-place motion, and verify that the E-Stop cleanly halts the robot and drops a CSV in the `data/` folder.
