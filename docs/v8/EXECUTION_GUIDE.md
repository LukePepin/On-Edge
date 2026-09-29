# V8 execution guide: dashboard, campaigns, demonstration

For whoever runs the On-Edge timing experiment (Luke or a future lab member). Written 2026-09-28 before any
hardware run: items marked **VERIFY** have not been checked on the lab hardware. What is and is not tested:
[VERIFICATION.md](VERIFICATION.md). Open approvals: [PENDING_APPROVALS.md](PENDING_APPROVALS.md).

---

## One-page run card

| Step | Where | Command / action |
| --- | --- | --- |
| 1 | Lab | Safety review done; E-stop reachable; cell clear (section 0) |
| 2 | Pi (SSH) | `cd ~/Documents/On-Edge && bash v8/scripts/pi_preflight.sh` |
| 3 | Pi, robot only | start the UR driver (section 6.2, **VERIFY** exact command) |
| 4 | Pi (tmux) | bench: `python3 v8/scripts/daemon.py --config v8/config/daemon/pi_bench.json`  robot: `... pi_robot.json` |
| 5 | Lunchbox | `powershell -ExecutionPolicy Bypass -File v8\scripts\start_dashboard.ps1` → browser opens |
| 6 | Dashboard | badge `LIVE · HARDWARE`, Monitor `fresh`, firmware `trust_monitor_v8 8.0.0 (<build>)`, Recording ok |
| 7 | Dashboard → Campaigns | pick campaign → review matrix → tick boxes → Start |
| 8 | Dashboard → Live | watch; Pause between trials; HOLD → decide with a reason; robot: confirm each trial |
| 9 | Dashboard → Replay | "Copy closed sessions from the Pi" → open attempts → summaries / exclusions |
| 10 | Shutdown | Ctrl+C the daemon (finalizes the active attempt as aborted); close the dashboard window |

---

## 0. Scope and safety — read first

* This software runs a **timing experiment**. The failure is injected with ATTACK commands; it is not a
  detection of real network loss. The "ZKP" workload is two elliptic-curve scalar multiplications (a cost
  proxy), not proof verification.
* **The dashboard and the daemon are not safety devices.** "Abort campaign" stops the software sequence
  (cancels the trajectory goal, sends no further commands, does not reconfigure the monitor). It is **not an
  emergency stop** and does not confirm the robot has stopped. The teach-pendant emergency stop is the safety
  device.
* Displayed states are observations: "D12 commanded LOW" is a firmware report, not a measured voltage;
  "below still threshold" is a telemetry reading, not a certified standstill; missing telemetry is shown as
  unknown.
* Lab safety requirements — **confirm each with the lab supervisor before any robot motion (VERIFY)**:
  1. Who is authorised to operate the UR5, and who must be present.
  2. The UR5 safety configuration in use (safeguard stop inputs, reset behaviour, stopping limits, speed).
  3. The documented interface: one Nano D12 output through an optocoupler to SI0 **and** SI1 in parallel
     (historical documentation). One signal feeding both channels is not an independently redundant safety
     design; the lab decides whether it may be used and how.
  4. Robot program: External Control URCap; local/remote control mode; who presses Play.
  5. The motion envelope of the pick-place sweep (poses in `v8/onedge_v8/motion.py`, taken unchanged from
     the historical kinematics node) is clear of people and objects.
  6. Oscilloscope use (if any): probe point, grounding, instrument compatibility.
  7. The monitor drives D12 HIGH at boot before any configuration (inherited firmware behaviour): unplugging
     or resetting the Nano re-closes the safeguard loop.
* Physical tests, flashing, and live commands each need Luke's explicit approval (PENDING_APPROVALS B1–B9).

## 1. Roles and connections

```
Lunchbox (Windows) ──SSH tunnel──► Pi (Ubuntu + ROS 2) ──USB──► Nano 33 BLE (trust_monitor_v8)
                                   │                               │ D12 → optocoupler → UR5 SI0/SI1 (VERIFY)
                                   └──Ethernet── UR5 controller (ur_robot_driver; dashboard server :29999)
```

| Machine | Role | Software |
| --- | --- | --- |
| Windows lunchbox | dashboard, replay, operator controls | Python ≥ 3.10, OpenSSH client, browser |
| Raspberry Pi (`on-edge-pi`, user `seeker`) | acquisition daemon: serial owner, campaign runner, recorder, ROS client | Ubuntu 22.04, ROS 2 Humble, `python3-serial` (**VERIFY**) |
| Arduino Nano 33 BLE | trust monitor: workload, EWMA, D12 | `firmware/trust_monitor_v8` |
| UR5 | robot, safeguard stop | External Control URCap; IP 192.168.0.149 historically (**VERIFY** at URI) |

No extra Python packages are needed on either computer (standard library + pyserial on the Pi; rclpy from
ROS for robot mode).

## 2. One-time setup

### 2.1 SSH key from the lunchbox to the Pi (run in **Git Bash on the lunchbox**, not on the Pi)

```bash
ssh-keygen -t ed25519 -f ~/.ssh/id_ed25519 -C "lunchbox-to-on-edge-pi"
```
```bash
cat ~/.ssh/id_ed25519.pub | ssh seeker@on-edge-pi.local "mkdir -p ~/.ssh && chmod 700 ~/.ssh && cat >> ~/.ssh/authorized_keys && chmod 600 ~/.ssh/authorized_keys"
```
Check: `ssh -o BatchMode=yes seeker@on-edge-pi.local hostname` prints `on-edge-pi` without a password prompt.
At URI the Pi may have another address: use `-PiHost <address>` with the start script.

### 2.2 Code on the Pi

The Pi's checkout is `~/Documents/On-Edge`. The V8 files (`v8/`, `firmware/trust_monitor_v8/`, `docs/v8/`)
must be committed and pulled, or copied. Keep the Pi and lunchbox on the same commit: every session records
the git commit, the dirty-file list and SHA-256 of the source files.

### 2.3 Software self-test (safe: simulated transport only)

Pi: `python3 -m unittest discover -s v8/tests` (from the repo root; firmware host tests are skipped if g++
or ArduinoJson headers are absent). Lunchbox: `python -m unittest discover -s v8/tests` and
`node --test v8/tests/js/modes.test.mjs`.

### 2.4 Firmware

Flash `firmware/trust_monitor_v8` with the Arduino IDE on the machine that has the historical libraries —
[FIRMWARE_V8.md](FIRMWARE_V8.md). Close the Serial Monitor afterwards.

## 3. Rehearse without hardware (any PC)

`powershell -ExecutionPolicy Bypass -File v8\scripts\start_sim_demo.ps1` starts a **simulated** daemon and
the dashboard. The badge reads `LIVE · SIMULATED`; data go to `data/v8_sim/` and are labelled simulated in
replay. Campaigns `sim-smoke` (bench) and `sim-robot-demo` (robot workflow with a simulated arm) exercise
every screen. Nothing here is evidence about the hardware.

## 4. Preflight on the Pi

```bash
cd ~/Documents/On-Edge && bash v8/scripts/pi_preflight.sh
```
Read-only. Check: pyserial present; serial access (the Pi's `ttyACM*` nodes are mode 666, so `dialout`
membership is not required there); the `/dev/serial/by-id/*Arduino*` devices; **no process holding the port**
and no historical logger/kinematics/campaign process running; disk space; for robot mode the UR topics are listed.

Exactly one Nano should be attached: the trust monitor, `usb-Arduino_Nano_33_BLE_4BF58E3CC72BBA71-if00`
(2026-09-28). If several match, `"serial": {"port": "auto"}` refuses to pick one and reports all of them.
Unplug the others, or set `serial.port` to the monitor's full `/dev/serial/by-id/...` path. Don't use
`ttyACMn`, because those numbers can swap on replug.

## 5. Bench session (Pi + Nano, no robot motion)

1. Pi, in `tmux` (so a dropped SSH session does not stop acquisition):
   ```bash
   cd ~/Documents/On-Edge
   python3 v8/scripts/daemon.py --config v8/config/daemon/pi_bench.json
   ```
   Expect: `[onedge_v8] HARDWARE daemon on http://127.0.0.1:8765 data -> .../data/v8`.
2. Lunchbox: `powershell -ExecutionPolicy Bypass -File v8\scripts\start_dashboard.ps1`.
3. Dashboard header: `LIVE · HARDWARE`; Monitor `fresh`; Joints `unavailable` (expected on the bench);
   Recording ok. Quality panel: firmware identity and build string; protocol `v8`; missing 0; malformed 0.
4. Campaigns tab → `v8-demo-bench` (demonstration) or the approved bench pilot → Start.

### 5.1 Lab network at URI (switch: lunchbox + Pi + UR5)

At URI the lunchbox, the Pi and the UR5 controller plug into one Ethernet switch (Luke, 2026-09-28). The lab
subnet is 192.168.0.x (UR5 historically 192.168.0.149). Whether the switch has a DHCP server is **VERIFY**, so
the Pi keeps DHCP first and falls back to a static address. One-time setup on the Pi (Luke runs, needs sudo;
the home DHCP profile keeps working):

```bash
sudo nmcli con modify "Wired connection 1" connection.autoconnect-priority 10 connection.autoconnect-retries 2 ipv4.dhcp-timeout 20
```
```bash
sudo nmcli con add type ethernet ifname eth0 con-name UR5-direct ipv4.method manual ipv4.addresses 192.168.0.210/24 ipv6.method link-local connection.autoconnect yes connection.autoconnect-priority 0
```
Check: `nmcli -f NAME,AUTOCONNECT,AUTOCONNECT-PRIORITY con show`. Expected behaviour (not yet tested): with
DHCP the Pi takes a lab address as before; without DHCP, the wired profile fails after about 1 minute and
`UR5-direct` gives 192.168.0.210. To force it: `sudo nmcli con up UR5-direct`; to go back:
`sudo nmcli con up "Wired connection 1"`. If the Pi cannot be reached, use a keyboard and monitor on the Pi.

At the lab:
1. Teach pendant: note the controller IP (Settings → System → Network) and model (CB3 or e-Series), and the
   External Control URCap **Host IP** (Installation → URCaps → External Control). The Host IP must be the Pi's
   address (192.168.0.210, or the DHCP address shown by `ip -brief addr` on the Pi); change the pendant or
   the `UR5-direct` address so they match, and avoid addresses already used in the lab.
2. Lunchbox: if it gets no 192.168.0.x address automatically, set Ethernet to manual IPv4 192.168.0.20,
   mask 255.255.255.0, no gateway (Windows Settings → Network → Ethernet → IP assignment).
3. From the lunchbox: `ssh -o BatchMode=yes seeker@192.168.0.210 hostname` (or `on-edge-pi.local`), then
   start the dashboard with `-PiHost 192.168.0.210`.
4. From the Pi: `ping -c 3 <UR5 IP>`; set `ur_host` in `v8/config/daemon/pi_robot.json` if it is not
   192.168.0.149.

## 6. Robot session

### 6.1 Before starting anything
Section 0 confirmed; robot powered, brakes released per lab procedure; External Control program loaded; the
cell is clear.

### 6.2 UR driver (Pi terminal 1) — VERIFY against the lab's working setup
The historical wrapper used ROS 2 Humble with `ROS_LOCALHOST_ONLY=1` and `sudo ip link set dev lo multicast
on`, and `cyclonedds_pi4.xml` exists in the repo. Start the driver exactly as the lab normally does (e.g.
`ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5 robot_ip:=<UR5 IP> ...`) and note the command
in the session notes. The daemon must use the **same** ROS environment variables (domain, localhost-only,
RMW).

### 6.3 Daemon (Pi terminal 2, tmux)
```bash
source /opt/ros/humble/setup.bash        # plus the driver workspace setup if messages come from there
export ROS_LOCALHOST_ONLY=1              # only if the driver uses it (VERIFY)
cd ~/Documents/On-Edge
python3 v8/scripts/daemon.py --config v8/config/daemon/pi_robot.json
```
Check `v8/config/daemon/pi_robot.json` first: `ur_host`, topic names, controller name (**VERIFY** with
`ros2 topic list` / `ros2 control list_controllers`).

### 6.4 Dashboard checks
Robot card: interface `ros`; Motion `BELOW STILL THRESHOLD (fresh telemetry…)` at rest; safety mode
`NORMAL`; program `running` or `not running`. The Joints indicator must be `fresh`. If safety mode or
program state says "unavailable", those topics or message packages are missing (see troubleshooting).

### 6.5 Each robot trial
The runner stops at **AWAITING_CONFIRMATION** before every trial. Tick the three checks and press
**Start T0xx**. The runner then re-arms the monitor (configuration raises D12), waits for safety mode NORMAL,
waits for the program to run (press **Play** on the pendant when "waiting_for_program" appears), re-activates
the passthrough controller, approaches Pick, settles, sweeps, confirms motion, injects, and waits for the
trajectory to end. If the arm is not confirmed moving, no ATTACK is sent and the attempt is recorded as
`failed_precondition`.

## 7. Choosing and starting a campaign

Campaigns tab → a campaign shows kind (RESEARCH / DEMONSTRATION / SOFTWARE_TEST), status (proposed /
approved), the full condition table with purposes and MODEL expectations, the complete trial order with
per-trial injection jitter, estimated duration, plan hash, and warnings. Start requires the operator name,
"I reviewed the full matrix", and for robot procedures "Robot motion is authorized". The plan hash must match
what you previewed; if the file changed, preview again.

| Campaign | Use |
| --- | --- |
| `v8-bench-pilot` | research, bench, 150 trials (**approved** 2026-09-28) |
| `v8-robot-pilot` | research, robot, 15 trials (**approved** 2026-09-28) |
| `v8-demo-bench`, `v8-demo-robot` | demonstration presets, 4 trials, labelled as demonstration |
| `sim-smoke`, `sim-robot-demo` | software tests with the simulator |

Editing a campaign: change the JSON and bump `config_version`. Reusing a version with different content is
refused once data exist.

## 8. During a campaign

* **Header badge:** LIVE · HARDWARE / LIVE · SIMULATED / DISCONNECTED / REPLAY. Indicators: Pi daemon,
  Monitor freshness (age of the last record), Joints, Recording, Operator heartbeat.
* **Campaign card:** state, progress (completed / skipped / planned / attempts), current attempt (trial,
  attempt number, workload, α, failure, repetition, phase), last attempt outcome.
* **Plots:** trust (step line at host receipt time, threshold 30, shaded device attack mode, host command
  markers, D12 command markers, red ticks for sequence gaps / invalid records); workload execution time
  (orange) and device-clock loop period (blue); joint speed envelope with hatched **NO FRESH DATA** where
  telemetry is missing; the event timeline keeps host command, device processing, trust < 30, D12 command,
  electrical D12 (not measured), controller report and motion in separate lanes.
* **Narration panel:** plain-language description of the current phase; MODEL statements are labelled.
* **Current attempt:** live device-clock and host-clock intervals (display estimates; final values are in
  `summary.json`).
* **Controls:** *Pause after this trial* (current attempt completes normally); *Resume*; *Abort campaign…*
  (reason required; not an E-stop); **HOLD** panel with the reason and the allowed decisions — *retry* (new
  attempt of the same trial; the failed attempt is kept), *skip* (trial marked skipped), *continue* (only after
  a completed attempt with warnings), *abort*. Every decision needs a reason and is recorded.
* **Manual ATTACK / RECOVER / configuration:** always recorded and flagged as departures; during an attempt a
  second confirmation is required and the attempt is flagged `operator_commands_during_attempt`.
* **Operator note:** timestamped note in the session log (use it for scope captures, observations, IDE
  versions).
* **Dashboard disconnect:** acquisition continues; the current attempt finishes; the next trial does not start
  until a dashboard heartbeat returns (campaign shows PAUSED "operator connection lost"). Resume manually.

## 9. Demonstration script (narration)

Use `v8-demo-robot` (or `v8-demo-bench` as the fallback). Pause between trials to explain.

1. **Normal operation (ECC, α 0.3, no failure).** "The monitor runs the key-generation workload each cycle
   (~112 ms) and updates trust with a normal observation of 100, so trust stays at 100. The loop period is
   measured on the Nano's own clock." Point at the loop-period dots and the missing-records counter (0).
2. **Brief failure (ECC, α 0.3, 250 ms).** "ATTACK is processed at the next loop boundary — the timeline
   shows the host sending it and the Nano processing it, two different events. Each attacked update
   multiplies trust by 0.7. Four are needed to fall below 30, but the failure ends first, so trust dips and
   recovers; D12 stays high; the robot keeps moving." MODEL note in the narration panel.
3. **Sustained failure (ECC, α 0.5, 3000 ms).** "Two attacked updates cross 30. The firmware reports the
   below-threshold update and the D12-low command a few microseconds later. The controller then reports a
   safeguard stop (host receipt time). Standstill is judged afterwards from fresh telemetry with the declared
   criterion; the electrical edge itself is not measured by this software." After RECOVER: "trust recovers,
   but D12 stays low until the next configuration."
4. **Slow configuration (ZKP proxy, α 0.1, 3000 ms).** "Twelve updates of a ~225 ms workload: the same
   algorithm, much later decision."
5. **Replay.** Replay tab → the demo session → open attempt 3 → scrub the timeline; compare attempts 3 and 4
   (trust vs device time since ATTACK processed).

What the demo does **not** show: a detected network outage, proof verification, a validated safety function,
or a guaranteed stopping time.

## 10. Expected behaviour (reference, not results)

* Records: one `upd` per cycle (≈ 8 /s ECC, ≈ 4 /s ZKP proxy); missing 0, malformed 0 (except a possibly
  partial first line after connect).
* Historical summaries for orientation: ECC keygen ≈ 111.5 ms, two multiplications ≈ 224.9 ms (DWT profiles);
  host-observed report intervals ≈ 120.4 / 232.1 ms. A V8 device loop period far from these → investigate
  before collecting.
* Attacked updates to cross (from 100): 12 (α 0.1), 4 (α 0.3), 2 (α 0.5). The summary's `model_check` should
  agree; a disagreement means a penalty observation, a missed ATTACK, or a firmware difference.
* `device_cross_to_out_low` a few microseconds (same cycle).
* After RECOVER the device reports `attack=0` and trust rising; D12 remains commanded low.

## 11. After a session

1. Replay tab → **Copy closed sessions from the Pi**: copies only closed sessions, verifies SHA-256, never
   overwrites (conflicts are listed). Hardware sessions go to `data/v8/`, simulated to `data/v8_sim/`.
2. Open attempts: the summary shows events, intervals (with clocks and ranges), outcome, quality warnings,
   and what is not measured.
3. Exclusions: select an attempt → scope → *Exclude…* with a reason; *Restore…* later. Counts of included /
   excluded appear above the table; "show excluded" toggles them. Raw files are untouched.
4. Recompute a summary offline: `python -m onedge_v8.analysis data/v8/sessions/<sid>/attempts/<aid>` (from
   `v8/`).
5. Commit the session directories (data are small: tens of MB per campaign) — Luke's decision.

## 12. Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Badge DISCONNECTED | tunnel down or daemon stopped | check the Pi tmux window; rerun the start script; acquisition on the Pi is unaffected |
| Start script: "port 8765 already listening" | a local simulated daemon or old tunnel | close it, retry |
| Tunnel fails | key login not set up / wrong host | `ssh -o BatchMode=yes seeker@<host> hostname`; use `-PiHost` |
| Monitor `unavailable`, "already open by PID" | Serial Monitor, old logger, second daemon | stop that process (the daemon never kills it) |
| Protocol `legacy` | template firmware still on the Nano | flash V8, or accept degraded legacy mode (no device times) |
| Missing records > 0 | USB problems, host overload | campaign HOLDs for review; check cable/hub; keep or retry (both kept) |
| Device resets > 0 | Nano rebooted (power, brown-out, re-plug) | attempt `failed_acquisition`; D12 went HIGH at boot; review before continuing |
| `configuration not acknowledged` | wrong firmware, busy port, Nano in bootloader | check the quality panel's firmware line; replug; retry |
| Joints `missing`/`stale` in robot mode | driver not running, ROS environment mismatch, QoS | compare `ros2 topic hz /joint_states`; set `joint_qos` to `best_effort` if the publisher is best-effort |
| Safety mode "unavailable" | `ur_dashboard_msgs` not importable | source the driver workspace before the daemon |
| `failed_setup: safety mode did not return to NORMAL` | safeguard reset input configured | reset at the pendant, then retry |
| `waiting_for_program` never ends | program paused | press Play; or set `resume_program: dashboard_play` (approved) |
| `failed_precondition: arm not confirmed moving` | trajectory not started / telemetry gaps | inspect the joint plot; no injection was sent |
| `fault_robot: PROTECTIVE_STOP` | robot fault | resolve at the pendant; *unlock protective stop…* only by decision |
| Recorder ERROR | disk full / write error | stop; free space; the HOLD prevents further trials |

## 13. Reset and shutdown

* End of campaign: the session closes itself (manifest written). A running campaign: *Abort campaign…*.
* Daemon: Ctrl+C in its tmux window. An active attempt is aborted and finalized; the session is closed as
  ABORTED. If the process is killed instead, restart it: interrupted attempts are marked automatically.
* Dashboard: close the PowerShell window (stops the tunnel too).
* Robot: follow the lab's procedure (program stop, E-stop / power down as required). The daemon does not
  power anything down.
* Nano: unplugging it opens the safeguard loop (D12 unpowered); plugging it back in drives D12 HIGH at boot.

## 14. Verified vs. not verified

Software-tested: parsing, continuity, clocks, telemetry criteria, campaign validation and ordering, recorder
durability and recovery, exclusions, runner state machine with a simulated monitor and robot, dashboard mode
gating, sync, firmware logic equivalence on a host emulation. **Not yet verified:** anything on the Pi, the
Nano, the UR5 or the lab network. See [VERIFICATION.md](VERIFICATION.md) and
[PENDING_APPROVALS.md](PENDING_APPROVALS.md).
