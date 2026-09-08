# Thesis task list (reviewed 2026-09-08 against ground_truth_v2.md; updated 2026-09-08 evening)

Legend: **[orig]** = from the existing Todoist list · **[audit]** = added or changed by the
2026-09-07 audit · p1–p4 = priority · dates are due / hard deadline.
Today is Tue 9/8. Draft 1 is due today; the Sodhi meeting is tomorrow 9/9.

---

## 0. Done 9/8
- [x] Draft 1 skeleton, chapter map, working title (Thesis repo 6218d0a)
- [x] Firmware contradiction reconciled in draft (ch3 §3.1) and On-Edge README
- [x] Draft 1 Methods + Results built (Thesis repo b53c68d and later); tables ruled; system flow diagram
- [x] Limitations paragraph (ch3 §3.10, ch6 §6.2)
- [x] On-Edge cleanup rebased onto the 08-14 reorganization and pushed (517933c)
- [x] `ground_truth_v2.md` authoritative; v1 and the 08-14 decontamination report archived in `audit/`
- [x] `docs/project_summary_review.md` first edition (Parts I–V)
- [x] `docs/claude_project_setup.md` (sources list + advisor prompt)
- [x] Placeholder text in chapters 1, 2, 5, 6

## 0a. Next (before the 9/9 meeting)
- [ ] Read the full PDF once; note anything to raise with Sodhi (agenda drafted: `docs/sodhi_meeting_2026-09-09.md`)
- [x] Claude project re-created
- [ ] Email Draft 1 to Sodhi — moved to during/after the 9/9 meeting

## 0b. Original plan for 9/8 (kept for the record)

1. **[orig, overdue 9/7] Build Draft 1 skeleton** — p1. Use `ground_truth_v2.md` §9 as the results
   spine: one subsection per A/B claim, in table order.
2. **[orig, overdue 9/7 → rescoped] Reconcile firmware contradiction in draft + README** — p1.
   Concretely: (a) the ZKP path is the "ZKP-cost proxy" (2× scalar mult), never a verification;
   (b) one safety output pin D12 feeding SI0+SI1 in parallel, Category 2 Safeguard Stop, no
   Category 0 path; (c) no hold-down exists in code. README additionally: drop MANET/p*, list the
   4 firmware files and 13 scripts actually used (see `audit/phase1_inventory.md` §1, §3).
3. **[orig] Deliver Draft 1 (Methods + Results) to Sodhi** — due 9/8, deadline 9/9, p1.
   Must-include from the audit, or the draft over-claims:
   - cycle times 120.4 / 232.1 ms (e2e), proxy cost 224.86 ± 0.21 ms (n=300) — not 247, not 334
   - V6/V7 tables with the **physical-stop** column (§3.2–3.4); no "4/5 boundary cell"
   - §6.5 logger-drop caveat (+1 cycle late in ≤20 % of trials) stated once in Methods
   - §3.4 statement: sub-500 ms stops occurred with a stationary arm
   - N = 195 (V6+V7) or 315 (V5+V6+V7); never 335
   - ECC vs proxy is a between-campaign contrast
4. **[audit] Draft-1 "limitations" paragraph** — p1, 9/8. Six bullets: proxy ≠ verification;
   Pi-driven ATTACK signal is the only failure input (§6.3); logger drops; motion onset after
   attack; failover sweep demo-grade; 500/400 ms are design budgets (§5.5).

## 1. Writing (drafts)

- **[orig] Triage Sodhi's Draft 1 feedback into revision list** — 9/18, p2.
- **[DONE 9/8, superseded] Propagate ground_truth_v2 §8 corrections** — the contaminated files were deleted instead (cleanup commit 517933c); only `docs/gaps.md` §4–5 still needs a rewrite (proxy wording, Cat 2, hold-down as proposed).
  Rewrite: `audit/conclusion.md`, `audit/conclusion2.md`, `audit/master_research_summary.md`,
  `audit/empirical_conclusions.md`, `audit/outline_v2.md`, `audit/system_architecture.md`,
  `audit/gaps.md` §4–5, `audit/experimental_pivots.md` (Pivots 2, 4, 7, 8), `docs/master.md`,
  both `docs/luke pepin - Thesis Outline*.md`, `docs/thesis_master_outline.md`,
  `docs/system_architecture.md`, `docs/mermaid.md`, `running.md`.
  Archive (do not rewrite): `audit/final_lab_plan.md`, `audit_checklist.md`,
  `docs/thesis_conclusions.md`, `docs/thesis_code_analysis.md`, `docs/final_test_review.md`,
  `docs/academic_audit_report.md`, `docs/cloud_edge_cloud_runbook.md`.
  Leave: `audit/original_thesis_proposal.md`.
- **[DONE 9/8]** `ground_truth_v2.md` is the single reference; v1 archived in `audit/`.
- **[orig → audit rescoped] Draft 2 (unified model + hold-down)** — deadline 10/10, p2.
  Hold-down must be written as a *proposed* mechanism (§6.3: nothing in code); use cycle times
  120 / 232 ms, not 125 / 247.
- **[orig] Draft 3 (full thesis)** — deadline 11/11, p2.
- **[audit] Decide fate of 368 ms URScript figure** — p2, before Draft 2. UNTRACED (§7). Either find
  the June/July analysis output or state the bypass motivation qualitatively.
- **[audit] Decide fate of QoS "99.6 % shedding" and RELIABLE→BEST_EFFORT claim** — p2, before
  Draft 2. Service rate μ = 103.63/s is traceable (§7); the mitigation effect is not.
- **[audit] Decide fate of "≈110 ms mechanical deceleration / EKF"** in `docs/master.md` §6.3 —
  p3. UNTRACED; drop unless an IMU analysis is produced.

## 2. Analysis / research

- **[orig → audit rescoped, STARTED 9/8] Derive unified time-to-safe-state closed form** — due 9/10, p1. `audit/closed_form_check.py` compares (n(α)+½)·T against V6/V7/bench; result and residual terms ready to write into ch5 §5.2.
  Anchor on the measured structure (§3.5): `T_evict ≈ n(α)·T_cycle + U(0, T_cycle) + t_serial`,
  plus detection window (probe interval × count) and mechanical deceleration (currently
  UNTRACED — treat as a symbol). Validate against `audit/eviction_v6.csv`, `eviction_v7.csv`,
  and the e2e CSV; the +1-cycle logger bias (§6.5) is the residual to explain.
- **[audit] Pi-side ZKP-cost-proxy profile** — p1, this week (Pi out of storage). Flash
  `zkp_real_profiler.ino`, run `run_real_zkp_test.py` with `PORT='/dev/ttyACM0'`, save as
  `data/real_zkp_profiling_pi.csv`, commit. Expect 224.9 ± 1 ms. Closes ground_truth_v2 §10 Q1.
- **[audit] Re-run cloud failover sweep** — p2, this week; needs only the sentry Arduino + PC or
  Pi. Flash `sentry_node.ino` (HEAD), run `run_cloud_failover_sweep.py` (HEAD → `…_v3.csv`),
  n ≥ 3 per configuration. Replaces the file with 27 corrupt probe=1000 rows (§6.7). Until
  done, the sweep is demo-grade.
- **[audit] Archive the 247 ms constant** — p2, 9/10. Note in `audit/conclusion2.md` header; do not
  cite `predicted_total_ms` / `residual_ms` from the e2e CSV.
- **[orig → audit rescoped] Formalize hold-down adversary model + simulate** — Draft 2, p2. Two
  models, both analytical/simulated: (a) the proposed hold-down (unbounded suspension);
  (b) the built system's actual gap — trust driven only by the Pi's ATTACK signal (§6.3).
  Cycle times 120 / 232 ms.
- **[orig] Design wall-clock watchdog mitigation + derive predicted stop latency** — Draft 2, p2.
  Firmware-side watchdog on serial silence addresses (b) above directly.
- **[orig] Profile ECC / ZKP-cost proxy on lunchbox x86 PC** — p3. Same `run_real_zkp_test.py`
  harness cannot be used (DWT is Cortex-M); needs a host-side timer wrapper like
  `uecc_wrapper.c`.
- **[audit] Optional: moving-arm stop campaign** — p3, only if UR5 access returns. Fire the attack
  mid-trajectory (t ≈ 2–4 s into phase 2) so sub-500 ms evictions hit a moving arm (§6.6). Also
  fix the logger read loop (§6.5) before any re-run: accumulate bytes, split on newline.
- **[audit] Optional: lossless-logger patch** — p3, tied to the above; do not modify until
  after the current data set is frozen.
- **[orig] Parked (p4): ns-3 failover sim, ML trust scoring, multi-node mesh.**

## 3. Presentation

- **[orig] Cloud-context slides (cloud authority role + control handoff)** — p3. Use the
  sentry state machine (§6.4) as built; label the sweep demo-grade until re-run.
- **[orig] Encryption-cost baseline slide** — p3. Numbers: 111.5 ms keygen, 224.9 ms proxy,
  120 / 232 ms loop; 9.65 ms `uECC_verify` on the Pi 4.
- **[orig] Survey of existing baselines/architectures for comparison slide** — p3.
- **[audit] One slide: "what the physical evidence shows"** — p3. The 245 physical stops as
  "trajectory not executed", and the stationary-arm caveat, before a committee member finds it.

## 4. Admin / defense

- **[orig] Sodhi meeting 9/9** — p1. Subtasks: chair confirmation (Rosseau), 12/11 date,
  committee (Maier-Speredelozzi, Sun), Draft 1 scope/turnaround, workshop paper venue,
  Wednesday absences, Industry 4.0 certificate.
  **[audit] add:** (a) agree the term "ZKP-cost proxy"; (b) agree that sub-500 ms stops were
  stationary-arm stops and how to present that; (c) whether to spend time on the failover re-run
  vs. writing.
- **[orig] Schedule defense with full committee** — deadline 11/11, p1 (blocked on Sodhi + Rosseau).
- **[orig] Nomination for Graduation** — due 10/12, deadline 10/14, p1.
- **[orig] Request to Schedule Oral Defense form** — due 11/17, deadline 11/20 (verify vs 11/15), p2.
- **[orig] Defense paperwork + room booking** — undated, p3.
- **[orig] Submit final thesis** — due 12/15, deadline 12/18, p1.

## 5. Repo hygiene (small, do when convenient)

- **[audit]** Delete or move `data/md1_profiling_n10_*.csv` (header-only) — p4.
- **[audit]** Mark `scripts/run_swapover_expansion.py`, `scripts/analyze_distributed_swapover.py`,
  `scripts/analyze_v6_data.py`, `firmware/cloud_edge_cloud_failback/` as demo/obsolete in
  `src/README.md` or move to `archive/` — p4.
- **[audit]** Recover `md1_profiling_serialized_n1000_1785266590.csv` from git
  (`git show 5414336:data/…`) into `data/` if the μ = 103.63/s figure is cited — p3.
- **[DONE 9/8]** audit outputs, v2, todoist committed.
- **[DONE 9/8]** `docs/gaps.md` §4–6 rewritten (proxy headroom; hold-down as proposed; supervisor-signal gap + watchdog).
- **[audit]** Deepen `docs/project_summary_review.md` where the advisor sessions find thin spots (Part I ch. 4–5 crypto, Part IV ch. 27) — p3, rolling.

---

### Pressure points (updated)
Draft 1 is due today with the handoff tomorrow; both "due 9/7" items are overdue and are
prerequisites for it. The Pi-side profile and failover re-run are the only bench work that
can still change a number in Draft 2; everything else is writing. The closed-form derivation
(9/10) should be built on §3.5's measured structure rather than started from scratch.
