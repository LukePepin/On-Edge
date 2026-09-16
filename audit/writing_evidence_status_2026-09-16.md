# Evidence status for thesis writing

Updated September 16, 2026. This addendum records the September 13 source/data review and September 15-16 learning clarifications. It qualifies older prose, including `ground_truth_v2.md`; it is not a new experiment or a rewrite of raw data.

Source baseline reviewed: `fb03972343020bffb91fcf6f73b60a33d24767d4`. A repository commit identifies source history, not independently the binary flashed in every past trial. Later untracked exposure-analysis files were not reviewed as part of this handoff.

## What the historical robot timing quantity measures

`audit/eviction_latency.py` subtracts the first CSV timestamp with `attack_active == 1` from the first subsequent timestamp with `trust_score <= 30`.

- `joint_logger_node.py` sets the attack flag before starting the injection thread. It does not timestamp device receipt/processing of ATTACK.
- The logger stores the latest successfully received trust value. It clears buffered input and can miss complete or partial serial messages; repeated CSV values do not establish fresh firmware reports.
- The CSV omits device event timestamps and cycle identifiers needed to identify exact device crossing time.
- Firmware uses `trust_score < 30`, commands D12 low, then prints the trust value. Code ordering is not independent electrical-edge or standstill evidence.

Use **logged threshold-observation interval** for this quantity. Do not silently substitute “time to safe state,” physical stopping time, or exact device crossing latency.

## September 13 read-only cross-check (historical review)

The check independently read all retained V6/V7 CSVs and compared their timestamp differences with saved audit entries. It was performed in this conversation and was not saved as a new executable audit script. These results were not rerun in the September 16 writing handoff.

| Check | V6 | V7 |
| --- | ---: | ---: |
| Retained trials | 120 | 75 |
| Rows inspected | 408,146 | 242,287 |
| Trials with recorded trust at/below 30 after flag begins | 73 | 44 |
| First recorded below-threshold value skips the expected initial crossing value under the simple decay sequence | 16 | 5 |
| First threshold observation after the host attack flag clears | 13 | 9 |

All saved threshold latencies matched raw timestamp subtraction within 0.001 ms. No retained recorded trust value equaled 30, was nonfinite/outside 0-100, or fell below 100 before the first attack-flag row. Retained timestamps were strictly increasing. The 14 additional raw files comprise 13 with no recorded attack and one excluded iter99 trial.

These checks establish reproducibility and basic consistency, not hardware timing accuracy. The absence of a recorded crossing is not proof that a crossing never occurred. Nominal 50 Hz logging does not justify a fixed +/-20 ms error or a universal one-cycle correction.

Example: `data/v6_logs/trial_ECC_outage1000_ewma3_iter3_1786495528.csv` records trust 34.30 at about 474.231 ms and 16.81 at about 734.035 ms relative to the first attack flag. The expected intervening 24.01 crossing value is missing. The logged latency is reproducible; the exact missing event time is not recoverable from those rows alone.

## Physical-stop evidence requires correction

The logger substitutes six zero velocities when joint feedback is over 0.1 s old. The physical-stop classifier uses these columns without establishing freshness. Therefore:

- Fresh zero velocity and synthetic zero from missing feedback must not be conflated.
- Old counts such as “245 physical stops,” “zero false stops,” and complete agreement of physical-stop outcome with a threshold law are not established by that classifier alone.
- Trust crossing does not demonstrate motion onset, deceleration, or standstill time.
- No new physical stop measurements have been collected by the planning/quiz work.

## Implemented mechanism and interpretation

- ATTACK sets an internal state that forces the next applicable observation to zero. EWMA updates then lower the accumulated score.
- The normal path separately penalizes excessive execution time (150 ms ECC / 400 ms proxy thresholds). The retained experiment does not show that real DoS or corrupted packets activated this penalty.
- Commands are processed between workload cycles. Workload execution, update position, reporting, and waits affect the response.
- RECOVER clears attack state but does not raise D12. A valid configuration resets score/cycle/attack state and raises D12. There is no implemented permission lease.
- The ZKP-labeled workload performs two public-key computations; it does not verify a received proof. It is not a universal verification-cost bound.
- A Windows COM32 profiler host and Pi/Linux trial conventions must not be treated as a single proven historical host configuration.
- The bench reader avoids the specific per-read flush defect, but host observations are not automatically exact firmware timestamps or universally lossless measurements.
- The bench detection-plus-response total is an arithmetic identity from common endpoints. Its hard-coded prediction/residual columns are not validated model evidence.
- The simple EWMA equation is not itself a novelty claim. A measured relationship with explicit assumptions may be useful; a guaranteed bound requires justified limits on all included delays.

## Writing and V8

Retain supported historical observations with their definitions. Mark V8 instrumentation, experimental matrix, physical criteria, and results as proposed/pending. New measurements cannot retroactively restore missing historical data. The approved plan allows bounded logging fixes and physical measurement validation; it does not authorize a full proof protocol, wider architecture, or automatic technical execution.

The documented one-signal/two-safeguard-input interface is not evidence of a validated redundant safety design. Before physical work, verify the actual lab interface and manufacturer requirements. Motion telemetry is preferred for motion; an oscilloscope measures electrical events. Relating them requires a defensible time relationship.

See [writing entry point](../docs/WRITING_START_HERE.md) and the separate Thesis repository's cut list/study materials.
