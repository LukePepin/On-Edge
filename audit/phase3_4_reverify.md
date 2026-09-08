# Phase 3 — Re-verification of ground_truth.md (2026-08-11) · Phase 4 — New results

Scripts: `audit/eviction_latency.py`, `audit/telemetry_capture.py`, `audit/physical_stop_crosstab.py`,
`audit/decel_after_eviction.py`, `audit/zkp_profile_stats.py`. Line numbers refer to HEAD fd2eba4.

## Phase 3 — section by section

### §1 EWMA update rule — STILL TRUE (line numbers moved)
`unified_trust_monitor_template.ino` lines 137 and 194 (were 134/182): `trust = α·current + (1−α)·trust`.
Under attack `current_trust = 0.0` at lines 128 and 185. Alpha weights the new sample; n(α) = ceil(log 0.3 / log(1−α)) = 12/4/2 for α = .1/.3/.5. Eviction test is `trust_score < 30.0` (lines 139, 196); the analysis scripts use `<= 30.0`; no trust value 100·(1−α)^k equals 30 exactly for the α used, so the two are equivalent. `outline_v2.md` §3.4 still carries the reversed formula (unchanged since 2026-08-07).

### §2 Measured cycle times — CHANGED
Swapover-log statistics reproduce exactly (ECC n=1640 111.54±0.09, "ZKP" n=300 334.66±0.17). The 334.66 figure remains the withdrawn stub. New values:

| Path | crypto only (DWT) | full loop period (wall clock, e2e, n=10 each) |
|---|---|---|
| ECC (`uECC_make_key`) | 111.54 ms (swapover log, n=1640) | 120.4 ms (sd 4.8, 113–124) |
| ZKP-cost proxy (2×`uECC_compute_public_key`) | 224.86 ms (sd 0.21, n=300, `real_zkp_profiling.csv`) | 232.1 ms (sd 5.4, 226–236) |

The fitted "123 ms / 345–375 ms" periods in §2 are superseded by 120 / 232 ms. The 247 ms figure in `conclusion2.md` and `run_end_to_end_campaign.py` line 177 is UNTRACED and is to be archived (Luke, 2026-09-07).

### §3 Measured eviction latency — STILL TRUE for V5; new tables for V6/V7 (recomputed, not copied)
V5 recomputation from the 120 per-trial CSVs matches §3 to 0.1 ms in every cell (`audit/eviction_v5.csv`). But two caveats now attach to every logger-derived latency:

1. **Attack latched in V1–V5.** The logger's `attack_active` flag stayed at 1 for ≈63.3 s in every V5 trial (column `attack_flag_ms` in `eviction_v5.csv`), i.e. the nominal 500–5000 ms outage was neither delivered to the firmware nor recorded by the logger. §6.1 stands for that data.
2. **Dropped telemetry lines** (new defect, see §6.5 below) bias logged latencies late by one cycle in roughly 10–20 % of trials.

New campaigns (RECOVER honoured), logger clock, valid trials only:

V6 — ECC, 2026-08-11, n=10 per cell, `audit/eviction_v6.csv`:

| α | outage | logged stops | physical stops | evict mean | sd | min | max |
|---|---|---|---|---|---|---|---|
| 0.1 | 250/500/1000 | 0/0/0 | 0/0/0 | – | | | |
| 0.1 | 2000 | 10 | 10 | 1572.0 | 38.5 | 1519.5 | 1648.1 |
| 0.3 | 250 | 0 | 0 | – | | | |
| 0.3 | 500 | 9 | **10** | 608.6 | 41.3 | 550.2 | 664.2 |
| 0.3 | 1000 | 10 | 10 | 659.5 | 74.2 | 540.9 | 765.0 |
| 0.3 | 2000 | 10 | 10 | 617.6 | 60.6 | 550.8 | 732.5 |
| 0.5 | 250 | 4 | **10** | 358.3 | 30.9 | 312.8 | 381.8 |
| 0.5 | 500 | 10 | 10 | 375.6 | 65.9 | 290.5 | 501.6 |
| 0.5 | 1000 | 10 | 10 | 324.0 | 39.9 | 286.6 | 394.1 |
| 0.5 | 2000 | 10 | 10 | 390.5 | 94.3 | 273.3 | 504.7 |

V7 — ZKP-cost proxy, 2026-08-12, n=5 per cell, `audit/eviction_v7.csv`:

| α | outage | logged stops | physical stops | evict mean | sd | min | max |
|---|---|---|---|---|---|---|---|
| 0.1 | 250/500/1000 | 0 | 0 | – | | | |
| 0.1 | 3000 | 5 | 5 | 2995.1 | 168.2 | 2846.4 | 3263.4 |
| 0.1 | 5000 | 5 | 5 | 3030.1 | 117.6 | 2950.5 | 3233.9 |
| 0.3 | 250/500 | 0 | 0 | – | | | |
| 0.3 | 1000 | 4 | **5** | 1076.6 | 73.9 | 978.3 | 1149.4 |
| 0.3 | 3000 | 5 | 5 | 1120.0 | 39.5 | 1050.1 | 1145.9 |
| 0.3 | 5000 | 5 | 5 | 1122.4 | 100.4 | 990.8 | 1250.1 |
| 0.5 | 250 | 0 | 0 | – | | | |
| 0.5 | 500 | 5 | 5 | 653.9 | 25.6 | 629.9 | 681.4 |
| 0.5 | 1000 | 5 | 5 | 551.6 | 21.8 | 537.6 | 589.7 |
| 0.5 | 3000 | 5 | 5 | 629.6 | 112.8 | 526.4 | 787.0 |
| 0.5 | 5000 | 5 | 5 | 658.8 | 87.2 | 515.4 | 742.1 |

"Physical stops" = the arm did not execute the commanded trajectory (standstill sustained through t_attack + 9.5 s), from the joint-velocity columns (`audit/physical_stop_crosstab.py`). Across V5+V6+V7, 0 trials were logged-stop-but-moving; 8 trials were physically stopped but logged as non-stops (7 in V6, 1 in V7), all in boundary cells, all explained by the dropped crossing line. **Stop/no-stop classification should use the motion columns, not `trust<=30` in the CSV.** With that correction the quantized model n(α)·T_cycle predicts every cell: ECC 2×120 = 240 < 250 → stop (10/10); ZKP-proxy 4×232 = 928 < 1000 → stop (5/5). The "partial 4/5 boundary cell" in `conclusion2.md` is an artefact.

Safety-budget consequence (unchanged in direction): the only condition with mean latency under 500 ms is ECC at α = 0.5 (V6 mean 362.8 ms, max 504.7 ms; V5 max 504.9 ms). With the ZKP-cost proxy the fastest condition is α = 0.5 at 623.5 ms mean, 515 ms minimum. Note that in every ECC α=0.5 stop (V5 20/20, V6 34/34) and every ECC α=0.3 stop except the 2000 ms cell, **the arm had not yet started moving when the safeguard input opened** (motion is commanded from t_attack+0.5 s; see `stream_wrist_kinematics.py` lines 192-210). Sub-500 ms stops of a *moving* arm were never observed; the physical evidence for those cells is "the commanded trajectory was never executed."

### §4 Factor levels — STILL TRUE for V5; extended
V5: ECC/ZKP-stub × {500,1000,2000,5000} × {.1,.3,.5} × 5 = 120. V6: ECC × {250,500,1000,2000} × {.1,.3,.5} × 10 = 120 (`run_campaign.py` @e8632fd lines 98-101). V7: ZKP-proxy × {250,500,1000,3000,5000} × {.1,.3,.5} × 5 = 75 (HEAD lines 98-101). e2e: {100,500} probe × {ECC,ZKP-proxy} × 5 = 20, no robot. "335 physical trials" in `conclusion2.md` counts the 20 Arduino-only e2e runs; physical (robot) trials at the corrected instrumentation are 195 (V6+V7); with V5 (latched attack) 315.

### §5.1 ZKP never executed — CHANGED (partially resolved)
A ZKP-cost proxy (two scalar multiplications) now has a measured cost and ran in the trust loop (Phase 2). No proof was verified. Withdrawn items stay withdrawn: 22.85 % security tax; "ZKP incompatible with safety" as empirical; all pre-2026-08-11 ZKP latencies. Reframed factor is still "verification cycle time": 120 vs 232 ms loop period; eviction ratios V7/V6 at α = .5/.3/.1 are 1.72/1.76/1.92 vs period ratio 1.93.

### §5.2 64-byte CLT — STILL WITHDRAWN
`zkp_clt_profiler.ino` never existed in git (`git log --all -- '*clt*'` empty): UNTRACED file. The new profile has sd 0.21 ms (CV 0.09 %): still no variance to "compress". Contaminated files unchanged since 08-07: `conclusion.md` §1, `master_research_summary.md`, `empirical_conclusions.md`, `outline_v2.md` §4.3, `experimental_pivots.md` Pivot 2, `docs/master.md` §4.2, `docs/thesis_conclusions.md`, both `docs/luke pepin - Thesis Outline*.md`.

### §5.3 Category 0 — PARTIALLY RESOLVED
Firmware comments now read "Trigger Category 2 Halt" (lines 140, 197; changed in 6db79e0). No Category 0 path exists: no EI0/EI1 pin, no relay-power control (grep of firmware/scripts/src: zero hits). Still-wrong text: `gaps.md` §4 ("Category 0 Protective Stop"), `conclusion.md` §3, `master_research_summary.md`, `outline_v2.md` §6.4, `audit/system_architecture.md`, `docs/master.md` §6.2 (mixes Cat 0 STO and Cat 2), `docs/thesis_conclusions.md`, `docs/mermaid.md`, `docs/system_architecture.md`, `running.md`, `analyze_distributed_swapover.py` line 43. Wiring per Luke (2026-09-07): D12 drives both SI0 and SI1 in parallel through the optocoupler block — one GPIO, one signal. Any C192A4 disagreement therefore arises in the optocoupler/wiring, not in firmware, and `docs/master.md` §6.2's "firmware transitions both GPIO pins synchronously … <20 ms" describes hardware that was never built (only `cloud_edge_cloud_failback.ino` drives pins 5/6, and it is a print-only demo).

### §5.4 Observed power — STILL TRUE
No new power analysis. `final_lab_plan.md` and `empirical_conclusions.md` still make the circular argument.

### §5.5 ISO 13849-1 500 ms — STILL TRUE (UNTRACED)
Nothing in the repo sources 500 ms or 400 ms to a standard, a UR document or a risk assessment.

### §6.1 Outage factor not implemented — RESOLVED (01a0971, 2026-08-11 18:43 EDT)
Firmware lines 226-227: `else if (input_buffer == "RECOVER") { attack_mode_active = false; }` — clears the attack without touching `trust_score`. Logger lines 216-222 send `RECOVER` at the end of the outage and clear its own flag (logged `attack_flag_ms` now 270/525/1035/2055/3025/5045 for nominal 250/500/1000/2000/3000/5000). Outage sweeps re-run: V6 (120) and V7 (75). Outage duration now varies observably (stop tables above). H1' as stated in `empirical_conclusions.md` remains withdrawn for V4/V5; for V6/V7 the correct statement is: outage duration determines *whether* eviction occurs (threshold n(α)·T_cycle) and, above threshold, has no effect on latency.

Residual: after eviction the safety pin is never re-raised (only a JSON reconfigure sets it HIGH, lines 99/250). Recovery of the robot is by the orchestrator's Dashboard "unlock protective stop / play" (`run_campaign.py` lines 27-40) after the next trial's reconfigure. So "auto-resumes on signal restoration" (§5.3) is never exercised by the campaign; the firmware latches by design.

### §6.2 validate_trial rejects non-stop trials — RESOLVED (01a0971)
`run_campaign.py` lines 45-85 return `(attack_fired, stop_occurred, min_trust)`; validity is `attack_fired` alone (line 166-167). Non-stop trials are kept and summarised to `sub_eviction_summary.csv`. Residual: `stop_occurred` there is the logger's `trust<=30`, which under-counts (see §3).

### §6.3 Hold-down unbounded — CHANGED: not implemented anywhere
No hold-down, suspension or CPU-busy gate exists in any firmware or script (`grep -i hold` → 0 hits in code). The mechanism is prose-only (`gaps.md` §5 added 01a0971, `master_research_summary.md`, `audit/system_architecture.md` mermaid). The built firmware has the opposite property: under `ATTACK` trust is forced to 0 regardless of CPU state, and the exec-time penalty path (`> 400 ms`, `> 150 ms`) never fires because the workloads sit ~40 % below the thresholds. The real, code-traceable denial-of-safety in the built system is different: the penalty is driven entirely by the Pi's `ATTACK` serial signal; a silenced or compromised Pi leaves trust at 100 forever, and the firmware's own "verification" can never fail. Draft 2's hold-down model should be written as a *proposed* mechanism, not a defect in shipped code.

### §6.4 Sentry fixed timer — RESOLVED in firmware (01a0971), demo path unchanged
`sentry_node.ino` lines 61-78: `INITIATE_REJOIN` is emitted only after `K_passes_required` consecutive `CLOUD_UP` events **and** `stable_duration >= DWELL_MS`; state becomes `CLOUD` only on `REJOIN_CONFIRMED` (81-84); `CLOUD_DOWN` resets the counters (52-54). Pi side (`run_cloud_failover_sweep.py`): probe = HTTP GET with 200 + JSON `status:"ok"` required (70-83); `simulate_rejoin_handshake()` re-probes before `REJOIN_CONFIRMED` (85-90, 219-230). This is the dwell-plus-verified-connectivity design, in code. Limits: the "cloud" is a localhost dummy on the same host (line 67); no robot, no crypto node, no motion; the sweep script ran on the Windows PC (`COM32`). The robot-side demo (`run_swapover_expansion.py`) still implements the §6.4 defect verbatim (algo=CLOUD, alpha=1.0, `start_robot_motion()` before any check, lines 137-143) and is now protocol-incompatible with the sentry firmware; it and its 2026-08-10 log are demo-only.

### §6.5 (new) Joint logger drops firmware telemetry lines
`joint_logger_node.py` lines 148-161 (unchanged since 226e45f, 2026-07-29): `reset_input_buffer()`; `sleep(0.01)`; non-blocking `readline()`; lines not entirely inside the 10 ms window are discarded. Measured capture of the first n(α)+2 decay steps: 0.78–0.92 mean, 0.50 minimum, in every campaign V4–V7. The eviction crossing line was missed in 5/44 (V7), 16/73 (V6), 26/120 (V5) logged stops; 8 further stops were missed entirely (V6 7, V7 1). Effects: +1-cycle late bias in logged latencies; boundary-cell stop rates under-counted; `min_trust` off by one step; the "75 vs 50" artefact. The e2e block reads lossless and is unaffected.

### §7 Surviving claims
| Claim | Status | Source |
|---|---|---|
| Latency model n(α)·T_cycle + offset | STILL TRUE, strengthened: now validated with a real outage factor at two cycle times (V6/V7, 195 robot trials) and with lossless timing (e2e, 20) | `audit/eviction_v6.csv`, `eviction_v7.csv`, e2e CSV |
| 368 ms URScript mode-switch penalty | **UNTRACED**. Only prose (`presentation_outline.md`, outlines, `master.md`, `experimental_pivots.md`). June/July `deceleration_data_*.csv` logs exist only in git history (commits f927c6f, be601a1, 57fe3c2; deleted 23f5cbc/f2c9923) with no event marker and no analysis script. | — |
| QoS livelock mitigation RELIABLE→BEST_EFFORT | **PARTLY TRACED**. Verifier service time on the Pi: `md1_profiling_serialized_n1000_1785266590.csv` (deleted at f2c9923; `git show 5414336:data/…`): n=1000, mean 9.650 ms, sd 0.163, CV 0.0169 → μ = 103.63/s — matches `master.md` §5.1 and `ns3_md1_ew_sim.cc` line 31. QoS code exists (`supervisor_node.py` 49-50). No before/after measurement of the QoS change and no source for "99.6 % shedding": UNTRACED. H3 timeout-rate report in `archive/docs/H3 Report.md` (ignored) has numbers but no CSV. | history only |
| Physical opto-isolated 24 V intercept halts a live UR5 | STILL TRUE with qualification: 245 physical stops observed (V5 120, V6 80, V7 45) as "commanded trajectory not executed / arm at standstill"; for ECC α ≥ 0.3 and ZKP-proxy α = 0.5 the arm was stationary at the moment of eviction. Active-high fail-safe: by design (`setup()` line 51). | motion columns |
| Randomized queue seed 42 | STILL TRUE, V6/V7 too (`run_campaign.py` 119-123) | |
| Cycle time drives eviction latency | STILL TRUE: 1.93× period → 1.7–1.9× latency | above |

### §8 Document status — STILL TRUE, all files unchanged since ground_truth; additions
No prose file listed in §8 has been edited since 2026-08-11 (`gaps.md` §4 was updated to 224.86 ms in 01a0971 but still says "Category 0" and still calls the proxy "ZKP bootstrapping"). Add: `audit/conclusion2.md` (247 ms, 659 ms, "4/5 boundary", "335 physical trials", "composition confirmed", "unexplained 75"); `docs/master.md` (334.5 ms, CLT, Cat 0/2 mix, dual-GPIO sync claim, 110 ms deceleration, 99.6 %); `docs/thesis_conclusions.md`, `docs/thesis_code_analysis.md`, `docs/final_test_review.md`, `docs/academic_audit_report.md` (historical, describe superseded firmware); `docs/system_architecture.md`, `docs/mermaid.md` (Cat 0); `docs/cloud_edge_cloud_runbook.md` (describes the print-only demo as "proof"); `README.md` (MANET/p*, stale file list).

## Phase 4 — results not in ground_truth.md (all after 2026-08-11 unless noted)

| # | Item | What ran | What it shows | Limitations | Grade |
|---|---|---|---|---|---|
| 1 | ZKP-cost proxy profile (`real_zkp_profiling.csv`) | 300 runs of 2×`uECC_compute_public_key`, fresh host random scalars, DWT timing, Windows host | 224.86 ± 0.21 ms; Gaussian; no drift | fixed-base only; no hash/point-add; 64 MHz assumed (wall-clock corroborated); Pi run not saved | thesis-grade as "cost of the proxy", n stated, repeatable (`run_real_zkp_test.py`) |
| 2 | V6 ECC outage sweep | 120 robot trials, RECOVER firmware, 4 outages × 3 α × 10 | outage threshold n(α)·120 ms; latency above threshold independent of outage; ECC α=.5 max 504.7 ms | logger drops lines (§6.5); boundary cell 250/.5 mis-logged 4→10; arm stationary at eviction for α ≥ .3 | thesis-grade with the motion-based correction |
| 3 | V7 ZKP-proxy outage sweep | 75 robot trials, 5 outages × 3 α × 5 | threshold n(α)·232 ms; α=.5 mean 623 ms, min 515 | n=5; same logger defect; 1000/.3 cell 4→5 | thesis-grade, n=5 stated |
| 4 | e2e composition block | 20 Arduino-only trials, localhost dummy cloud, lossless serial | loop period 120.4 / 232.1 ms; eviction after detection = partial + n(α) cycles; ECC 262/333 ms, proxy 533/549 ms | no robot; detection window ≈ one probe timeout by construction; "predicted" column uses untraced 247/125 ms; identity check is tautological | thesis-grade for cycle period and structure; the "composition confirmed" claim is not a finding |
| 5 | Cloud failover sweep (`cloud_failover_sweep_results.csv`) | 108 configs × 1 run, sentry Arduino + localhost dummy cloud, Windows | detection ≈ 3.3× probe interval for probe ≤ 500 (K-independent); recovery ≈ dwell + ~1–2 s; 0 excess oscillations; 1 false rejoin (probe 1000, K=1, dwell 0, flapping) | produced by the e8632fd revision *before* the parse-failure fix (af59d47): **all 27 probe=1000 rows are corrupt** (detection 0, recovery 0 in 25–26 of 27); n=1 per config; no robot; no crypto node; "unmonitored_motion_ms" is probe-count × interval, not motion | demo-grade; re-run with HEAD script needed for probe=1000 and for n>1 |
| 6 | Sentry firmware rewrite (`sentry_node.ino`, 01a0971) | — | K-pass + dwell hysteresis, confirm-before-CLOUD | not integrated with the crypto node or robot | code exists; demo-grade integration |
| 7 | RECOVER path + validate_trial fix (01a0971) | — | resolves §6.1/§6.2 | pin never re-raised (latching by design) | done |
| 8 | Aug-10 distributed swapover (predates GT, covered by §2/§6.4) | 20 scripted sequences | stub timings only | orphaned script; demo | demo-grade |
| 9 | (audit-derived) telemetry-drop defect §6.5 | — | 10–20 % of lines lost; 8 stops mis-logged | — | instrument caveat, must be stated |
| 10 | (audit-derived) physical-stop cross-tab | motion columns of 315 trials | 0 false stops; 8 missed stops; sub-500 ms stops occurred with a stationary arm | trajectory design puts motion onset 0.5–1 s after attack | thesis-grade caveat |
| 11 | `md1_profiling_n10_*.csv` (08-11) | supervisor_node run | empty | header only | discard |

## Judgment calls I need from Luke before writing v2
1. Use motion-based physical stop as the authoritative stop/no-stop for V6/V7 tables (my recommendation), with the logged `trust<=30` retained as a secondary column?
2. Present e2e loop periods (120/232 ms) as the canonical cycle times, and re-run the proxy profile on the Pi+Arduino at home only as confirmation?
3. Label the 27 probe=1000 rows of the failover sweep as corrupt and exclude, or re-run the whole sweep with the HEAD script before Draft 1?
