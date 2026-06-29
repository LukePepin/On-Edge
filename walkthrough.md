# Multi-Threaded Pick-and-Place & Preemption

## What Was Accomplished
The multi-threaded Trust Monitor integration is now fully implemented. You can now simulate a high-speed pick-and-place routine and trigger an exact, real-time deceleration halt if the cryptographic Trust Score drops below the safety threshold.

### 1. The Pick-and-Place Script (`pick_and_place.py`)
- Created a new script that calculates a 0.15Hz (6.6-second) sinusoidal sweep across the `shoulder_pan`, `shoulder_lift`, and `elbow` joints.
- It natively maps to the robot's `forward_position_controller` at exactly 50Hz for perfectly smooth execution.
- Added an emergency halt listener that subscribes to `/sentry/e_stop`. The moment an E-Stop fires, the Python script instantly ceases its 50Hz stream to prevent conflicting with the robot's hardware braking procedure.

### 2. Trust Monitor Kill Switch (`trust_monitor_node.py`)
- The Trust Monitor node was upgraded to broadcast the E-Stop state.
- Upon an execution time anomaly (>500ms) or a critical Trust Score drop (<30.0), the node does two things simultaneously:
  1. Fires a raw `stopj(5.0)` URScript directly to the robot controller for an immediate ISO 13849-1 compliant deceleration.
  2. Broadcasts a `std_msgs/Bool` on `/sentry/e_stop` to cleanly shut down any active Python kinematic streams.

### 3. Telemetry Logging (`joint_logger_node.py`)
- The logger was modified to automatically build absolute paths and save all high-frequency `JointState` CSVs securely into your `data/` directory, keeping the workspace perfectly clean during aggressive testing.

## How to Run the Recorded Test
Open three separate terminals on the Raspberry Pi and run them in this order:

**Terminal 1 (Telemetry Logging):**
```bash
ros2 run sentry_logic joint_logger
```

**Terminal 2 (Trust Monitor):**
```bash
ros2 run sentry_logic trust_monitor
```

**Terminal 3 (Pick and Place):**
```bash
ros2 run sentry_logic pick_and_place
```
*(Remember to press "Play" on the UR Teach Pendant AFTER launching the script to ensure a flawless connection.)*

The robot will immediately begin the pick-and-place sweep. Wait for the Trust Monitor to catch an anomaly from the Arduino serial stream. When the kill switch fires, the robot will abruptly halt, the script will safely pause, and your CSV will be safely stored in the `data/` folder for your thesis graphing!
