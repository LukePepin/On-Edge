# V8 dataset schema (`onedge.v8.dataset/1`)

Raw measurements are append-only and never rewritten. Metadata files are created once (`open(..., "x")`).
Derived files (`summary.json`) can be regenerated with `python -m onedge_v8.analysis <attempt_dir>`.
Exclusions are stored separately. Simulated data live in a different root (`data/v8_sim/`, git-ignored) and
carry `"simulated": true`, `"data_origin": "software_simulation"`.

## Roots

| Root | Contents |
| --- | --- |
| `data/v8/` on the Pi | original hardware records (the source of truth) |
| `data/v8/` on the lunchbox | verified copies of **closed** sessions (`/api/sync`: SHA-256 checked, never overwrites) |
| `data/v8_sim/` | software-simulation records only |
| `<root>/annotations/exclusions.jsonl` | manual exclusion/restore events |

## Layout

```
<root>/daemon_runs/<run_id>/            one per daemon start; always recording
    run.json                            daemon config, software provenance, mode, realtime result
    serial_rx_raw.jsonl                 every byte read from the monitor during the run
    daemon_events.jsonl                 link/robot/operator events outside a session
    *_nosession.jsonl                   parsed records with no session open
<root>/sessions/<session_id>/           session_id = <UTC start>_<campaign_id>_v<config_version>
    session.json                        campaign identity, kind, status, operator, acknowledgements, plan hash,
                                        software provenance (git commit, dirty files, source SHA-256),
                                        device identity at start, robot capabilities, clock and unit notes
    campaign_config.json                verbatim config file text
    plan.json                           explicit ordered plan (conditions, trials, seed, jitter, plan_sha256)
    session_events.jsonl                runner states, operator actions and decisions, notes
    serial_rx_raw.jsonl                 every byte read during the session
    device_msgs_idle.jsonl, serial_tx_idle.jsonl, host_events_idle.jsonl, robot_state_idle.jsonl
    attempts.jsonl                      attempt started / ended index
    attempts/<trial_id>_A<n>/           one directory per attempt (retries get A2, A3, ...)
        attempt_start.json              planned trial, attempt number, trial + telemetry config, device and
                                        robot status at start
        device_msgs.jsonl               parsed monitor records
        serial_tx.jsonl                 host commands
        host_events.jsonl               runner phases, trajectory events, link events, dashboard queries
        robot_state.jsonl               controller safety mode / program state (host receipt time)
        joint_states.csv                every joint_states message during the attempt
        attempt_end.json                status, reason, phase reached, departures, continuity, recorder state
        attempt_recovered.json          only if the process died: "interrupted" + file counts
        summary.json                    DERIVED: events, intervals, outcome, quality warnings
    session_end.json                    final state, per-trial resolution, counts
    session_recovered.json              only if the session never closed
    manifest.json                       path, size, SHA-256 of every file at close
```

## Clock domains and units

| Field suffix | Clock | Unit |
| --- | --- | --- |
| `t_us`, `t0_us` (inside `f`) | device `micros()`, 32-bit, raw | µs |
| `t_dev_us`, `t0_dev_us` | device clock unwrapped within `epoch` | µs |
| `*_mono_ns` | Pi `time.monotonic_ns()` | ns |
| `*_wall_ns` | Pi `time.time_ns()` | ns |
| `stamp_ns` | ROS header stamp (Pi system clock) | ns |

`epoch` counts device restarts seen by the host; device times from different epochs are not comparable.

## Device records (`device_msgs*.jsonl`)

```json
{"rx_mono_ns":..., "rx_wall_ns":..., "first_rx_mono_ns":..., "status":"ok", "kind":"upd", "proto":"v8",
 "epoch":0, "t_dev_us":..., "t0_dev_us":..., "f":{...record fields...},
 "raw":"<only when status != ok>", "problems":[...], "cont":[{"kind":"gap","expected":41,"got":43,"missing":2}],
 "first_after_connect":true}
```

`status`: ok, empty, invalid_encoding, not_json_object, malformed_json, invalid_fields, invalid_value,
unknown_message, overflow, unterminated. `cont` kinds: gap, duplicate, reset, clock_backstep (large),
legacy_cycle_gap. `first_after_connect` marks the first line after (re)opening the port (often partial).

Firmware record fields (protocol 1):

| kind | fields |
| --- | --- |
| boot / hello | fw, ver, build, proto, thr, pen_ecc_ms, pen_zkp_ms, pin, d12, n_cfg |
| cfg | algo, wl (ECC/ZKP/NONE actually selected), alpha, trust, cycle, attack, d12, n_cfg |
| cmd | cmd (ATTACK/RECOVER), attack (after), prev (before), cycle (next update) |
| upd | t0_us (workload start), cycle, exec_ms (DWT), obs, trust, attack, below (trust<30), d12 (commanded level after the update), pw_us (previous report write duration, -1 if none) |
| out | pin, level (0 = first LOW command after HIGH; 1 = raised by configuration), cycle, trust |
| idle | algo |
| err | code (bad_json, bad_cfg, unknown_cmd, overflow), len |

Legacy firmware (template) records parse as `legacy_upd` {cycle, exec_ms, trust} and `legacy_ready`; missing
updates are detected from `cycle`; there are no device times.

## Host commands (`serial_tx*.jsonl`)

`t_request_mono_ns`, `t_write_start_mono_ns`, `t_write_end_mono_ns` (write + flush returned), `t_wall_ns`,
`cmd` (ATTACK/RECOVER/CONFIG), `text`, `purpose` (trial_config, trial_attack, trial_attack_resend,
trial_recover, manual_attack, ...), `source` (runner/operator), `note`, `ok`, `error`.

## Joint states (`joint_states.csv`)

`rx_mono_ns, rx_wall_ns, stamp_ns, valid, problem, msg_order, pos_<joint>×6, vel_<joint>×6` in canonical
order (shoulder_pan … wrist_3), mapped by name. `msg_order` gives each canonical joint's index in the
original message. Invalid messages keep a row with `valid=0`, the problem text, and empty values — never zeros.
Rows exist only during attempts.

## Attempt statuses

completed · failed_setup · failed_precondition · failed_procedure · failed_acquisition · fault_robot ·
aborted_operator · interrupted (from `attempt_recovered.json`) · unfinalized (no end record and not yet
recovered).

## Summary (`summary.json`, definitions `onedge.v8.definitions/1`)

* `events`: D_CFG, D_ATTACK, D_CROSS, D_OUT_LOW, D_RECOVER (device), H_CFG_SENT, H_ATTACK_SENT,
  H_RECOVER_SENT, H_RX_CROSS, H_RX_OUT_LOW, H_RX_SAFEGUARD (host).
* `key_intervals`: each with `clock` and `definition`; cross-clock ones also `range_ms` and a note.
  `device_attack_to_cross`, `device_attack_to_out_low`, `device_cross_to_out_low`, `device_failure_window`,
  `host_attack_sent_to_rx_cross`, `host_attack_sent_to_rx_out_low`, `host_failure_window`,
  `host_attack_sent_to_rx_safeguard`, `aligned_attack_sent_to_device_processed`,
  `aligned_out_low_to_rx_safeguard`, and for robot trials `host_attack_sent_to_standstill`,
  `aligned_out_low_to_standstill`.
* `attacked_updates_to_cross` (from cycle numbers, robust to missing records) and `model_check` (MODEL).
* `updates`: loop period (device clock, consecutive cycles only), exec_ms, report write µs, min trust,
  penalty updates.
* `motion`: telemetry rate and gaps, `moving_before_injection`, `standstill_after_out_low` (status reached /
  not_reached / undetermined / no_data, window start, preceding gap), criteria used.
* `outcome`: injection (not_planned, not_sent, processed, not_observed), crossing
  (crossed_while_attack_active, crossed_without_attack, no_crossing_in_complete_record,
  no_crossing_observed_record_incomplete, undetermined_legacy_protocol), crossing relative to RECOVER,
  D12-low commanded, crossing report received after RECOVER was sent.
* `quality_warnings` (automatic, never exclude): malformed_records, sequence_gap (with whether it falls in
  the attack→crossing window), device_reset_during_attempt, execution_time_penalty_observed,
  attack_not_sent / attack_not_acknowledged / recover_not_sent / recover_not_acknowledged,
  robot_fault_safety_mode, joint_invalid_samples, joint_telemetry_gap, joint_telemetry_missing,
  not_confirmed_moving_at_injection, operator_commands_during_attempt.
* `not_measured_by_this_software`: electrical D12 transition; physical standstill beyond the criterion.

## Exclusions (`annotations/exclusions.jsonl`, schema `onedge.v8.exclusion/1`)

`event_id, t_wall_ns, t_utc, action (exclude|restore), session_id, attempt_id, scopes (all |
comparison_plots | timing_analysis | motion_analysis), reason (≥ 8 characters), operator`. Current state =
replay of all events in order. Restores add events; history is never deleted.
