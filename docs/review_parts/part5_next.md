# Part V — Where it goes next

---

## 29. Draft 2: the unified time-to-safe-state model

### 29.1 What "unified" should mean

Draft 1 presents the decay stage on its own. Draft 2 should present one expression for the
whole path from the network event to the arm at rest, with every term either measured,
bounded, or explicitly left symbolic:

    T_safe = T_detect + T_decay + T_stop

- **T_detect**: from the moment the cloud becomes unreachable to the moment the
  supervisor asserts ATTACK. Depends on probe interval P, probe timeout τ, and phase:
  under natural phase T_detect ∈ [τ, P + τ]. Measured only in the degenerate case
  (probe at the instant of failure), where it equals τ.
- **T_decay**: from ATTACK to the safety pin going low. Measured. n(α)·T + φ·T + t_s.
- **T_stop**: from the pin going low to the arm at rest. Not isolated in the data.
  Bounded above by the UR5's documented stopping performance at the commanded speed, and
  the thesis can cite the manufacturer's stopping-distance tables as the bound while
  stating that it was not measured here.

### 29.2 Closed form

With φ uniform on [0,1] and T_detect uniform on [τ, P + τ]:

    E[T_safe] = (τ + P/2) + (n(α) + ½)·T + t_s + E[T_stop]
    max T_safe = (P + τ) + (n(α) + 1)·T + t_s + max T_stop

The thesis should present both, because a safety argument is usually made on the maximum.
The V6/V7 data validate the middle term; the bench validates its structure; the first and
last terms are design inputs.

### 29.3 What to do with the logger bias

Draft 2 can either present logged latencies with the +0.15·T correction estimated from the
capture ratio, or present them uncorrected with the one-cycle-late caveat. Uncorrected with
caveat is the more defensible choice; the correction is a model of the instrument, not a
measurement.

---

## 30. Draft 2: the hold-down adversary and the wall-clock watchdog

### 30.1 Two adversaries, one built and one proposed

The project's earlier documents describe a "hold-down" mechanism that suspends trust
decay while the edge node is busy with legitimate cryptographic work, and an adversary who
keeps it busy forever. That mechanism was never built. Draft 2 should analyse it as a
*proposed* design and its failure mode, and should analyse separately the failure mode of
the *built* design:

- **Built system.** Trust falls only when the supervisor says ATTACK. An adversary who
  silences the supervisor, or a supervisor that crashes, freezes trust at 100. The edge
  node never detects this because it verifies nothing that depends on the supervisor.
- **Proposed hold-down.** If decay were suspended during verification work, an adversary
  who floods verification requests keeps decay suspended. Same outcome by a different
  route.

Both are denial-of-safety conditions: the attacker does not defeat the cryptography, only
the timing.

### 30.2 The watchdog

The natural mitigation for both is a wall-clock watchdog on the edge node: if no
well-formed heartbeat (or no completed verification) arrives within W milliseconds, treat
it as a failed observation and let trust decay. Predicted stop latency then becomes
W + T_decay; choosing W trades false stops under legitimate load against exposure under
attack. This can be analysed on paper with the measured T and simulated with any loop
model; it needs no robot. A bench confirmation (heartbeat withheld, pin observed) needs one
Arduino.

### 30.3 What the simulation should use

Cycle times 120.4 and 232.1 ms, not 125 and 247. α ∈ {0.1, 0.3, 0.5}. Threshold 30. Attack
phase uniform. Report predicted T_decay distributions and compare to the V6/V7 cells as a
check that the simulator reproduces the measured data before it is used for anything new.

---

## 31. Bench work still possible without the UR5

In priority order:

1. **Proxy profile on the Pi.** Flash `zkp_real_profiler.ino`; run `run_real_zkp_test.py`
   with the Pi port. Confirms the committed profile from a second host. Ten minutes.
2. **Failover sweep re-run.** Flash `sentry_node.ino`; run `run_cloud_failover_sweep.py`
   (current script, writes the `_v3` file); n ≥ 3 per configuration. Replaces the
   partly corrupt file. About two hours of unattended run time.
3. **Loop period under serial load.** Bench block with the joint logger's 20 Hz ATTACK
   flood active, to see whether serial interrupts move the 232 ms period. Addresses the
   July audit's "measure under load" request.
4. **Watchdog prototype.** Add the heartbeat timeout to a copy of the firmware; measure
   time from withheld heartbeat to pin low on the bench. Supports Chapter 30.
5. **Variable-base multiplication cost.** One more profiler variant calling the point
   multiplication with a non-generator base, to close the fixed-base caveat.
6. **Lossless logger.** Fix the serial reader (accumulate bytes, split on newline) in a
   copy of the logger, verify against the bench, and keep it ready for any future robot
   session. Do not touch the file that produced the archived data.

Anything requiring the arm (mid-trajectory attack, deceleration isolation, Category 0 path)
waits for renewed access and is future work in the thesis.

---

## 32. Glossary

- **α (alpha)**: EWMA weight on the newest observation. Higher reacts faster.
- **ATTACK / RECOVER**: serial keywords from supervisor to edge node that set and clear
  the attack condition.
- **Category 0 / 1 / 2 stop**: power removed immediately / controlled stop then power
  removed / controlled stop with power retained. The project's stop is Category 2.
- **C192A4**: UR safety fault code for safeguard-input channel disagreement.
- **DIL**: disconnected, intermittent, limited (network conditions).
- **DWT_CYCCNT**: Cortex-M cycle counter used to time workloads.
- **EWMA**: exponentially weighted moving average.
- **Eviction**: trust score falling below 30, which opens the safeguard input.
- **Loop period, T_cycle**: wall-clock time per firmware iteration: 120.4 ms (ECC),
  232.1 ms (proxy).
- **micro-ecc / uECC**: the C elliptic-curve library used on the edge node.
- **n(α)**: attacked cycles needed to evict: 12, 4, 2 for α = 0.1, 0.3, 0.5.
- **Physical stop**: the arm did not execute its commanded trajectory (motion criterion).
- **Proxy, ZKP-cost proxy**: two secp256r1 scalar multiplications standing in for the
  arithmetic of a Schnorr verification.
- **RTDE**: UR's real-time data exchange interface used by the ROS driver.
- **secp256r1 / P-256**: the elliptic curve used throughout.
- **Sentry node**: the second Arduino running the cloud-viability state machine.
- **SI0 / SI1**: UR5 safeguard-stop input pair.
- **Supervisor**: the Raspberry Pi 4 running ROS 2 and the orchestration.
- **Trust monitor**: the edge Arduino running the workload and the EWMA.
- **V5 / V6 / V7**: the three robot campaigns used in the thesis.

---

## 33. File and data index

Repository `On-Edge` after the 2026-09-08 cleanup.

**Top level**
- `ground_truth_v2.md` — authoritative claims ledger.
- `todoist.md` — task list.
- `README.md` — layout and reproduction commands.

**firmware/**
- `unified_trust_monitor_template/` — trust monitor (canonical).
- `zkp_real_profiler/` — proxy cost profiler.
- `sentry_node/` — cloud-viability state machine.

**scripts/**
- `run_test.sh` — one robot trial. `run_campaign.py` — randomized campaign.
- `run_real_zkp_test.py` — profiler host. `run_end_to_end_campaign.py` — bench block.
- `run_cloud_failover_sweep.py` — sentry sweep.
- `combine_v6_sub_eviction.py`, `combine_v7_logs.py` — CSV concatenation
  (the V7 one still globs the old location).
- `setup_ur5_ros2.sh` — Pi setup.

**src/sentry_logic/** — ROS 2 package: `joint_logger_node.py`,
`stream_wrist_kinematics.py`, `supervisor_node.py`, `c_src/` (Pi-side verify wrapper).

**data/**
- `real_zkp_profiling.csv` — 300 proxy runs.
- `cloud_failover_sweep_results.csv` — 108 sweep rows (27 corrupt).
- `sub_eviction_summary.csv` — V7 per-trial logged summary.
- `v5_spoofing_archive/` — V5 (latched attack), 138 files.
- `v6_logs/` — V6, 127 trial files + summary + combined.
- `v7_logs/` — V7, 82 trial files + `e2e_composition_results.csv` + combined.
- `archive_pre_v5/` — V1–V4, Aug-10 swapover log, July baseline PNG.

**audit/**
- Scripts: `inventory_data.py`, `inventory_trials.py`, `eviction_latency.py`,
  `telemetry_capture.py`, `physical_stop_crosstab.py`, `decel_after_eviction.py`,
  `zkp_profile_stats.py`, `make_thesis_figures.py`.
- Outputs: `data_inventory.csv`, `trial_inventory.csv`, `eviction_v{4,5,6,7}.csv`.
- Notes: `phase1_inventory.md`, `phase2_zkp.md`, `phase3_4_reverify.md`.
- History: `ground_truth_v1_2026-08-11.md`, `decontamination_report_2026-08-14.md`.

**docs/**
- `project_summary_review.md` — this document.
- `enhanced_earc_literature_review.md` — literature review material.
- `gaps.md` — open gaps (§5 hold-down to be rewritten as proposed, not built).
- `original_thesis_proposal.md` — historical baseline.

**Thesis repository** (`URI-ISE/Thesis/draft 9-9/`): `thesis.tex`, `chapter1–6.tex`,
`abstract.tex`, `figures/` (four data figures plus `system_flow.mmd`/`.pdf`),
`urithesis.cls`, `references.bib`.

---

*End of Part V.*
