# Phase 1 — Repository Inventory (audit working notes)

Audit date: 2026-09-07. Repo HEAD: fd2eba4 (2026-08-12 14:06 EDT). All timestamps below are
UTC unless marked EDT (commit times are EDT, `-0400`). Scripts used: `audit/inventory_data.py`
(→ `audit/data_inventory.csv`), `audit/inventory_trials.py` (→ `audit/trial_inventory.csv`).

## 0. Blocking finding

`ground_truth.md` (dated 2026-08-11) is **not in the repo**, not in git history (`git log --all -- '*ground_truth*'`
is empty), not in `archive/`, and not anywhere under the user's home directories. Phase 3 cannot be
executed section-by-section without it.

## 1. Directory map

| Path | Content | Tracked |
|---|---|---|
| `firmware/unified_trust_monitor_template/` | Trust-monitor firmware (ECC/ZKP/CLOUD modes, EWMA, safety pin) | yes |
| `firmware/zkp_real_profiler/` | Standalone scalar-mult profiler (added 01a0971, 2026-08-11) | yes |
| `firmware/sentry_node/` | Cloud-viability state machine (K-passes + dwell hysteresis) | yes |
| `firmware/cloud_edge_cloud_failback/` | Print-only demo; no logic, no serial protocol | yes |
| `scripts/` | 11 py + 2 sh orchestrators/analysers | yes |
| `src/sentry_logic/` | ROS 2 package: joint_logger, kinematics, supervisor, legacy nodes | yes |
| `data/` (top level) | V7 core campaign trials + summaries + profiling + sweep | yes |
| `data/v1..v6_*` | Archived campaigns V1–V6 | yes |
| `data/v7_logs/` | combined V7 CSV + end-to-end composition results | yes |
| `archive/` | 60_trial_run pcaps, 29 legacy scripts, 6 legacy docs | **ignored** |
| `camera/` | videos/screens | ignored (1 png tracked) |
| `audit/`, `docs/` | prose | yes (audit/conclusion2.md untracked) |

## 2. Data files

Per-directory roll-up (from `inventory_data.py` / `inventory_trials.py`):

| Directory | Trial CSVs | Valid* | Rows | Time span (UTC) | Factors | Writer |
|---|---|---|---|---|---|---|
| `data/v1_probabilistic_archive/58_trial_confirmed` | 54 | 54 | 101,310 | 2026-08-05 22:37–23:34 | ECC/ZKP × loss{25,50,75}% × ewma{1,3,5} × iter1-3 | joint_logger (loss = iptables random drop; older run_test.sh) |
| `data/v2_deterministic_archive` | 144 | 125 | 253,442 | 2026-08-06 00:38–02:36 | ECC/ZKP × "loss"{500,1000,2000,5000}ms × ewma{1,5,9} × iter1-12 (Res-IV 12-config design) | joint_logger; filename still says `loss` |
| `data/v3_deterministic_archive` | 124 | 104 | 447,634 | 2026-08-06 16:46–19:46 | ECC/ZKP × outage{500,1000,2000,5000} × ewma{5,7,9} (+ a few ewma1/iter0) | joint_logger |
| `data/v4_logs` | 133 | 121 | 520,244 | 2026-08-06 20:33 – 08-07 00:07 | ECC/ZKP × outage{500,1000,2000,5000} × ewma{5,7,9} × iter1-5 → 120 cells complete | run_campaign (randomized queue, seed 42) |
| `data/v5_spoofing_archive` | 138 | 120 | 524,057 | 2026-08-07 16:53–20:46 | ECC/ZKP × outage{500,1000,2000,5000} × ewma{1,3,5} × iter1-5 → 120 cells complete | run_campaign |
| `data/v6_logs` | 127 | 120 | 829,568 | 2026-08-11 23:12 – 08-12 01:59 | ECC × outage{250,500,1000,2000} × ewma{1,3,5} × iter1-10 → 120 cells | run_campaign @e8632fd; `sub_eviction_summary.csv` 120 rows |
| `data/` (V7 core) | 82 | 75 (+1 smoke iter99) | ≈778k | 2026-08-12 15:48–17:35 | ZKP × outage{250,500,1000,3000,5000} × ewma{1,3,5} × iter1-5 → 75 cells | run_campaign @6db79e0; `sub_eviction_summary.csv` 75 rows |

\* "Valid" = passes `run_campaign.validate_trial()` (≥50 rows, `attack_active==1` observed). Invalid files are
attempts where the attack never fired; in V4–V7 each was re-run (hence duplicate cells). In V2/V3 no re-run
occurred, so those matrices are short in some cells.

Non-trial CSVs:

| File | Rows | Columns | Writer | Notes |
|---|---|---|---|---|
| `data/real_zkp_profiling.csv` | 300 | cycle,start_cycles,end_cycles,total_cycles,exec_time_ms,res1,res2,keybyte | `scripts/run_real_zkp_test.py` (PORT=`COM32` → Windows host) | committed 01a0971 2026-08-11 18:43 EDT |
| `data/cloud_failover_sweep_results.csv` | 108 | probe_ms,K,dwell_ms,outage_pattern,unmonitored_motion_ms,false_rejoin_rate,detection_latency_ms,recovery_latency_ms,oscillation_count | `scripts/run_cloud_failover_sweep.py` **@e8632fd** (HEAD writes `..._v3.csv`, which does not exist) | PORT=`COM32`; no in-file timestamps; committed 6db79e0 |
| `data/sub_eviction_summary.csv` | 75 | algo,outage_ms,alpha,iter_num,stop_occurred,min_trust | run_campaign (V7) | |
| `data/v6_logs/sub_eviction_summary.csv` | 120 | same | run_campaign (V6) | |
| `data/v7_logs/e2e_composition_results.csv` | 20 | probe_ms,algo,alpha,iter,t_jam,t_detection,t_first_decay,t_eviction,… | `scripts/run_end_to_end_campaign.py` (PORT=/dev/ttyACM0 → Pi; **no robot, no logger**) | t_jam 2026-08-12 17:54–17:55 UTC |
| `data/v7_logs/combined_v7_campaign.csv` | ~778k | trial cols + algo,outage_ms,alpha,iteration | `scripts/combine_v7_logs.py` | includes the 6 invalid attempts (script only skips iter99) |
| `data/distributed_swapover_log_20260810_150831.csv` | 1,940 | timestamp,node,algorithm,cycle,exec_time_ms,trust_score | `scripts/run_swapover_expansion.py` | 2026-08-10; ZKP exec ≈334 ms → produced by the **3×make_key stub** firmware |
| `data/md1_profiling_n10_1786489760.csv`, `..._1786489938.csv` | **0** (header only) | request_id,execution_time_ns,success | `src/.../supervisor_node.py` | empty; orphan |
| `data/combined_v5_spoofing.csv` (ignored) | — | | `combine_v5_spoofing_archive.py` | local only |

PCAPs: 83 top-level (V7), 59 in v1/60_trial_run, 120 v3, 132 v4, 138 v5, 128 v6, 0 in v2 (v2 pcaps live in ignored `archive/60_trial_run/`).

## 3. Firmware

| File | Board | Accepts (serial) | Emits | Referenced by | Last change |
|---|---|---|---|---|---|
| `unified_trust_monitor_template.ino` | Nano 33 BLE (nRF52840 Cortex-M4, DWT @ 64 MHz assumed: `/64000.0`) | `{"algo":..,"alpha":..}\n` (boot handshake and runtime reset), `ATTACK\n`, `RECOVER\n` | `{"status":"READY"}`, per-cycle `{"cycle","exec_time_ms","trust_score"}` | joint_logger_node.py, run_end_to_end_campaign.py, run_swapover_expansion.py | 6db79e0 2026-08-12 11:46 EDT (ZKP block → 2×`uECC_compute_public_key`; comments Category 0→2) |
| `zkp_real_profiler.ino` | same | 64 raw bytes | `READY`, `{"start","end","res1","res2","keybyte"}` | run_real_zkp_test.py | 01a0971 2026-08-11 |
| `sentry_node.ino` | Nano 33 BLE (no crypto) | `CONFIG:K,DWELL`, `CLOUD_UP/DOWN`, `BOOTSTRAP_COMPLETE`, `REJOIN_CONFIRMED/FAILED` | `{"status":"SENTRY_ONLINE"}`, `{"transition":..}`, `{"cmd":"INITIATE_REJOIN"}` | run_cloud_failover_sweep.py | 01a0971 2026-08-11 (rewrite; previous fcc893e 2026-08-10 was fixed 5 s ZKP + 10 s ECC timers emitting START_ZKP/START_ECC/REJOIN_CLOUD) |
| `cloud_edge_cloud_failback.ino` | Nano 33 BLE | nothing | fixed demo strings every 5 s (incl. hard-coded "EWMA Trust Score: 98.4") | docs/cloud_edge_cloud_runbook.md only | 1d2a2f5 2026-08-07 |

Key firmware facts (HEAD):
- EWMA: `trust_score = alpha*current_trust + (1-alpha)*trust_score` (lines 137, 194). alpha weights the **new** sample. Init 100, eviction `< 30.0` (line 16, 139, 196).
- Under `attack_mode_active`, `current_trust = 0.0` unconditionally (lines 126-128, 183-185). No hold-down/suspension logic exists anywhere in firmware or scripts (grep `hold` → 0 hits in code).
- Safety output: single pin `SAFETY_PIN = 12` (line 46). Driven LOW on eviction; driven HIGH only in `setup()` and on JSON reconfigure. There is no path that re-raises it after a `RECOVER`.
- ECC mode: 1×`uECC_make_key` per cycle (+10 ms delay). ZKP mode: 2×`uECC_compute_public_key` on a static payload (+10 ms delay). Both are keygen/scalar-mult; neither verifies anything.
- Cycles→ms uses 64,000 cycles/ms in both firmware and `run_real_zkp_test.py` (`CYCLES_PER_MS = 64000.0`).

Firmware ↔ campaign mapping (inferred from commit time vs. filename epochs; **the flashed binary is not tracked**):

| Campaign | Ran (EDT) | Firmware commit in effect | ZKP block | RECOVER honoured? |
|---|---|---|---|---|
| V1 | 08-05 18:37–19:34 | 0d86b5e/e351b7e | 3×make_key (+6 extra under attack) | no (no such cmd) |
| V2 | 08-05 20:38–22:36 | same | same | no |
| V3 | 08-06 12:46–15:46 | same (pre-d2f7ad6) | 3×make_key, blocking attack loops | no |
| V4 | 08-06 16:33–20:07 | d2f7ad6 (non-blocking, trust=0 under attack) | 3×make_key | no → attack latched until JSON reset |
| V5 | 08-07 12:53–16:46 | eef65fe (unchanged loop) | 3×make_key | no → latched |
| swapover (Aug 10) | 08-10 ~11:08 | de42883/fffa21a | 3×make_key (334 ms) | no |
| V6 | 08-11 19:12–21:59 | 01a0971 (RECOVER added 18:43) | 3×make_key (unused; ECC only) | yes |
| V7 core | 08-12 11:48–13:35 | 6db79e0 (committed 11:46) | 2×compute_public_key | yes |
| V7 e2e | 08-12 13:54–13:55 | 6db79e0 | same | yes |

Anything modified after 2026-08-11: `unified_trust_monitor_template.ino` (08-12), `run_campaign.py` (08-12), `run_end_to_end_campaign.py` (08-12, new), `combine_v7_logs.py`, `combine_v6_sub_eviction.py`, `analyze_v6_data.py` (08-12, new), plus data dirs v6/v7 and top-level V7 trials. Modified on 08-11 (same day as ground_truth): `zkp_real_profiler.ino` (new), `sentry_node.ino` (rewrite), `run_real_zkp_test.py` (new), `run_cloud_failover_sweep.py` (new; 3 revisions 18:43→20:35), `joint_logger_node.py` (RECOVER), `run_test.sh`.

## 4. Orphans and mismatches

- `run_swapover_expansion.py` expects sentry messages `START_ZKP/START_ECC/REJOIN_CLOUD` and sends `JAMMED`; current `sentry_node.ino` emits/accepts none of these. Script only works with the 2026-08-10 sentry firmware (fcc893e). Its data (`distributed_swapover_log_*.csv`) was produced with the stub ZKP.
- `run_cloud_failover_sweep.py` HEAD writes `cloud_failover_sweep_results_v3.csv`; only `cloud_failover_sweep_results.csv` exists. Producing revision is e8632fd or earlier; the later "fix V2 serial buffering and log parse failures" commit (af59d47) postdates the file's name.
- `analyze_distributed_swapover.py` reads `distributed_swapover_log_20260810_150831.csv` from CWD, not `data/`.
- `md1_profiling_n10_*.csv`: header-only.
- `cloud_edge_cloud_failback.ino` and `run_cloud_failback_test.py`: demo-only, no measurement, no data.
- `running.md` references `scripts/cloud_idp_server_1s.py` etc. → moved to ignored `archive/scripts/`.
- `analyze_v6_data.py` assumes a 20 ms cycle time (its own comment questions this); ECC cycle is ~121–125 ms.
- `src/sentry_logic` legacy nodes (`zkp_auth_service.py`, `zkp_auth_verifier.py`, `mock_niryo_bridge.py`, `h1_test_listener.py`, `trust_monitor_node.py`, `supervisor_node.py`, `pick_and_place.py`) untouched since June/July; not used by any campaign script.
- `src/edge_node/.pio/libdeps/nano33ble/micro_ros_platformio` — dead micro-ROS remnant.
- Prose vs code: prose describes a dual-channel SI0/SI1 drive (pins 5/6) and a "hold-down" suspension; the campaign firmware drives one pin (D12) and has no hold-down.

## 5. Threshold-tuning flags (for Phase 3/5)

- e351b7e (2026-08-05): ZKP stub changed 10×→3×`uECC_make_key` with comment "≈334.5 ms … perfectly fits right under your 400 ms threshold bound"; ECC threshold moved 100→150 ms "gives ~38 ms headroom". Both thresholds were chosen after the fact to sit above the measured workload.
- The 400 ms / 150 ms thresholds only matter when `attack_mode_active == false`; under attack `current_trust` is forced to 0 regardless of timing, so exec-time thresholds play no role in any V4–V7 eviction result.
- `run_swapover_expansion.py` labels algorithm by `exec_time_ms > 200` (line 153), i.e. the "ZKP vs ECC" column in the swapover log is inferred from timing, not from state.
