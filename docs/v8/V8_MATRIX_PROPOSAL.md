# V8 pilot matrix — proposal for Luke's decision

Status: **PROPOSED (2026-09-28). Not approved. No V8 data have been collected.**
Configs: [`v8/config/campaigns/v8_bench_pilot.json`](../../v8/config/campaigns/v8_bench_pilot.json),
[`v8/config/campaigns/v8_robot_pilot.json`](../../v8/config/campaigns/v8_robot_pilot.json).
Both carry `"status": "proposed"`; the dashboard labels them so until you set `"status": "approved"`,
`"approved_by"`, `"approved_on"` (and bump `config_version` if you change anything else).

Todoist places the final V8 matrix decision on **October 7** ("use September bench/pilot findings to select
workload/alpha contrasts and failure durations"). These are therefore **pilot** matrices for 9/29–9/30:
they check the instrumentation and estimate variability; they are not the final study design.

## What the pilot has to answer

1. Does the V8 pipeline capture every monitor record with detectable losses, correct event ordering, and a
   usable device-to-host clock relationship? (instrumentation validity)
2. On the **device clock**, how long from the monitor processing ATTACK to the first update below 30, and
   how does that depend on workload and alpha? (primary timing outcome)
3. Which injected-failure durations end before crossing, and where is the outcome phase-dependent?
   (finite-duration behaviour)
4. How large is the V8 reporting overhead (device-clock loop period vs. workload time)? (overhead)
5. Robot pilot only: with motion confirmed first, what is the sequence and spacing of D12-low command,
   controller safeguard report, and the declared telemetry standstill? (physical relationship, pilot)

## Bench pilot (Pi + Nano, no robot motion) — 30 conditions × 5 = 150 trials, about 20 min

| Factor | Levels | Purpose |
| --- | --- | --- |
| Workload | ECC (key generation), ZKP (two scalar multiplications) | historical V6/V7 workloads; contrast of cycle duration |
| Alpha | 0.1, 0.3, 0.5 | 12, 4 and 2 zero-observation updates to fall below 30 (firmware float recurrence) |
| Injected failure | 0, 250, 500, 1000, 3000 ms | 0 = no-injection control; the others span "ends before crossing" → "crosses for all settings" |

Design: full factorial, 5 repetitions, randomized complete blocks (seed 20260929). Baseline 2000 ms plus a
seeded 0–300 ms injection jitter per trial (more than one loop period, so ATTACK lands at a varying phase of
the workload cycle). ATTACK sent once; RECOVER after the failure duration; 2500 ms observation.

MODEL expectation (from the firmware recurrence and **historical** host-observed period summaries 120.4 /
232.1 ms; labelled MODEL in the preview, not a result): crossing before RECOVER is processed needs the n-th
attacked cycle to start before RECOVER is processed, i.e. failure F > w + (n−1)·T with command phase w in
[0, T). Impossible for F ≤ (n−1)T, certain for F > nT, phase-dependent between:

| Setting | (n−1)T – nT (ms) | 250 | 500 | 1000 | 3000 |
| --- | --- | --- | --- | --- | --- |
| ECC α 0.5 | 120 – 241 | **boundary** | cross | cross | cross |
| ECC α 0.3 | 361 – 482 | no | cross (near edge) | cross | cross |
| ECC α 0.1 | 1324 – 1445 | no | no | no | cross |
| ZKP α 0.5 | 232 – 464 | **boundary** | cross | cross | cross |
| ZKP α 0.3 | 696 – 928 | no | no | cross | cross |
| ZKP α 0.1 | 2553 – 2785 | no | no | no | cross |

Controls: failure 0 in every cell; configuration reset acknowledged by the device before every trial.

## Robot pilot (UR5, 9/30) — 5 conditions × 3 = 15 trials

| Condition | Purpose |
| --- | --- |
| ECC α 0.5, 3000 ms | sustained failure, fastest decision: stop characterization while moving |
| ZKP α 0.5, 3000 ms | workload contrast at the same alpha (later decision) |
| ECC α 0.1, 3000 ms | alpha contrast: slow decision (≈1.4 s) during motion |
| ZKP α 0.3, 250 ms | brief-failure control: expected to end before crossing; sweep should complete |
| ECC α 0.3, 0 ms | no-injection control: no stop expected; full-sweep telemetry continuity |

Procedure per trial: operator confirms the checklist → configuration (D12 commanded high) → wait for
safety mode NORMAL → program running (operator presses Play; `dashboard_play` is available but off) →
phase 1 approach (5 s) → settle (telemetry standstill criterion) → phase 2 sweep → **injection only after
moving is confirmed on fresh telemetry** (≥ 0.05 rad/s for 100 ms) → +800 ms + seeded 0–300 ms → ATTACK →
failure window → RECOVER → 2 s observation → wait for the trajectory result.

Proposed operational criteria (declared, not standards; recorded with every trial):
standstill = all joints |q̇| < 0.01 rad/s for 250 ms with no telemetry gap > 40 ms; moving = max |q̇| ≥
0.05 rad/s for 100 ms. Tune after seeing the real joint_states rate and noise at the lab.

## Known confounds (also listed in each config)

* Command phase (ATTACK/RECOVER processed only between cycles): measured on the device, not controlled.
* The execution-time penalty (150/400 ms) is a separate observation path; any penalty-caused decline is
  flagged per attempt and kept distinct from injected failure.
* V8 reports one larger record per cycle; its cost is measured per record (`pw_us`) and in the device loop
  period, so V8 and V6/V7 timings come from different instruments.
* Robot: pose/speed at the decision instant differ between conditions (later decisions happen further
  along the sweep); controller safeguard reports are host-receipt times; standstill depends on the declared
  criterion; the electrical D12 edge is not measured unless an oscilloscope is added and aligned; the single
  D12 → SI0/SI1 wiring is not a validated redundant safety design.
* Single Nano, single robot, one firmware build, randomized-block ordering only partly controls drift.

## Optional boundary block for October (not in the pilot)

To test the phase-dependence prediction directly, place failures inside the phase-dependent ranges measured
by the bench pilot (e.g. ECC α 0.3 at ≈420 ms, ZKP α 0.3 at ≈810 ms) with ≥ 10 repetitions each. Decide
after the pilot, from the measured device loop periods.

## Demonstration presets (labelled, not campaigns)

`v8_demo_robot.json` / `v8_demo_bench.json`: normal → brief failure → sustained failure → slow configuration,
one trial each, kind `demonstration`. The dashboard shows "Demonstration preset — not a complete experimental
campaign" wherever these data appear.

## Decision needed

Approve, change, or reduce: factor levels, repetitions (bench 5, robot 3), jitter/baseline, the motion and
standstill criteria, and the Play policy. Changing levels only requires editing the JSON (the preview shows
the full matrix and trial count before anything runs).
