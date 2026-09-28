# Review of the historical launchers and the V8 recovery policy

The historical files are kept unchanged as provenance. V8 does not call any of them.

## What the historical launchers do

| File | Behaviour worth knowing | V8 treatment |
| --- | --- | --- |
| `scripts/run_test.sh` | `sudo ip link set dev lo multicast on`; `ROS_LOCALHOST_ONLY=1`; `pkill -f` of logger/kinematics; `sudo killall tshark`; repeated `sudo iptables -D OUTPUT ... 8080`; `sudo tshark` capture on `wlan0`; `taskset 0x7` + `sudo chrt -f 99` on the logger and kinematics; a fixed 6 s handshake wait and "4 SECONDS TO PRESS PLAY"; `ros2 control switch_controllers` to passthrough after Play; `stty sane` | none of these; no sudo; the daemon refuses a busy port and names the PID; readiness is checked by acknowledgements, not sleeps. ROS environment (localhost-only, multicast on `lo`) must still match the UR driver: see the execution guide |
| `scripts/run_campaign.py` | 5 s countdown; shuffled schedule (seed 42); "validity" = ≥ 50 rows and attack flag seen; invalid trials re-appended and the queue **reshuffled**; after every trial: 2 s, dashboard `unlock protective stop`, 2 s, `play`, 3 s (the first `recv` returns the dashboard banner, so the printed "response" was not the command's reply) | plan saved with seed and hash; no automatic reruns or reshuffles; every attempt kept; faults → HOLD with operator decision; `unlock protective stop` never automatic; `play` only when configured (`dashboard_play`) or by the operator |
| `src/.../joint_logger_node.py` | serial read loop calls `reset_input_buffer()`; zero velocities when feedback > 0.1 s old; attack flag before the injection thread; ATTACK at 20 Hz under a lock; CLOUD mode runs `sudo iptables` | replaced by `DeviceLink` + `Recorder` + `RobotMonitor` |
| `src/.../stream_wrist_kinematics.py` | two-phase trajectory; attack service called 0.5 s after the phase-2 goal is **sent**; `os._exit(0)` after 60 s | poses, normalization and timing reused in `onedge_v8/motion.py`; injection only after motion is confirmed; no forced exits |
| `scripts/run_end_to_end_campaign.py` | local mock cloud; buffered serial reader (no per-read flush); hard-coded 125/247 ms prediction columns | not used; its buffered-read pattern informed the V8 framer |

## V8 trial and reset sequence (robot procedure)

1. **Between trials** the runner waits in `AWAITING_CONFIRMATION`. The dashboard shows the next trial and a
   checklist (work area clear; E-stop within reach; robot state reviewed). Nothing moves until the operator
   confirms.
2. **Preconditions**: joint telemetry fresh; safety mode not a fault (protective stop, E-stop, violation,
   fault → `fault_robot`, resolve at the pendant).
3. **Re-arm**: configuration command → device acknowledges (trust 100, cycle 0, D12 commanded high). The
   latched safeguard stop from the previous trial is expected here and only here.
4. Safety mode must return to NORMAL within 5 s, otherwise `failed_setup` ("a safeguard reset may be
   required").
5. Program running: the operator presses **Play** on the pendant (default), or the runner sends `play` when
   `resume_program` is `dashboard_play`. Timeout → `failed_setup`. Then, as the historical wrapper did after
   Play, the runner re-activates `passthrough_trajectory_controller` (switch_controller, BEST_EFFORT;
   `switch_controller_each_trial`) and checks it is active (`list_controllers`); failure → `failed_setup`.
6. Approach, settle (standstill criterion), sweep, **confirm moving**, delay, inject, observe, wait for the
   trajectory result. A safeguard stop before the firmware reports D12 low, a protective stop, or a trajectory
   abort without D12 low → `fault_robot` → HOLD.
7. The runner never sends `unlock protective stop`. The dashboard offers it as an operator command with a
   recorded reason, disabled during attempts.

Abort at any point: trajectory cancel request, no ATTACK/RECOVER, no reconfiguration. The monitor state is
left as it is (if ATTACK was active, trust keeps falling and D12 goes low: the stop direction).
