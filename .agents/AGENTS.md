# Project Development Guidelines

## Context
- Master's thesis: edge-side authorization for an industrial manipulator under cloud loss;
  eviction latency of an EWMA trust monitor on a Cortex-M4 driving a UR5 safeguard stop.
- `ground_truth_v2.md` is authoritative. Do not restate numbers from any other prose file.
- The ZKP path is a **ZKP-cost proxy** (two scalar multiplications). Never call it a
  verification. Never use the product name that begins with "Sentry" followed by "C2".
- Safety output: one pin (D12) to UR5 SI0+SI1 in parallel, Category 2 stop. No Category 0.

## Rules
- Do not modify firmware, scripts, or `data/` without an explicit request; analysis goes in `audit/`.
- Canonical files: `firmware/unified_trust_monitor_template/`, `firmware/zkp_real_profiler/`,
  `firmware/sentry_node/`, `scripts/run_test.sh`, `scripts/run_campaign.py`,
  `src/sentry_logic/sentry_logic/{joint_logger_node,stream_wrist_kinematics}.py`.
- `data/archive_pre_v5/` is superseded-firmware data; cite only as history.
- Kinematics: use `passthrough_trajectory_controller`; two-phase trajectory; omit `p0`.
- Do not run PlatformIO from the terminal; ask the user to use the VS Code extension.
- Style: concise, blunt, systems-engineering register.
