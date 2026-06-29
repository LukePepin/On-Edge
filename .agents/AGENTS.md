# Project Development Guidelines
- Do NOT run PlatformIO (`pio`) commands directly in the terminal via agent tools. The terminal environment is misconfigured for `pio`. Instead, always ask the user to click the corresponding buttons in the VS Code PlatformIO extension UI to compile, upload, or manage libraries.
- **Workspace Architecture Enforcement:**
  - `src/`: STRICTLY for ROS 2 Python/C++ packages (e.g., `sentry_logic`). This prevents `colcon build` from accidentally attempting to compile microcontroller code.
  - `firmware/`: STRICTLY for bare-metal microcontroller code (Arduino/PlatformIO).
  - `data/`: For CSV files and timeseries evaluation datasets.
  - `docs/`: For academic reports and system guides.
- **Communication Style:** Remain concise at all times. Avoid overly verbose explanations unless asked.
- **Maintenance Protocols:** During pivot phases and end-of-day wrap-ups, actively prompt the user to delete dead code, obsolete configuration files, and unused documentation to ensure the repository remains pristine.
