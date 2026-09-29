# V8 dashboard: purpose, what works, difficulties

Status as of 2026-09-29 (URI integration day), `onedge_v8` 0.1.3, firmware `trust_monitor_v8 8.0.0`
(build `Sep 28 2026 21:51:04`). Written for Luke and a future lab member. Step-by-step operation is in
[EXECUTION_GUIDE.md](EXECUTION_GUIDE.md); open approvals are in [PENDING_APPROVALS.md](PENDING_APPROVALS.md).

## 1. Purpose

The dashboard is the operator console for the On-Edge **timing experiment**. It asks one question:
when the supervisor's trust signal fails, how long does the Nano trust monitor take to decide (trust below 30),
command D12 LOW, and bring the UR5 to a Category 2 safeguard stop? The dashboard does four jobs:

1. **Run campaigns**: preview a campaign's full matrix and trial order, start it, and confirm each robot trial.
2. **Show the live system**: trust score, workload timing, joint speed, D12 command, robot safety mode, and
   acquisition quality, each labelled with its clock and freshness.
3. **Record honestly**: every record, command and operator action is written on the Pi. Missing telemetry is
   shown as missing, and the dashboard never makes up a value.
4. **Explain**: the "What is happening" narration and the **Mermaid sequence chart** tab show the whole model.

It is **not a safety device**. "Abort campaign" stops the software sequence only. The teach-pendant E-stop is
the safety device.

## 2. How it fits together

```
Lunchbox browser --SSH tunnel :8765--> Pi daemon (runner, recorder, ROS client) --USB--> Nano (trust monitor)
                                           |                                           | D12 -> optocoupler -> SI0/SI1
                                           +-- UR ROS 2 driver (localhost-only) --Ethernet--> UR5 CB3 (192.168.0.149)
```

* The **Pi daemon** (`v8/scripts/daemon.py`) owns the serial port, runs campaigns, writes the dataset under
  `data/v8/`, and serves the dashboard at `http://127.0.0.1:8765` (reached from the lunchbox by an SSH tunnel).
* The **lunchbox dashboard server** (`v8/dashboard/server.py`, started by `start_dashboard.ps1`) adds
  verified copying of closed sessions from the Pi, replay of local copies, and reversible exclusions.
* A **simulated** mode (`start_sim_demo.ps1`) exercises every screen without hardware. It is labelled
  `LIVE · SIMULATED` and writes to `data/v8_sim/`.

## 3. The tabs

| Tab | What it shows / does |
|---|---|
| **Live** | Campaign state and progress; campaign controls (pause after trial, resume, abort); **Start T00x** per robot trial; manual ATTACK / RECOVER / configuration (recorded as departures); robot card (interface, motion state, safety mode, program, D12 command, read-only dashboard queries, play / unlock with a recorded reason); operator notes; plots of trust, workload execution time and device loop period, and joint speed (fresh samples only); event timeline; narration; live attempt estimate; acquisition quality (firmware identity, protocol, records, missing, malformed, resets, disconnects, recorder, disk) |
| **Replay & compare** | Recorded sessions and attempts, the same plots from recorded files, the attempt summary (intervals with their clock), comparison of attempts aligned at device-side ATTACK processing, manual exclusions with history |
| **Campaigns** | Campaign configurations on the Pi: kind (research / demonstration / software test), approval status, conditions with MODEL expectations, full trial order with seeded jitter, estimated duration, plan hash; start requires "I reviewed the full matrix" and, for robot procedures, "Robot motion is authorized… cell is prepared" |
| **Mermaid sequence chart** | One robot trial end to end: operator, dashboard, daemon, Nano, optocoupler, UR driver, UR5, with the three outcomes (sustained failure, brief failure, control). The source is `v8/dashboard/static/model_sequence.mmd` (download / copy for the thesis). Mermaid loads from cdn.jsdelivr.net, and the source text is shown if it cannot load |

Header indicators: mode badge (`LIVE · HARDWARE` / `SIMULATED`), Pi daemon, monitor freshness, joint freshness,
recording, operator presence.

## 4. What works (verified on hardware)

**Bench (Pi + Nano), 2026-09-28**
* Smoke run `v8-demo-bench` (4/4) and the approved **bench pilot, 150/150 trials** (about 18 min): 0 missing and
  0 malformed records, no warnings, no penalty updates.
* Every crossing agreed with the model: **2 / 4 / 12** zero-observation updates for α 0.5 / 0.3 / 0.1 (70/70).
  All 5 repetitions of each condition had the same outcome, and ATTACK→crossing varied by at most ±3 ms per condition.
* Crossing → D12-low command ≈ 10 µs (same cycle). D12 stays LOW after RECOVER until the next configuration.
* Data committed to git (`data/v8/`, SHA-256 verified, line-ending conversion disabled).

**Robot (URI, UR5 CB3, PolyScope 3.15.8), 2026-09-29**
* Wiring check (arm stationary): D12 LOW → controller `SAFEGUARD_STOP`, D12 HIGH → `NORMAL`, no disagreement
  fault (C192A4) on restore.
* UR driver 2.13.0 with `ROS_LOCALHOST_ONLY=1`: `/joint_states` 125 Hz, safety mode and program state received,
  passthrough controller switched per trial, External Control connected at Host IP 192.168.0.242.
* Robot demo `v8-demo-robot`, session `20260929T191850Z`, T001–T003 (T004 was pending when this was written):
  * T001 control and T002 brief failure: full sweeps, no stop, as expected.
  * **T003 sustained failure (ECC α 0.5):** motion confirmed before injection; crossing after 2 updates,
    ATTACK→crossing 233.1 ms (device clock, rate-corrected); **D12-low → safeguard-stop report 20.2 ms**;
    telemetry standstill 527 ms after the D12-low command; paused sweep cancelled; attempt `completed`.
    One demonstration trial, not a campaign result.
  * The first robot session (`20260929T182849Z`) gave 16–21 ms in its two stop trials, with the same caveat.

## 5. Difficulties found and how they were resolved

| # | Difficulty | Effect | Resolution |
|---|---|---|---|
| 1 | Nano `micros()` (and CPU) ≈ **0.72 % fast** vs the Pi; the rate wanders by a few hundred ppm | Device↔host alignment wrong (ATTACK "processed before sent") | Software correction, firmware unchanged: fit up to 20,000 ppm (0.1.1), use session records within ±60 s for short attempts (0.1.2), rate-corrected device intervals |
| 2 | `delay(10)` is not exactly 10 ms on the device (9.8 / 10.5 ms) | "loop − exec − 10 ms" is not a valid overhead estimate | Use the measured update-to-next-workload gap; overhead interpretation (B3) still open |
| 3 | Lab network carries **other ROS 2 systems on domain 0** | Topics could mix with other robots' `joint_states` | `ROS_LOCALHOST_ONLY=1` for driver and daemon (checked isolated) |
| 4 | Safety mode / program topics are **latched, on change only** | Daemon showed "no report yet" at start | TRANSIENT_LOCAL subscriptions |
| 5 | **Trial confirmation ticks reset** by status updates | Operator could not start T001 | Card re-rendered only when changed; per-trial checkboxes later removed (session acknowledgement + Start click remain) |
| 6 | **Safeguard stop pauses, not ends, the sweep** on the UR5 | Runner waited for the sweep result → timeout `fault_robot`; next approach "rejected"; the **leftover sweep resumed** when the next configuration closed the loop | 0.1.3: after D12 LOW, wait for standstill, then **cancel the goal while D12 is still LOW**; never re-arm while a goal is active; simulator now models the pause. Verified on hardware (T003 above) |
| 7 | Operator reasons required everywhere | Slowed the operator | Optional (recorded as "(no reason given)"); exclusion reasons stay required |
| 8 | Model tab squeezed into a 320 px column on wide screens | Unreadable chart | One full-width column |
| 9 | SSH tunnel dropped during the demo | Runner **paused** (no operator heartbeat), as designed | Restart the tunnel; the dashboard reconnects; press Resume |
| 10 | UR driver: calibration mismatch error | Cartesian accuracy only; joint-space trajectories unaffected | Accepted; extracting the robot calibration is optional |
| 11 | No `tmux` on the Pi | Daemon must survive SSH drops | `setsid nohup` with logs in `~/v8_logs/`; start script `~/v8_logs/start_robot_daemon.sh` |

## 6. Limitations and open items

* **Not safety-rated.** One D12 line feeds SI0 and SI1 in parallel through the optocoupler, which is not an
  independently redundant design. Lab safety review is required for every robot session.
* **Goals from an earlier daemon run are invisible** to the runner. After a robot fault or a daemon restart,
  **Stop** (not Pause) External Control on the pendant, then press Play.
* The **electrical D12 edge is not measured** (the oscilloscope is for setup validation only). Controller safeguard
  reports are host-receipt times, and standstill is a declared telemetry criterion, not a certified stop.
* Robot results so far are **demonstration trials**. The approved robot pilot (15 trials) has not been run.
* Instrumentation overhead (B3) is measured but not yet interpreted against the historical V6/V7 numbers.
* Replay, sync and exclusions on the lunchbox server were tested in software only, and not yet on today's
  hardware sessions.
* The Mermaid tab needs internet on the lunchbox to render. Offline it shows the source text.

## 7. Quick start (robot session)

1. Pendant: External Control installed, Host IP = Pi eth0 (192.168.0.242 today), program loaded; cell clear.
2. Pi, driver: `source /opt/ros/humble/setup.bash && export ROS_LOCALHOST_ONLY=1 && ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5 robot_ip:=192.168.0.149 launch_rviz:=false`
3. Pi, daemon: `~/v8_logs/start_robot_daemon.sh`
4. Lunchbox: `ssh -N -L 8765:127.0.0.1:8765 seeker@on-edge-pi.local`, then open `http://127.0.0.1:8765/`.
5. Pendant: Play. Dashboard: Campaigns → pick the campaign → acknowledge → Start. Then **Start T00x** for each trial.
