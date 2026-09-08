# Part III — The experiments

This part is the evidence. Each chapter names the files the numbers come from and the
script that recomputes them. If a number here is not in `ground_truth_v2.md`, this part is
wrong and that file is right.

---

## 16. Campaign history V1–V7: what changed each time and why

The project ran seven campaigns in eight days (2026-08-05 to 08-12). Only the last three are
usable for the thesis, and it is important to be able to say precisely why the first four
are not.

| Campaign | Date | Factor varied | Firmware state | Verdict |
|---|---|---|---|---|
| V1 | Aug 5 evening | random packet loss 25/50/75 % via iptables; ECC vs stub; α .1/.3/.5; n=3 | stub ZKP; attack latched | Probabilistic loss never reached the firmware as a factor; superseded the same night. |
| V2 | Aug 5–6 night | "deterministic outage" 500–5000 ms; resolution-IV 12-config design; n=12 | same | First use of ATTACK keyword flooding. No RECOVER, so every trial latched. 19 trials failed to fire and were not re-run. |
| V3 | Aug 6 afternoon | full 2×4×3 (α .5/.7/.9) | same, blocking attack loops | 20 failed trials not re-run. |
| V4 | Aug 6 evening | same matrix, randomized queue, re-run on failure | non-blocking attack (trust forced to 0) | Complete 120-cell matrix, but attack latched: every trial evicts regardless of outage. The "H1' null result" came from here. |
| V5 | Aug 7 | α changed to .1/.3/.5, outage 500–5000, n=5 | same | Complete, clean, latched. Kept as the latched-attack baseline. |
| V6 | Aug 11 evening | ECC only; outage 250–2000; n=10 | **RECOVER added 18:43** | First campaign in which outage duration is a real factor. |
| V7 | Aug 12 | proxy only; outage 250–5000; n=5 | **proxy replaces stub 11:46** | First campaign with the measured ZKP-cost workload. |

Three things to be able to say in a defense:

- Why α changed from {.5,.7,.9} to {.1,.3,.5}: the high values all evict in one or two
  cycles and give no resolution; the low set spans 2 to 12 cycles.
- Why the outage set changed between V6 and V7: the threshold n(α)·T_cycle is about twice
  as long for the proxy, so the levels were shifted up to bracket it (250/500/1000 below,
  3000/5000 above, 1000 near the α = 0.3 boundary).
- Why V6 and V7 were never run together: time. The UR5 was available for a few more hours.
  The consequence, that ECC versus proxy is a between-campaign comparison, has to be stated.

The "latched attack" defect deserves its own sentence. Before Aug 11 the firmware had
exactly one attack command and no way to clear it except a full reconfiguration. The
supervisor's logger did stop sending ATTACK after the nominal duration, but the flag on the
device stayed set, so the score decayed to eviction in every single trial. The logger's own
`attack_active` column shows the same thing from the other side: in V5 it stays at 1 for
about 63 s, the length of the trial, regardless of the nominal 500–5000 ms. So the earlier
finding "outage duration has no effect" was a statement about a factor that was never
delivered. It was withdrawn and replaced by the V6/V7 threshold result.

---

## 17. Measurement definitions and the audit scripts

Every quantity in Parts III and IV is one of the following. The scripts live in `audit/`.

| Quantity | Definition | Script |
|---|---|---|
| Verification cost | DWT cycles ÷ 64,000 per workload call | `zkp_profile_stats.py` |
| Loop period T_cycle | host time between trust 50 and trust 25 at α = 0.5 (bench) | inline in `phase2_zkp.md` |
| Trial validity | ≥ 50 logger rows and `attack_active`=1 observed | `inventory_trials.py` |
| Eviction latency (logged) | first row with trust ≤ 30 after attack − first row with attack flag | `eviction_latency.py` |
| First-decay latency | first row with trust < 100 after attack − attack flag | same |
| Step sequence | distinct successive trust values during decay | same |
| Physical stop | joint speeds < 0.02 rad/s from before t_attack + 8.5 s through + 9.5 s | `physical_stop_crosstab.py` |
| Capture ratio | expected decay values 100(1−α)^k actually present in the log | `telemetry_capture.py` |
| Crossing missed | first logged value ≤ 30 is not the first expected value ≤ 30 | same |

Two definitions need justification.

**Why physical stop is defined by motion.** The trajectory commands continuous motion from
about half a second after the attack until about nine and a half seconds after it. An arm
that sits still for that entire window did not execute its program, and the only mechanism
in the cell that prevents program execution is the safeguard input. The definition is
therefore a direct observation of the safety action, independent of the trust telemetry.
It cannot be fooled by a dropped serial line. It can be fooled only by a trial in which the
program was not running at all, which the orchestrator's Play command and the presence of
phase-1 motion rule out (phase-1 motion is visible in every valid file).

**Why 0.02 rad/s.** The controller's idle jitter on a stationary UR5 is below 0.01 rad/s in
these logs; 0.02 gives margin without admitting slow real motion (the slowest commanded
segment exceeds 0.1 rad/s).

---

## 18. Verification cost results

File: `data/real_zkp_profiling.csv`, 300 rows. Columns: cycle, start_cycles, end_cycles,
total_cycles, exec_time_ms, res1, res2, keybyte.

| Statistic | Value |
|---|---|
| n | 300 |
| mean | 224.864 ms |
| standard deviation | 0.209 ms |
| minimum | 224.083 ms |
| median | 224.867 ms |
| 95th percentile | 225.183 ms |
| maximum | 225.391 ms |
| coefficient of variation | 0.093 % |
| Shapiro–Wilk | W = 0.995, p = 0.44 |
| first 50 vs last 50 mean | 224.87 vs 224.81 ms |

All 300 rows have `res1 = res2 = 1` (both scalars valid) and `exec_time_ms` equals
`total_cycles / 64000` exactly, confirming the conversion is a host constant. The start
counter reads 4 in every row: the counter is zeroed and then read, and the read itself
costs four cycles.

ECC keygen: from the Aug 10 swapover log's 1640 ECC cycles, mean 111.54 ms, sd 0.09,
range 111.24–111.87. Ratio proxy/ECC = 2.016, which is what two scalar multiplications
against one should give (keygen also draws randomness; the difference is inside the noise).

What this establishes, exactly: the cost of two fixed-base secp256r1 scalar multiplications
in micro-ecc on this device, with no accelerator, at the assumed 64 MHz. What it does not
establish: the cost of any complete verification, the cost of variable-base multiplication
(the same routine in micro-ecc, so probably similar, but not measured), or the behaviour
under interrupt load (the audit reports from July asked for a loaded measurement; none was
done).

Provenance: the file was written on the Windows PC at 18:39 on Aug 11 and committed four
minutes later. Luke recalls also running the profiler on the Pi; no file from that run
survives, and a repeat on the Pi is scheduled.

---

## 19. Loop period and the structure of eviction

File: `data/v7_logs/e2e_composition_results.csv`, 20 rows, one host clock.

### 19.1 The period

At α = 0.5 the trust sequence under attack is 100 → 50 → 25, so the interval from the
first decayed line (50) to the eviction line (25) is one complete loop iteration: workload,
serial print, 10 ms delay, serial read.

| Workload | mean | sd | min | max | n |
|---|---|---|---|---|---|
| ECC | 120.4 ms | 4.8 | 113.2 | 123.7 | 10 |
| proxy | 232.1 ms | 5.4 | 225.7 | 236.4 | 10 |

The sd of about 5 ms is host-side: the script polls the serial port every 10 ms, so each
timestamp carries up to 10 ms of quantization. The device-side period is more stable than
this.

### 19.2 Detection to first decay

| Workload | mean | range |
|---|---|---|
| ECC | 177 ms | 125–228 |
| proxy | 309 ms | 258–443 |

This interval is one full period plus a partial one: the ATTACK arrives at a random point
in the running cycle, waits for that cycle to finish (the partial term, uniform on [0, T]),
and then the next full cycle runs with the attack in effect and emits the first decayed
value. The ranges are consistent with T + U(0, T) plus serial latency.

### 19.3 The eviction structure

Putting the two together, from detection to eviction is a partial cycle plus n(α) full
cycles, so

    T_evict ≈ n(α)·T_cycle + U(0, T_cycle) + t_serial

with mean (n(α) + ½)·T_cycle. At α = 0.5: predicted mean 2.5 × 120.4 = 301 ms for ECC and
2.5 × 232.1 = 580 ms for the proxy; measured 262/333 ms (ECC, probe 100/500) and 533/549
ms (proxy). The measured values sit somewhat below the (n + ½) prediction, which suggests
the effective partial term is a little shorter than a full uniform cycle (the serial read
in the firmware happens right after the delay, so an ATTACK sent during the delay is
picked up sooner). This is a second-order effect and the model is presented as an
approximation.

### 19.4 What the bench block does not show

Its detection column equals one probe timeout because the script probes at the instant it
kills the cloud. Under natural probe phase the detection window would be uniform between
one and two probe intervals. The identity "detection + eviction = total" holds because the
columns are defined that way. And the script's "predicted_total" column is built on an
untraced 247 ms and must be ignored.

---

## 20. Eviction latency on the robot and the outage threshold

Files: `data/v6_logs/trial_*.csv` (120 valid), V7 trial files (75 valid). Per-trial outputs
in `audit/eviction_v6.csv` and `audit/eviction_v7.csv`.

### 20.1 Tables

The Draft 1 tables (Chapter 4 of the thesis) are the reference. Condensed:

**ECC (V6), n = 10 per cell.** Stops (physical): α = 0.1 only at 2000 ms; α = 0.3 at 500
ms and above; α = 0.5 at 250 ms and above. Latencies where eviction occurred: 1572 ms
(α = 0.1), 609–660 ms (α = 0.3), 324–391 ms (α = 0.5), with within-cell ranges of about one
loop period.

**Proxy (V7), n = 5 per cell.** Stops: α = 0.1 at 3000 and 5000; α = 0.3 at 1000 and above;
α = 0.5 at 500 and above. Latencies: 2995–3030 ms (α = 0.1), 1077–1122 ms (α = 0.3),
552–659 ms (α = 0.5).

### 20.2 Against the model

Predicted means (n + ½)·T:

| α | ECC predicted | ECC measured (pooled) | proxy predicted | proxy measured (pooled) |
|---|---|---|---|---|
| 0.1 | 12.5 × 120.4 = 1505 | 1572 | 12.5 × 232.1 = 2901 | 3013 |
| 0.3 | 4.5 × 120.4 = 542 | 629 | 4.5 × 232.1 = 1044 | 1109 |
| 0.5 | 2.5 × 120.4 = 301 | 363 | 2.5 × 232.1 = 580 | 624 |

Measured exceeds predicted by 40–90 ms in every row. Two contributions: the logger samples
at 50 Hz (up to 20 ms late), and the logger drops lines so that in 10–20 % of trials the
recorded crossing is a full cycle late (Chapter 21). A crude correction, adding 0.15 × T to
the prediction, brings every row within about 30 ms. The model has no fitted parameter; the
agreement is in ordering, spacing, and magnitude.

### 20.3 The threshold

The cleanest result in the project. With outage as a real factor, each cell is all-stop or
all-no-stop, and the boundary sits where n(α)·T_cycle predicts:

- ECC, α = 0.5: 2 × 120 = 240 ms. 250 ms stops (10/10), and there is no shorter level.
- ECC, α = 0.3: 4 × 120 = 480 ms. 250 no, 500 yes.
- ECC, α = 0.1: 12 × 120 = 1444 ms. 1000 no, 2000 yes.
- Proxy, α = 0.5: 2 × 232 = 464 ms. 250 no, 500 yes.
- Proxy, α = 0.3: 4 × 232 = 928 ms. 500 no, 1000 yes.
- Proxy, α = 0.1: 12 × 232 = 2785 ms. 1000 no, 3000 yes.

Twenty-seven cells, zero exceptions, once stop is judged by motion. Above the threshold the
latency is independent of outage duration, as it must be: the outage only needs to last
long enough to deliver n(α) attacked cycles.

One subtlety about the ECC 250 ms / α = 0.5 cell. The threshold is 240 ms and the logger
records the attack flag as lasting about 272 ms, so the margin is one-eighth of a cycle.
The device sees ATTACK at cycle boundaries, so whether two attacked cycles occur depends on
where in the cycle the attack starts. All ten trials stopped. Either the margin was enough
in every trial or the 20 Hz ATTACK repeats plus RECOVER timing extend the effective
attack slightly; the data cannot distinguish these, and the thesis should describe this
cell as "at threshold, stopped in all ten" without claiming more.

---

## 21. Physical stop, the stationary-arm finding, and the dropped-line defect

### 21.1 Logged versus physical

Across V5, V6 and V7 (315 valid trials):

- Trials logged as stopped (trust ≤ 30 in the CSV) whose arm nevertheless completed its
  trajectory: **0**.
- Trials whose arm never executed the trajectory but which show no trust ≤ 30 in the CSV:
  **8** (V6: six in the 250 ms / α = 0.5 cell, one in 500 ms / α = 0.3; V7: one in
  1000 ms / α = 0.3).

The eight are all boundary cells, where the crossing happens on the last attacked cycle
and a single missing serial line hides it. So the logged stop count under-reports, never
over-reports. Earlier internal reports treated the 4/10 and 4/5 boundary cells as evidence
of "cycle-boundary jitter deciding marginal cases"; they were instrumentation.

### 21.2 The dropped-line defect, quantified

Because the firmware's under-attack sequence is exactly 100(1−α)^k, the audit can check
which expected values appear. Restricting to the first n(α)+2 decay steps (the tail rounds
to zero and would inflate the count):

| Campaign | mean capture | worst trial | crossing line missed / logged stops |
|---|---|---|---|
| V7 | 0.83–0.86 | 0.50 | 5 / 44 |
| V6 | 0.78–0.81 | 0.50 | 16 / 73 |
| V5 | 0.79–0.92 | 0.50 | 26 / 120 |
| V4 | 0.80–0.91 | 0.50 | (same mechanism) |

Mechanism: the logger's reader flushes the input, sleeps 10 ms, and reads one line
non-blocking; anything that straddles the boundaries is lost. The visible signatures are
skipped steps (50 then 12.5), first-decay values that are impossible (75 at α = 0.5, which
is the first *recovery* step after a dropped 50), and a one-cycle spread in every latency
cell. The bench harness, which accumulates all bytes, has none of these.

### 21.3 The stationary-arm finding

The trajectory's first waypoint is the arm's current pose at t = 1 s, and the attack is
called at t = 0.5 s. Motion starts between 0.5 and 1.0 s after the attack. Evictions faster
than that open the safeguard input before the arm has moved. From the velocity columns:

| Condition | stops | arm moving at eviction |
|---|---|---|
| ECC α = 0.5 (V5, V6) | 54 | 0 |
| ECC α = 0.3 (V5, V6) | 49 | only the V6 2000 ms cell (10), at 0.06 rad/s |
| ECC α = 0.1 | 30 | all, 0.3–0.4 rad/s |
| proxy α = 0.5 (V7) | 20 | 2 of 20, slow |
| proxy α = 0.3 (V7) | 14 | 0 |
| proxy α = 0.1 (V7) | 10 | all, ~0.57 rad/s |
| stub α = 0.5 / 0.3 (V5) | 40 | all |

Therefore: **every stop that landed under 500 ms happened with a stationary arm.** What
those trials show is that the trajectory was never executed, which is a valid observation
of the safety action, but it is not a demonstration of arresting a moving arm inside the
budget. Stops of a moving arm exist only at α = 0.1 and in the withdrawn-stub cells, all
above 1.5 s. The thesis says this in one sentence in the results and again in the
limitations. A future campaign that wants the missing evidence fires the attack two to four
seconds into phase 2.

### 21.4 What is not measured about the stop

The mechanical deceleration phase after the input opens, the safety controller's reaction
time, and the exact moment the input opened (the logged trust crossing is a proxy, up to
one cycle late). The IMU columns exist but were never analysed; an Extended Kalman Filter
mentioned in old outlines was never written.

---

## 22. The failover sweep

File: `data/cloud_failover_sweep_results.csv`, 108 rows, one per configuration.

Usable rows: the 81 at probe intervals 100, 250 and 500 ms. The 27 rows at 1000 ms were
produced before a serial-parsing fix and record detection or recovery as zero in almost all
cases.

Observations (single runs, loopback mock cloud, no robot, no crypto node):

- Detection latency is about 3.1–3.4 probe intervals for clean-drop and degraded patterns
  and up to 6.3 intervals under flapping, and does not depend on K (the state machine
  detects on the first CLOUD_DOWN; K gates only the rejoin).
- Recovery latency is approximately dwell + 1–2 s.
- No excess oscillation in any usable row; one false rejoin in the corrupt block.
- "Unmonitored motion" equals probe interval × number of failed probes before the
  transition; it is an accounting quantity, not motion.

Grade: demo. The sweep can be re-run without the robot (one Arduino plus the script) and
should be, with n ≥ 3 per configuration, before anything from it goes into a results
chapter.

---

## 23. Results that were withdrawn, and the exact reason for each

| Withdrawn statement | Reason | Where it came from |
|---|---|---|
| ZKP costs 334.66 ms | Stub of 3× keygen, calibrated to sit under 400 ms (commit message of Aug 5) | Aug 10 swapover log |
| 22.85 % security tax | Computed from the stub | proposal-era profiling |
| 301–346 ms "64-byte stabilization" and the central-limit-theorem argument | No 64-constraint code exists; the profiler file cited never existed; measured sd is 0.2 ms | never in repo |
| "ZKP is incompatible with industrial safety" as a measured finding | Based on the stub; with the proxy it is a model statement | V4/V5 prose |
| ECC halts in 236–439 ms at α = 0.5/0.7/0.9 | Those α were V4; V5 measured 291–505 ms at 0.5 | `empirical_conclusions.md` (deleted) |
| Outage duration has no effect (H1' null) | Attack latched; factor never delivered | V4 |
| Category 0 / STO / "latching cryptographic halt" | SI0/SI1 is Category 2; C192A4 is a timing fault | multiple |
| Cohen's d = 2.4 proves n = 4 suffices | Observed-power fallacy | `final_lab_plan.md` (deleted) |
| 500 ms is an ISO 13849-1 limit | The standard sets no stop time | multiple |
| 247 ms proxy loop period | Untraced; measured 232 ms | `conclusion2.md`, e2e script constant |
| "Composition confirmed to 0.0 ms" | Arithmetic identity of the columns | `conclusion2.md` |
| 4/5 partial boundary cell; "unexplained 75 first step" | Dropped-line defect | `conclusion2.md` |
| 335 physical trials | Counts 20 Arduino-only bench runs | `conclusion2.md`, `project_truth.md` |
| K ≥ 3 eliminated all false rejoins | Single-run sweep with a corrupt block; one false rejoin total | `project_truth.md` |
| 368 ms URScript mode-switch penalty | No data or script | prose only |
| 99.6 % boot-storm shedding | No measurement | prose only |
| Hold-down suspension as a built mechanism and its "unbounded" defect | Never implemented | `gaps.md` §5 |
| μ = 3.10 packets/s, ρ = 16.14, NS-3 n* | Built on the stub | Phase 3.5/5 docs |
| ≈110 ms mechanical deceleration, EKF | Never analysed | `master.md` (deleted) |

Each was removed from the repository on 2026-09-08 or is retained only in git history and
in `audit/ground_truth_v1_2026-08-11.md`.

---

*End of Part III.*
