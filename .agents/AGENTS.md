# Project Development Guidelines

## Project Context & Architecture
- **Goal**: Master's thesis on "Decentralized ZKP Authorization Meshes for Industrial Robotics in DIL (Disconnected, Intermittent, Limited) Environments". Testing the network-failure threshold (p*) where MANET authentication utilizing Zero-Knowledge Proofs (ZKPs) maintains operational continuity on an edge device, comparatively benchmarked against traditional ECC (Elliptic Curve Cryptography) baselines.
- **Hardware Constraints (CRITICAL)**: The Raspberry Pi 4 is heavily resource-constrained by ZKP cryptography, trust monitors, and network traffic sniffing (`tshark`). DO NOT propose computationally heavy ROS 2 modules (e.g., MoveIt 2).
- **Kinematic Driver Rule**: Always use `passthrough_trajectory_controller` (not `scaled_joint_trajectory_controller`). Offload trajectory spline math directly to the UR5 native hardware to prevent CPU jitter from causing `Error Code: -1` Protective Stops.
- **Kinematic Trajectory Generation**: Always use a two-phase architecture. When feeding cubic splines to the UR5, ensure Runge's phenomenon (overshoot) is suppressed by anchoring the spline with a trailing identical waypoint (e.g., `[Pick(t=1), Transfer(t=3), Place(t=5)]`). Omit `p0` at $t=0$ so the controller natively auto-prepends the current hardware state.

## Workspace Architecture Enforcement
- `src/`: STRICTLY for ROS 2 Python/C++ packages (e.g., `sentry_logic`). This prevents `colcon build` from accidentally attempting to compile microcontroller code.
- `firmware/`: STRICTLY for bare-metal microcontroller code (Arduino/PlatformIO).
- `data/`: For CSV files and timeseries evaluation datasets.
- `docs/`: For academic reports and system guides.

## Firmware Guidelines
- Do NOT run PlatformIO (`pio`) commands directly in the terminal via agent tools. The terminal environment is misconfigured for `pio`. Instead, always ask the user to click the corresponding buttons in the VS Code PlatformIO extension UI to compile, upload, or manage libraries.

## Communication Style & Maintenance
- **Communication Style**: Remain concise at all times. Avoid overly verbose explanations unless asked. Act like a highly competent, blunt Systems Engineer.
- **Maintenance Protocols**: During pivot phases and end-of-day wrap-ups, actively prompt the user to delete dead code, obsolete configuration files, and unused documentation to ensure the repository remains pristine.



