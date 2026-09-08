# On-Edge

Master's thesis repository (Luke Pepin, URI Industrial and Systems Engineering, 2026):
edge-side authorization for an industrial manipulator when its cloud identity provider is
unreachable, and the time it takes to reach a safe state.

**Read first:** [`ground_truth_v2.md`](ground_truth_v2.md) — the audited, file-traced statement of
what the system does and what the data support. It supersedes every other prose document.
[`docs/project_summary_review.md`](docs/project_summary_review.md) explains the project from
first principles. [`todoist.md`](todoist.md) is the task list.

## What was built

- A **trust monitor** on an Arduino Nano 33 BLE (Cortex-M4) that runs a cryptographic
  workload every cycle (ECC keygen, or a *ZKP-cost proxy* of two secp256r1 scalar
  multiplications), keeps an EWMA trust score, and opens the UR5's safeguard-stop input
  (Category 2 stop) when the score falls below 30.
- A **supervisor** (Raspberry Pi 4, ROS 2 Humble) that drives the UR5 trajectory, injects
  network-outage events over USB serial, and logs joint state, IMU and trust at 50 Hz.
- A **bench harness** (Arduino plus a local mock cloud) that measures the loop timing
  losslessly, and a **sentry node** state machine for cloud rejoin gating.

Naming: the workload in the ZKP path is always called the *ZKP-cost proxy*. No proof is
verified anywhere in this repository.

## Layout

| Path | Contents |
| --- | --- |
| `firmware/unified_trust_monitor_template/` | trust-monitor firmware (canonical) |
| `firmware/zkp_real_profiler/` | stand-alone cost profiler for the proxy |
| `firmware/sentry_node/` | cloud-viability state machine (bench) |
| `scripts/run_test.sh`, `run_campaign.py` | one robot trial; the randomized campaign |
| `scripts/run_real_zkp_test.py` | proxy profiling host script (`data/real_zkp_profiling.csv`) |
| `scripts/run_end_to_end_campaign.py` | bench block (`data/v7_logs/e2e_composition_results.csv`) |
| `scripts/run_cloud_failover_sweep.py` | sentry sweep (`data/cloud_failover_sweep_results*.csv`) |
| `scripts/combine_v6_sub_eviction.py`, `combine_v7_logs.py` | campaign CSV concatenation (note: `combine_v7_logs.py` still globs `data/trial_ZKP_outage*.csv`; the V7 files moved to `data/v7_logs/` on 2026-08-14) |
| `src/sentry_logic/` | ROS 2 package: `joint_logger_node.py`, `stream_wrist_kinematics.py`, `supervisor_node.py`, `c_src/` (Pi-side `uECC_verify` wrapper) |
| `data/` | V5 (`v5_spoofing_archive/`, latched-attack baseline), V6 (`v6_logs/`), V7 (`v7_logs/`, trials plus bench results), profile, sweep, summaries |
| `data/archive_pre_v5/` | V1–V4 and the Aug-10 swapover log: superseded firmware, kept for provenance only |
| `audit/` | recomputation scripts, phase notes, `ground_truth_v1_2026-08-11.md`, `decontamination_report_2026-08-14.md` |
| `docs/` | project review, literature review, `gaps.md`, original proposal |

## Reproducing the numbers

```bash
python audit/inventory_trials.py          # matrices, validity, duplicates
python audit/eviction_latency.py data/v6_logs v6
python audit/eviction_latency.py "data/v7_logs/trial_ZKP_outage*.csv" v7
python audit/physical_stop_crosstab.py data/v6_logs V6
python audit/zkp_profile_stats.py
python audit/make_thesis_figures.py <output-dir>
```

## Running a robot trial (requires the UR5 cell)

See the header of `scripts/run_test.sh`. Supervisor build: `colcon build --packages-select sentry_logic`
then `source install/setup.bash`. The trust-monitor firmware is flashed with the PlatformIO
extension; the flashed source must match the committed source (`git log -1 -- firmware/`).

## Bench work possible without the robot

- Proxy profile on the Pi: flash `zkp_real_profiler.ino`, run `run_real_zkp_test.py` with `PORT='/dev/ttyACM0'`.
- Sentry sweep: flash `sentry_node.ino`, run `run_cloud_failover_sweep.py` (writes `..._v3.csv`).
- Loop timing: flash the trust monitor, run `run_end_to_end_campaign.py`.
