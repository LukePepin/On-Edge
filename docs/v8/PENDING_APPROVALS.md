# Pending approvals and unverified behaviour (V8)

Updated 2026-09-28. Everything built so far is **software-tested only** (unit tests, simulated transport,
host-compiled firmware logic, an ARM compile of the firmware). Nothing here has run on the Nano or the UR5.

## A. Decisions for Luke

| # | Decision | Where |
| --- | --- | --- |
| A1 | Approve/modify the V8 bench and robot pilot matrices | **approved as proposed by Luke 2026-09-28** (bench 150, robot 15; configs `status: approved`), see [V8_MATRIX_PROPOSAL.md](V8_MATRIX_PROPOSAL.md) |
| A2 | Firmware build machine | **resolved 2026-09-28**: the lunchbox. `uECC.h` (pre-1.0 API) comes from the Arduino mbed_nano 4.6.0 core (Cordio BLE stack), not from a separate library; ArduinoJson 7.4.3. See [FIRMWARE_V8.md](FIRMWARE_V8.md) |
| A3 | Program resume policy: operator presses Play | **approved by Luke 2026-09-28** (default `trial.motion.resume_program`) |
| A4 | Standstill / moving criteria (0.01 rad/s · 250 ms · 40 ms gap; 0.05 rad/s · 100 ms) | **approved by Luke 2026-09-28** |
| A5 | Whether to add an oscilloscope measurement of D12 on 9/30 and how to align it | **decided by Luke 2026-09-28**: the oscilloscope is used only to validate the setup (D12 levels/edges, optocoupler → SI0/SI1), not during test trials; no scope data enter the dataset, so the electrical D12 edge stays unmeasured in trial data |
| A6 | Commit/push the new code | **approved by Luke 2026-09-28**; the Pi gets it by `git pull` |
| A7 | D12 driven HIGH at boot; one D12 line → optocoupler → SI0/SI1 | **accepted by Luke 2026-09-28** (safety review item) |
| A8 | Device clock runs ≈ 0.72 % fast vs the Pi (found in B2, below): correct in software (session-level rate fit) or start the nRF52840 crystal (HFXO) in firmware | **open** |

## B. Hardware actions that need your explicit approval each time

| # | Action | Notes |
| --- | --- | --- |
| B1 | Flash `firmware/trust_monitor_v8` with the Arduino IDE | **done 2026-09-28** by Luke on the lunchbox from `c2e135e`: build `Sep 28 2026 21:51:04`, mbed_nano 4.6.0, ArduinoJson 7.4.3 (IDE version not yet recorded); hello records correct, D12 HIGH at boot |
| B2 | Bench smoke run (Pi + Nano): `v8-demo-bench` or a 1-repetition cut of the bench pilot | **done 2026-09-28** (approved by Luke), session `20260929T015656Z_v8-demo-bench_v1` on the Pi, no robot: 4/4 completed, 0 missing / 0 malformed, model check agreed (2 updates ECC α 0.5, 12 ZKP α 0.1), cross→D12-low ≈ 10 µs, D12 held LOW after RECOVER; found the device clock rate issue (A8) |
| B3 | Bench overhead check: compare device loop period with the historical summaries | same hardware as B2 |
| B4 | Bench pilot (150 trials) | after A1 |
| B5 | Start the daemon with the ROS robot interface (passive subscriptions) | first contact with the live driver |
| B6 | Robot dry run: 1–2 trials of `v8-demo-robot` with the operator at the pendant | robot motion |
| B7 | Robot pilot (15 trials) and demonstration | robot motion; after A1 and lab safety review |
| B8 | Any dashboard `play` / `unlock protective stop` command | recorded; never automatic |
| B9 | Any oscilloscope probing of D12 / optocoupler | lab safety review |

## C. Behaviour not yet verified on hardware

Pi / software environment. Read-only inspection over key-based SSH on 2026-09-28 found: Ubuntu 22.04.5,
aarch64, Python 3.10.12, pyserial 3.5, `/opt/ros/humble` present, NTP synchronized, no historical
launcher running, 29 GB free. The Pi's repository had an untracked `src/edge_node/`. A second Nano was attached
at first; Luke unplugged it, and the only board now is the trust monitor,
`usb-Arduino_Nano_33_BLE_4BF58E3CC72BBA71-if00` → ttyACM0. With `"port": "auto"` the daemon refuses to guess
if several boards are attached again. Still open:
* `seeker` is not in `dialout`; this works today only because the tty nodes are mode 666.
* `rclpy`, `control_msgs`, `ur_dashboard_msgs`, `controller_manager_msgs` importable in the daemon's
  environment; the UR driver launch command and ROS environment (domain, `ROS_LOCALHOST_ONLY`, CycloneDDS
  config `cyclonedds_pi4.xml`) — the historical wrapper set `ROS_LOCALHOST_ONLY=1`.
* `RosRobot` (joint_states, safety mode, program-running topic, FollowJointTrajectory on
  `passthrough_trajectory_controller`, `list_controllers`) has **never executed**. Topic names and message
  packages follow ur_robot_driver for ROS 2 Humble and must be checked with `ros2 topic list`.
* Actual `/joint_states` rate, QoS, joint name order (the historical CSVs indicate the driver's order starts
  with shoulder_lift), and whether telemetry continues during a safeguard stop.
* UR controller model and dashboard-server command set (CB3 vs e-series) and controller IP at URI
  (historical 192.168.0.149): Luke to check at URI on 9/29. Lunchbox↔Pi SSH at URI.
* Driver launch: plain `ros2 launch ur_robot_driver ur_control.launch.py` (Luke, 2026-09-28); `ur_type`,
  `robot_ip` and any other arguments still to be confirmed.

Firmware on the Nano:
* Compiles for `arduino:mbed_nano:nano33ble` with the core-bundled uECC (102,264 B flash, 44,952 B RAM,
  2026-09-28); workload times on the real board not yet checked against history.
* Real USB CDC timing of one-record-per-cycle writes (`pw_us`), loop period vs history. First look (B2, one session):
  `pw_us` median ≈ 355–373 µs; device-clock loop period median 121.9 ms (ECC) / 234.6 ms (ZKP), exec 112.2 /
  224.1 ms. Rate-corrected (÷ 1.0072) ≈ 121.0 / 232.9 ms vs historical host-observed 120.4 / 232.1 ms.
  A full B3 comparison is still open.
* Boot/hello behaviour on real connect/disconnect; record formatting on real floats.
* Inherited behaviour, accepted by Luke on 2026-09-28: the firmware drives D12 HIGH at boot, before any
  configuration or trust evaluation (unchanged from the template). A reset of the Nano therefore re-closes
  the safeguard loop.

Measurement:
* Clock fit on real USB latency; the assumed minimum-latency bound (2 ms) for cross-clock ranges.
  **B2 finding:** the Nano's `micros()` runs ≈ 7,200 ppm fast relative to the Pi's monotonic clock
  (47 s session: min-delay envelope slope 992.84 host ns per device µs, envelope residuals < 0.7 ms; every
  attempt independently estimated 992.7–993.0). The per-attempt fit rejects slopes beyond 1,000 ppm and falls
  back to nominal, so the **aligned host↔device intervals in the B2 summaries are wrong** (e.g. ATTACK
  "processed" 19.5 ms before it was sent). Device-clock intervals are internally consistent but scaled by
  ≈ +0.72 %. Likely cause (not verified): the Mbed core leaves the nRF52840 on its internal RC oscillator
  (HFINT) rather than the 32 MHz crystal. See A8.
* Host scheduling jitter on the Pi without real-time priority (device-clock intervals do not depend on it).
* Standstill/moving criteria on real telemetry noise.

Robot and safety interface:
* D12 → optocoupler → SI0/SI1 wiring as documented historically; safeguard stop and reset behaviour;
  program pause/resume after a safeguard stop; whether a safeguard reset input is configured.
* None of this software is a safety function. The campaign abort is not an emergency stop.
