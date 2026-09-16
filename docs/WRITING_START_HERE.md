# Writing from On-Edge

Updated September 16, 2026. This repository holds implementation and historical evidence. Write thesis prose in the separate [Thesis repository](https://github.com/LukePepin/Thesis), currently `draft 9-23/`.

## Read in this order

1. [Evidence corrections and current interpretation](../audit/writing_evidence_status_2026-09-16.md).
2. [Agreed timing outline](../thesis_outline_timing_experiment.md).
3. [Thesis writing brief](https://github.com/LukePepin/Thesis/blob/main/draft%209-23/writing_brief.md), [cut list](https://github.com/LukePepin/Thesis/blob/main/draft%209-23/chapter_cut_list.md), and [study guide](https://github.com/LukePepin/Thesis/blob/main/draft%209-23/study_materials/project_study_guide.pdf).
4. Actual code/data for the claim being written. Local sibling path: `../../Thesis/draft 9-23/` from this `docs/` directory.

Cross-repository GitHub links require the corresponding files to be published. Local availability is separate from remote synchronization.

## Source map

| Writing need | Source | Read with this limitation |
| --- | --- | --- |
| EWMA, workload, commands, output latch | [Firmware](../firmware/unified_trust_monitor_template/unified_trust_monitor_template.ino) | Misleading function names do not establish verification |
| What the CSV actually records | [Logger](../src/sentry_logic/sentry_logic/joint_logger_node.py) | Lost serial reports, cached trust, synthetic zero velocities |
| Trial and campaign procedure | [Wrapper](../scripts/run_test.sh), [campaign](../scripts/run_campaign.py), [kinematics](../src/sentry_logic/sentry_logic/stream_wrist_kinematics.py) | Code history is not proof of every historical hardware state |
| Logged threshold interval | [Analysis definition](../audit/eviction_latency.py), [V6 table](../audit/eviction_v6.csv), [V7 table](../audit/eviction_v7.csv) | Observed report timing, not independently measured stop timing |
| Underlying robot-trial records | [V6](../data/v6_logs/), [V7](../data/v7_logs/) | Include valid non-crossing observations; preserve exclusions |
| Supporting bench timing | [Harness](../scripts/run_end_to_end_campaign.py), [records](../data/v7_logs/e2e_composition_results.csv) | No robot; host clocks; unvalidated prediction columns |
| Old physical classifications | [Classifier](../audit/physical_stop_crosstab.py) | Does not resolve stale-feedback zero filling |
| Prior summaries and source inventory | [Ground truth v2](../ground_truth_v2.md), [project review](project_summary_review.md) | Consult the correction addendum first |

## Do not import old assumptions into the draft

The main robot experiment injects failure over serial; DIL/cloud loss is motivation. No real ZKP verification, lease renewal, mesh, independent DoS detection, or safety certification was demonstrated by those trials. Cloud-failover, hold-down, watchdog expansion, and unrelated simulations are outside the agreed core.

`todoist.md` is an older snapshot. Live Todoist has the approved September draft/demo and October validation plan. V8 is still planned; design questions from the quiz are not implemented changes.

Firmware, scripts, raw data, and unreviewed exposure-analysis artifacts are not changed by this writing handoff. Do not run historical scripts simply because they appear in a README: several write output or operate hardware and require separate authorization.
