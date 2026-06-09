# ROS 2 Source Directory

This directory is the root of the `colcon` workspace.
Place your ROS 2 packages and Arduino firmware projects inside this directory.

## Suggested Structure
- `edge_firmware/`: Arduino PlatformIO or Arduino IDE projects for the Cortex-M4 nodes.
- `supervisor_node/`: ROS 2 package for the Raspberry Pi 4 arbiter/supervisor logic.
- `ns3_simulation/`: NS-3 network simulation scripts.
- `data_analysis/`: Jupyter notebooks and Python scripts for processing IMU and DWT_CYCCNT telemetry.
