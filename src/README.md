# src/

ROS 2 workspace source. Only `sentry_logic` is built (`colcon build --packages-select sentry_logic`).

- `sentry_logic/joint_logger_node.py` — 50 Hz CSV logger, serial handshake with the trust monitor, attack injection service.
- `sentry_logic/stream_wrist_kinematics.py` — two-phase UR5 trajectory, calls the attack service 0.5 s into phase 2.
- `sentry_logic/supervisor_node.py` — BEST_EFFORT/KEEP_LAST auth-request service with the `c_src/` `uECC_verify` timing wrapper (Pi-side service-rate profiling).
