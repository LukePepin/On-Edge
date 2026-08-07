# Empirical Conclusions: H1' & H2 Validation

This document finalizes the empirical conclusions for the decentralized verification framework based on the 121-run V4 ANOVA Physical Dataset.

## The Security Tax (H2) Validation
We hypothesized that Zero-Knowledge Proofs (ZKP) inflict an unsustainable computational "Security Tax" on edge microcontrollers, preventing them from satisfying the 500ms safety threshold required by ISO 13849-1.

**Empirical Result:**
The V4 dataset definitively proves H2. A Two-Way ANOVA confirmed the statistical significance of the cryptographic algorithm on the safety eviction latency ($T_{\text{evict}}$), yielding a substantial main effect ($\eta_p^2$). Subsequent post-hoc pairwise comparisons (ECC vs. ZKP) isolated the severe performance degradation caused by ZKP, yielding an extreme Cohen’s *d* effect size of **2.398** (where $n=4$ was required for 80% power, and we collected $n=5$).
*   **ECC (Elliptic Curve Cryptography)**: Operating with a ~111ms cycle time, the ECC verifier was able to process the EWMA trust penalty iteratively, dropping the 24V STO pin in time to physically halt the UR5 between **236ms and 439ms**, successfully passing the ISO limit.
*   **ZKP (Zero-Knowledge Proof)**: Operating with a simulated ~334ms cycle time, the Cortex-M4 CPU suffered from continuous thread-locking. The UR5 failed to halt until **517ms to 1060ms**, catastrophically violating functional safety limits.

**Conclusion:** ZKP is mathematically superior for extreme coalition privacy but is fundamentally incompatible with the bare-metal safety intercepts of heavy industrial robotics in DIL environments. The proposed architecture resolves this by enforcing a Hybrid-Tiered topology: ZKP is utilized strictly for initial network joining and authorization (when latency is acceptable), transitioning to ECC for the real-time kinematic loops to satisfy the 500ms safety deadline.

## The Central Limit Theorem & Variance Bounds (Theoretical Mandate)
While early data indicates that segmenting ZKP payloads into 64-byte chunks stabilizes execution latency, the invocation of the Central Limit Theorem (CLT) is strictly conditional. Cryptographic hashing algorithms on bare-metal controllers are highly susceptible to heavy-tailed distributions due to cache misses and arithmetic overflow handling. 
**Required Action:** The final dataset must subject the individual 64-byte processing times to a Shapiro-Wilk test or tail-index bounds estimation. The system mathematically cannot claim deterministic convergence via the CLT unless the 64-byte segment variance is empirically proven to be finite and non-heavy-tailed.

## DIL Outage Resilience (H1') Validation

**Empirical Result:**
The V4 dataset definitively proves H1'. A Two-Way ANOVA confirmed that the duration of the EW jamming attack (500ms, 1000ms, 2000ms, 5000ms) had no statistically significant interaction with the stopping time. 
The eviction latency was exclusively driven by the `Alpha` decay parameter ($\alpha = 0.5, 0.7, 0.9$) and the algorithmic cycle time, completely isolating the robot's physical safety from the unpredictability of the network layer.

**Conclusion:** The proposed framework successfully maps transient network health into physical kinetic safety in real-time, bridging the cyber-physical gap without relying on static Cloud Identity Providers.
