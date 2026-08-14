# Empirical Conclusions: H1' & H2 Validation

This document finalizes the empirical conclusions for the decentralized verification framework based on the 120-trial V5 physical campaign (2 algorithms × 4 outage durations × 3 alpha levels × 5 iterations; the project total across V5, V6, V7, and the end-to-end block is 335 trials).

## The Security Tax (H2) Validation
We hypothesized that Zero-Knowledge Proofs (ZKP) inflict an unsustainable computational "Security Tax" on edge microcontrollers, preventing them from satisfying the 500ms stop budget — a **self-imposed design budget**; ISO 13849-1 sets no stop-time ceiling.

**Empirical Result:**
The campaign shows that *verification cycle time* drives eviction latency — the experimental factor is cycle time, not algorithm identity, because the "ZKP" path as run was a stub (three ECC keypair generations timed to ~334.7 ms; real ZKP has since been profiled at 224.86 ms, sd 0.21, over 300 runs). A Two-Way ANOVA confirmed the statistical significance of the cycle-time factor on the safety eviction latency ($T_{\text{evict}}$), yielding a substantial main effect ($\eta_p^2$) and an extreme Cohen’s *d* effect size of **2.398** for the pairwise comparison. (An earlier draft used this observed *d* to argue retroactively that $n=4$ sufficed for 80% power; that observed-power justification is circular and is withdrawn — the effect size is reported descriptively.)
*   **ECC (~111.5ms cycle time)**: The verifier processed the EWMA trust penalty iteratively, dropping the 24V safety pin and halting the UR5 between **291ms and 505ms** at the fastest setting (α = 0.5, mean 374.3ms). The observed maximum of 504.9ms sits just *over* the 500ms design budget; slower α settings exceed it by wide margins.
*   **"ZKP" stub (~334.7ms cycle time)**: The slower cycle delayed eviction to **738ms–1300ms** at α = 0.5 (mean 898.8ms), well outside the design budget. The ~3× slower path evicts ~2.8× later, exactly as the latency model predicts.

**Conclusion:** Slow verification cycles are incompatible with tight stop budgets on bare-metal safety intercepts. For real ZKP this is a *model prediction from profiling*, not yet a measured trial outcome: at ~247ms/cycle, the fastest possible eviction is ~600–700ms (α = 0.5) — cheaper than the stub suggested, still outside the 500ms budget at every α tested. The architecture therefore enforces a Hybrid-Tiered design: ZKP strictly for initial network joining and authorization (when latency is acceptable), transitioning to ECC for the real-time kinematic loops.

## The Central Limit Theorem & Variance Bounds — WITHDRAWN
The claim that segmenting ZKP payloads into 64-byte chunks stabilizes execution latency via the Central Limit Theorem is withdrawn entirely (see `ground_truth.md` §5.2). The firmware never executed 64 independent byte-level constraints — the workload was one loop run three times — and its measured standard deviation (0.17–0.21 ms) shows a deterministic workload with no variance to compress. No Shapiro-Wilk or tail-index follow-up is required, because there is no stabilization phenomenon to validate.

## DIL Outage Resilience (H1') Validation — Withdrawn and Replaced by the V6 Result

**Original claim (withdrawn):** An earlier draft reported that outage duration (500ms, 1000ms, 2000ms, 5000ms) had no statistically significant effect on stopping time, with eviction driven exclusively by the `Alpha` decay parameter and cycle time. That null result was an **instrumentation artifact**: the firmware had no path to clear `attack_mode_active` (no RECOVER command existed), so trust decayed to eviction regardless of the nominal outage — the factor was never observable. (The same draft also misstated the alpha levels as 0.5/0.7/0.9; the levels actually run were **α = 0.1, 0.3, 0.5**.)

**Replacement (V6, 120 trials, after the RECOVER fix):** Outage duration *governs* eviction once it is observable. A stop occurs iff the outage spans the required cycle count: per 10 trials at 250/500/1000/2000ms, stop rates were 0/0/0/10 (α = 0.1), 0/9/10/10 (α = 0.3), and 4/10/10/10 (α = 0.5), with the boundary cells (4/10, 9/10) decided by cycle-boundary jitter. The cycle period was independently confirmed at ~125ms.

**Conclusion:** The framework maps transient network health into physical kinetic safety in real-time, and the eviction decision is jointly governed by outage duration, the `Alpha` decay parameter, and the verification cycle time — exactly as the latency model predicts.
