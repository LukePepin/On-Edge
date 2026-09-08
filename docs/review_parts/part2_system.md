# Part II — The system as built

Everything in this part is present in the repository at the commit audited on 2026-09-07
(HEAD fd2eba4, then cleaned up on 2026-09-08). Line numbers refer to the files as they stand
after the cleanup; the audit notes in `audit/` carry the pre-cleanup references.

---

## 10. Topology and every communication path

### 10.1 The five boxes

1. **Mock cloud identity provider.** A small Python server. In the robot campaigns it is a
   TCP server on a laptop that streams `AUTH_OK`; in the bench block it is an HTTP health
   endpoint on the Pi itself. It exists to be severed. Nothing about it is measured.
2. **Supervisor: Raspberry Pi 4.** Runs ROS 2, the UR driver, the joint logger, the
   kinematics node, and the campaign orchestrator. Talks to the robot over Ethernet, to the
   edge node over USB serial, and to the mock cloud over Wi-Fi or loopback.
3. **Edge node: Arduino Nano 33 BLE.** Runs the trust-monitor firmware. Talks only over USB
   serial to the supervisor, and drives one output pin.
4. **Optocoupler block.** Converts the pin's 3.3 V logic to the 24 V PNP signal the UR5
   expects, on both safeguard channels in parallel.
5. **UR5 with its CB controller.** Executes trajectories from the supervisor, reports joint
   states, and stops when its safeguard inputs open.

The Draft 1 figure (`figures/system_flow.mmd` in the thesis repository) draws these with
every arrow labelled. The important structural fact is that there are **two independent
paths from the supervisor to the robot**: the ROS 2 path (trajectory goals, dashboard
commands, joint-state feedback) and the trust path (serial to the edge node, then the pin,
then the safety input). The experiment measures the trust path's latency using timestamps
recorded on the ROS 2 path.

### 10.2 The serial protocol

Both directions are newline-terminated text at 115,200 baud.

Supervisor → edge node:
- `{"algo": "ECC"|"ZKP"|"CLOUD", "alpha": <float>}` — configure. Resets Γ to 100, resets the
  cycle counter, clears the attack flag, raises the safety pin, replies `{"status": "READY"}`.
  Sent at boot (the firmware blocks until it gets one) and at the start of every trial.
- `ATTACK` — set the attack flag. Sent at 20 Hz for the duration of the nominal outage.
- `RECOVER` — clear the attack flag without touching Γ. Added 2026-08-11.

Edge node → supervisor, once per cycle:
- `{"cycle": <int>, "exec_time_ms": <float>, "trust_score": <float>}`

Nothing else crosses the link. In particular, no joint data, no hashes, no credentials and
no proofs go to the edge node; the "vault and broker" data flow in older architecture
documents was never implemented.

### 10.3 The ROS 2 path

- `ur_robot_driver` ↔ UR5 controller: RTDE over Ethernet, plus the reverse interface for
  trajectory passthrough. The URCap "external control" program must be running on the
  pendant for the driver to command motion; a safeguard stop pauses it.
- Kinematics node → driver: one `FollowJointTrajectory` action goal per phase to
  `/passthrough_trajectory_controller`.
- Driver → joint logger: `/joint_states` and `/io_and_status_controller/ur_imu`.
- Kinematics node → joint logger: the `/inject_attack` service (a `std_srvs/Trigger`).
- Orchestrator → UR5 dashboard server (TCP port 29999): `unlock protective stop` and `play`
  between trials.

### 10.4 Timing sources

Three clocks appear in the data. The **edge node's DWT counter** measures workload cost.
The **supervisor's PC clock** timestamps every logger row and every bench event. The
**UR controller's clock** is never used directly; joint states are stamped on arrival by the
logger's 50 Hz timer. All eviction latencies in the robot campaigns are differences of
supervisor timestamps; all loop periods are differences of supervisor timestamps in the
bench block. No cross-clock subtraction is ever performed, which is one reason the numbers
are clean.

---

## 11. The trust-monitor firmware, line by line

File: `firmware/unified_trust_monitor_template/unified_trust_monitor_template.ino`, 268 lines.

### 11.1 Globals (lines 11–46)

`current_algo`, `ewma_alpha` (default 0.3, always overwritten by configuration),
`EVICTION_THRESHOLD = 30.0`, `trust_score = 100.0`, `cycle_count`, `attack_mode_active`.
DWT register macros. `#define uECC_CURVE uECC_secp256r1` before including micro-ecc. A
`rand()`-based RNG handed to micro-ecc (weak entropy, noted in the early audit reports, and
irrelevant to timing). Two booleans selecting the workload. `SAFETY_PIN = 12`.

### 11.2 setup() (lines 48–105)

Serial at 115,200; pin 12 output, driven HIGH immediately ("start in active state to
prevent reset jitter"); DWT enabled; wait for the USB serial connection; then **block**
until a JSON line with both `algo` and `alpha` arrives. On success: set the workload flags,
reply READY, drive pin 12 HIGH again. The firmware therefore never runs a workload until the
supervisor has configured it, and the safety loop is closed from power-up.

### 11.3 execute_ecc_verification() (lines 111–153)

Zero the cycle counter, call `uECC_make_key`, read the counter, convert to ms. Then:

```
if (attack_mode_active) current_trust = 0.0;
else if (exec_time_ms > 150.0) current_trust = max(0, 100 - (exec_time_ms - 150));
else current_trust = 100.0;
trust_score = alpha*current_trust + (1-alpha)*trust_score;
if (trust_score < 30.0) digitalWrite(SAFETY_PIN, LOW);
print JSON; cycle_count++; delay(10);
```

Note what is absent: no `digitalWrite(SAFETY_PIN, HIGH)` anywhere in this function. Once
the pin goes LOW it stays LOW until a configuration message.

### 11.4 execute_zkp_verification() (lines 155–210)

Identical structure. The workload (lines 162–176):

```
static uint8_t attributes[64]; static bool payload_init = false;
if (!payload_init) { RNG(attributes, 64); attributes[0] |= 1; attributes[32] |= 1; payload_init = true; }
volatile int acc = 0;
acc += uECC_compute_public_key(&attributes[0],  public_key); acc += public_key[0];
acc += uECC_compute_public_key(&attributes[32], public_key); acc += public_key[0];
```

Two scalar multiplications on a buffer generated once. The `|= 1` forces the low bit so the
scalars are odd (nonzero). The volatile accumulator stops the optimizer from deleting the
calls. The penalty threshold here is 400 ms. The comment above the block reads "Real ZKP
proxy", and the thesis keeps that honesty.

### 11.5 loop() (lines 215–268)

Character-at-a-time serial drain into `input_buffer` (capped at 200 characters). On
newline: `ATTACK` sets the flag; `RECOVER` clears it; a JSON object with `algo` and `alpha`
performs the full reset described in 10.2 and raises the pin. Then one workload call
depending on the flags. A `CLOUD` configuration sets neither flag, so the loop does nothing
but drain serial; that mode was used in the abandoned three-algorithm matrix and in the
Aug-10 swapover demo.

### 11.6 Properties that follow

- Command latency: up to one loop period, uniformly distributed, because commands are read
  only at the top of the loop.
- Latching: no path re-raises the pin except reconfiguration.
- The exec-time penalty never fires in practice (workloads at ~60 % of thresholds).
- Under `ATTACK`, `exec_time_ms` continues to be measured and printed but has no effect on
  trust; the workload's only role during an attack is to consume one loop period.
- Single pin: the "dual-channel synchronized GPIO" described in older documents does not
  exist in this file. The dual-channel behaviour is entirely in the wiring.

### 11.7 History that matters

- 2026-08-05: unified template created; ZKP stub set to 3× keygen "to fit under 400 ms".
- 2026-08-06: attack made non-blocking (trust forced to 0 instead of extra keygen loops).
- 2026-08-11 18:43: `RECOVER` added. This is the commit that made outage duration a real
  factor. V6 ran that evening.
- 2026-08-12 11:46: ZKP stub replaced by the two-multiplication proxy; comments changed from
  "Category 0" to "Category 2". V7 ran two minutes later. Luke confirms no uncommitted edits
  were flashed (2026-09-07).

---

## 12. The supervisor: joint logger, kinematics node, orchestrator

### 12.1 joint_logger_node.py (320 lines)

Parameters: `algo`, `outage` (ms), `iteration`, `alpha`, `timestamp` (Unix seconds, passed
in by the shell script so the CSV and the packet capture share a name).

Startup: open `/dev/ttyACM0` (or `ttyACM1`), send the configuration JSON repeatedly for up
to 6 s until READY comes back, else abort the trial. Then start a serial-reader thread and a
CSV-writer thread, subscribe to joint states and IMU, create the `/inject_attack` service,
and start a 50 Hz timer.

The 50 Hz timer (`log_timer_callback`) writes one row: PC time (seconds and nanoseconds),
the latest trust score received, six joint positions, six joint velocities (forced to zero
if no joint-state message has arrived in the last 100 ms, on the assumption that a paused
URCap means standstill), raw and EMA-filtered IMU acceleration, and the attack flag.

The attack sequence (`_execute_attack_sequence`): for the nominal outage duration, write
`ATTACK\n` every 50 ms; then write `RECOVER\n` and clear the flag. For the `CLOUD` algorithm
it instead inserts and removes an iptables rule on port 8080; that branch was not used in
V5–V7.

The serial reader (`serial_read_loop`, lines 148–161) is the source of the dropped-line
defect: it calls `reset_input_buffer()`, sleeps 10 ms, and does one non-blocking
`readline()`. A line that straddles the flush or the read boundary is discarded (a partial
line fails the `{...}` check). Chapter 21 quantifies the effect. The design intent was to
always read the freshest line; the side effect was losing 10–20 % of lines.

### 12.2 stream_wrist_kinematics.py (267 lines)

Phase 1: send a single-waypoint goal that moves the arm to the Pick pose over 5 s. Wait for
the result, then poll joint states until the arm is at standstill (joint position change
below 2 mrad between messages).

Phase 2: send a five-waypoint goal: Pick at 1 s, Transfer at 3 s, Place at 5 s, Transfer at
7 s, Pick at 10 s. Waypoints are normalized to the shortest angular path from the current
pose to avoid full-turn unwinds. Velocities are left unspecified so the UR controller uses
cubic interpolation. Immediately after sending, a thread sleeps 0.5 s and then calls
`/inject_attack`. The same thread sleeps a further 60 s and then hard-exits the process so
the shell script is never blocked by a paused robot.

The consequence for the results: since the first waypoint is the pose the arm is already
in, at 1 s, commanded motion effectively begins between 0.5 and 1.0 s after the attack.
Fast evictions land before the arm moves.

### 12.3 run_test.sh (139 lines)

Argument parsing (`--algo`, `--outage`, `--iter`, `--alpha`); checks `ulimit -l` is
unlimited (for `mlockall`); clears leftover iptables rules; kills zombie loggers; starts
`tshark` on the wireless interface writing to `/tmp`; starts the joint logger under
`taskset 0x7` and `chrt -f 99`; sleeps 6 s for the handshake, prints a 4 s warning for the
operator to press Play; switches the UR controller to passthrough; runs the kinematics node
under the same real-time settings and waits for it; sleeps 3 s; kills everything; moves the
pcap into `data/`. The CSV name is built as
`trial_<ALGO>_outage<OUTAGE>_ewma<alpha*10>_iter<ITER>_<timestamp>.csv`.

### 12.4 run_campaign.py (192 lines)

Builds the factorial list, shuffles with `random.seed(42)`, optionally takes one half
(`--half 1|2`), and loops: run `run_test.sh`, validate the CSV (at least 50 rows and the
attack flag seen), append to `data/sub_eviction_summary.csv` if valid, else re-queue the
trial with an incremented attempt counter and reshuffle the remainder. After every trial,
`recover_robot()`: 2 s pause, dashboard `unlock protective stop`, 2 s, dashboard `play`, 3 s.

The validation rule changed on 2026-08-11. Before that a trial was rejected unless it
*stopped*; with a working outage factor that would have re-queued every legitimate
non-stop trial forever. The rule now checks only that the trial ran.

### 12.5 What the supervisor does not do

It does not hash telemetry, does not send anything to the edge node except configuration
and attack/recover keywords, does not verify anything cryptographic in the robot campaigns,
and does not participate in the safety path except by telling the edge node when the
network is "down". The supervisor's `supervisor_node.py` (an auth-request service with the
Pi-side `uECC_verify` timing wrapper) belongs to the July service-rate work and is not part
of any V5–V7 trial.

---

## 13. The safety intercept

### 13.1 The circuit

Arduino D12 (3.3 V logic) → optocoupler block input → 24 V PNP output → UR5 SI0 and SI1 in
parallel (Luke, 2026-09-07). The block is active-high: logic high closes the safeguard loop.
Loss of power or connection on the Arduino side therefore opens the loop, which is the
fail-safe direction.

### 13.2 What the UR5 does when the loop opens

Safeguard stop: controlled deceleration, hold position, program paused, pendant shows the
safeguard-stop state. Category 2. Drive power remains. When the loop closes again the
program can be resumed with Play (or auto-resume if configured). Between trials the
orchestrator issues `unlock protective stop` and `play` via the dashboard; `unlock
protective stop` is harmless if no protective stop is present and covers the case where a
trajectory fault occurred.

### 13.3 What the firmware does when the loop should close again

Nothing, until the next configuration message. The score may recover to 100 after
`RECOVER`, but the pin stays low. This is by construction, and the thesis should describe it
as a latched Category 2 stop with reset by reconfiguration, not as an auto-resuming stop and
not as a Category 0 stop.

### 13.4 The C192A4 disagreement fault

Observed during integration. With one pin feeding both channels, any skew between channels
on restoration is a property of the optocoupler pair and wiring. The fault forces a
pendant-level reset. It is worth a paragraph in the thesis as an observed integration
hazard; it is not a designed security feature.

### 13.5 What is not in the loop

No emergency-stop input, no reduced-mode input, no power relay. Nothing the firmware does can
remove drive power. If a committee member asks "what if the arm must be de-energized", the
answer is that this design does not do that and a Category 0 path would need the EI0/EI1
inputs or a relay on the drive supply, both of which are future work.

---

## 14. The bench harness and the sentry node

### 14.1 run_end_to_end_campaign.py (196 lines)

Runs on the Pi with only the trust monitor attached. Starts a local HTTP server on
127.0.0.1:8081 whose `/health` returns 200 while `cloud_is_up` is true and hangs for 2 s
otherwise. For each trial (probe interval 100 or 500 ms; workload ECC or proxy; α = 0.5;
five iterations): configure the edge node; for 3 s, probe at the interval; then set
`cloud_is_up = false` and record `t_jam`; probe immediately and on each failure (the first
one, in practice) record `t_detection` and send `ATTACK`; read the serial stream by
accumulating all bytes and splitting on newlines (no drops); record `t_first_decay` at the
first trust value below 100 and `t_eviction` at the first value ≤ 30; then send `RECOVER`.

Because all four timestamps are `time.time()` on the same host, the differences are direct.
The script also computes a "predicted_total" from hard-coded cycle times of 125 and 247 ms;
that column is untraced and is not used.

### 14.2 sentry_node.ino (93 lines)

A state machine on a second Arduino with no cryptography. States: CLOUD, ZKP_BOOTSTRAP,
ECC_STEADY. Inputs from the host: `CONFIG:K,DWELL`, `CLOUD_UP`, `CLOUD_DOWN`,
`BOOTSTRAP_COMPLETE`, `REJOIN_CONFIRMED`, `REJOIN_FAILED`. Outputs: transition messages and
`INITIATE_REJOIN`. The rejoin request is emitted only when K consecutive `CLOUD_UP` events
have been received and at least DWELL_MS have elapsed since the first of them; any
`CLOUD_DOWN` resets both. The state becomes CLOUD only on `REJOIN_CONFIRMED`. This replaced
(2026-08-11) an earlier version that rejoined on a fixed 15 s timer regardless of
connectivity.

### 14.3 run_cloud_failover_sweep.py (287 lines)

Host side of the sentry test. Serves a mock cloud on 127.0.0.1:8080 with three failure
patterns (hang; alternate 500 ms up/down; respond slowly), probes it at the configured
interval requiring HTTP 200 and a JSON `status: ok`, forwards `CLOUD_UP`/`CLOUD_DOWN` to the
sentry, simulates the crypto node's bootstrap by sending `BOOTSTRAP_COMPLETE` 1.5 s after
the sentry enters ZKP_BOOTSTRAP, and on `INITIATE_REJOIN` re-probes the cloud before
answering `REJOIN_CONFIRMED` or `REJOIN_FAILED`. Records detection latency, recovery
latency, "unmonitored motion" (probe count × interval while in CLOUD with the cloud down),
false rejoins, and excess oscillations.

Limits: everything is on one host with a loopback cloud; one run per configuration; the
archived results file predates a serial-parsing fix and its probe = 1000 ms rows are
unusable. The sweep never involved the robot or the trust monitor.

---

## 15. What was proposed but never built

A defense goes badly when the candidate is surprised by a gap the committee already found.
This list is the set of things earlier project documents describe as existing that do not
exist in the repository.

| Described in earlier documents | Status in the built system |
|---|---|
| ZKP selective-disclosure verification on the edge node | Not built. Two scalar multiplications on a static buffer. |
| 64-byte "independent constraints" payload with CLT stabilization | Not built. One loop, deterministic cost, sd 0.2 ms. The profiler file cited for it never existed. |
| Hashed telemetry streamed to the edge node ("vault and broker") | Not built. Nothing but keywords and configuration crosses the serial link. |
| Kinematic trajectory hashes unlocked by verification | Not built. |
| Nine Arduino worker nodes in a star | One trust monitor (plus one sentry on the bench). |
| Dual-channel synchronized GPIO with < 20 ms skew | One pin; channels paralleled in wiring. |
| Category 0 / STO stop | Category 2 safeguard stop. |
| Hold-down suspension of EWMA decay during legitimate crypto work | Not built. Trust is forced to 0 whenever ATTACK is asserted. |
| Token-bucket admission control | Not built. |
| 368 ms URScript mode-switch penalty measurement | No data or script in the repository. |
| 99.6 % boot-storm shedding from QoS change | No measurement in the repository. |
| IMU + Extended Kalman Filter deceleration proof | Not built. IMU is logged raw and EMA-filtered; never analysed. |
| Ledger/SQLite work-order reconciliation on rejoin | Not built. |
| NS-3 extrapolation to n* | Simulations exist in history, built on the withdrawn 3.10 packets/s figure. Not usable. |

Each of these can be presented as future work or as a design intent that was descoped when
the hardware sprint ran out of time. None of them can be presented as done.

---

*End of Part II.*
