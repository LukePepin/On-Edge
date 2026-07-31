# Codebase Audit Checklist (Final Video Run)

This strict notebook audit must be completed *before* filming the N=2 (and potentially N=4) final Phase 3 thesis videos.

## 1. Feature Additions (Pre-Flight)
- [ ] **CSV Logger Flag**: Add a boolean `attack_active` column to `joint_logger_node.py` that flips to `True` the exact millisecond the ROS 2 `/inject_attack` service is called. This guarantees we can mathematically chart the network delay (Time between `attack_active == True` and `trust_score == 0.0`).
- [ ] **Hardware Constrained Limits**: Confirm `run_test.sh` is configured to only execute N=2 or N=4 nodes (to respect the unpowered USB splitter limit) to prevent serial brownouts.

## 2. Firmware Sterility (`firmware/zkp_trust_monitor/`)
- [ ] Ensure the penalty baseline threshold is accurately calibrated (e.g., `< 400.0ms` for nominal runs).
- [ ] Ensure the attack loop iteration count accurately simulates the target Byzantine payload without permanently bricking the Arduino state.
- [ ] Confirm no leftover Serial debug `Serial.print()` statements are polluting the JSON telemetry string and risking buffer overflows on the Pi.

## 3. ROS 2 Node Sterility (`src/sentry_logic/sentry_logic/`)
- [ ] **`stream_wrist_kinematics.py`**: Verify the delay thread is firmly set to `0.5s` for the strike zone.
- [ ] **`joint_logger_node.py`**: Verify the `csv.writer` header aligns perfectly with the newly added `attack_active` row.
- [ ] **`joint_logger_node.py`**: Ensure the non-blocking serial `readline()` loop is actively flushing the buffer (`reset_input_buffer()`) so 50Hz telemetry doesn't back up.

## 4. Orchestrator Sterility (`scripts/run_test.sh`)
- [ ] Verify `pkill -f "sentry_logic/joint_logger"` is present to prevent Zombie Node spawning.
- [ ] Verify `tc qdisc del` is executed both before *and* after the test to guarantee pristine network conditions across iterations.
- [ ] Verify SSH (Port 22) and the UR5 Hardware IP are explicitly exempted from the `tc` filter to prevent catastrophic terminal lockouts during jamming.

## Approval Protocol
Once the above checklist is satisfied and the code is pushed/pulled cleanly to the Raspberry Pi, we will officially greenlight the Final Phase 3 Trials.
