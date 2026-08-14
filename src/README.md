# ROS 2 Source Directory

Root of the `colcon` workspace. Contains only ROS 2 packages — Arduino firmware lives in `firmware/` (bare-metal, flashed separately), and analysis scripts live in `scripts/`.

## Packages
- `sentry_logic/`: Raspberry Pi 4 supervisor logic — UR5 integration, serial handshake with the Arduinos, and 50 Hz telemetry logging (`joint_logger_node.py`, `stream_wrist_kinematics.py`).
- `edge_node/`: placeholder (empty).
