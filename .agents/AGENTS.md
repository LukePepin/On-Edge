# Project Development Guidelines

## Project Context & Architecture
- **Goal**: Master's thesis on an edge-local trust monitor that keeps an industrial robot (UR5) running through network loss and stops it in hardware when local verification degrades. The measured contribution is a latency model predicting stop time from verification cycle time and the EWMA weight α, validated across 335 physical trials. The system is a USB-serial star (Raspberry Pi 4 supervisor + two Arduino Nano 33 BLE verification nodes); the earlier MANET/ZKP-mesh framing and the p\* threshold were abandoned. **Authoritative references: `docs/ground_truth.md` and `docs/project_truth.md` — never restore claims those files withdraw.**
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



