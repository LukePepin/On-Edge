# FINAL THESIS DEFENSE: EXPERIMENTAL & STATISTICAL ROADMAP

## 1. THE H1\' CENTRALIZED BASELINE (THE CLOUD TIMEOUT)
*Goal: Empirically prove centralized architectures fail under DIL conditions to establish 50% MTTR reduction.*
- [ ] **Execution:** Deploy simulated Identity Provider (IdP) natively on the LAN. **DO NOT** use WSL2 (NAT firewalls will drop UDP multicast discovery).
- [ ] **Degradation:** Use Linux Traffic Control (\	c\) and \iptables\ to inject highly controlled, randomized packet loss sweeping from **0% to 30%**.
- [ ] **Measurement:** Log the absolute time delta from connection loss to the system-wide involuntary safety stop.

## 2. PHASE 3.5 KINEMATIC DECELERATION (THE PHYSICAL BYPASS)
*Goal: Physically prove <500ms ISO 13849-1 safety compliance.*
- [ ] **Execution:** Run the UR5 50Hz kinematic loop.
- [ ] **Injection:** Send a massive 256-byte payload to intentionally choke the Cortex-M4 and drag the EWMA Trust Score (Γ) below the 30.0 eviction threshold.
- [ ] **Measurement:** Capture 9-axis IMU telemetry. Fuse the data to strip gravitational noise.
- [ ] **Integration:** Mathematically integrate the acceleration curve (v(t)=v_0 + ∫ a(t)dt).
- [ ] **Proof:** Irrefutably prove the time delta between Γ < 30.0 and absolute zero physical velocity is ≤ 500ms.

## 3. PHASE 3.7 NS-3 DROPTAILQUEUE CALIBRATION (THE SWEEP)
*Goal: Ground the NS-3 simulation sweeps in physical hardware limits.*
- [ ] **Execution:** Explicitly calibrate the NS-3 DropTailQueues to exactly match the physical ROS 2 DDS First-In-First-Out (FIFO) queue depth constraints and MTU limits observed during the n=10 boot storm tests.
- [ ] **Validation (H3\'):** Use the calibrated simulation to prove the M/M/1 Queue Saturation Hypothesis: demonstrate that for a 64-byte payload at 50Hz, Livelock (ρ ≥ 1.0) is mathematically inevitable unless the network is sharded across N ≥ 17 edge nodes.

## 4. THE STATISTICAL CAMPAIGN & RUN COUNTS (THE MATH)
*Goal: Generate legally and academically defensible datasets using multiple-comparisons strategy.*
- [ ] **The Pilot Study:** Run exactly 5 trials per experimental condition (totaling 60 trials across matrices) to establish variance estimation.
- [ ] **The Power Analysis:** Use the 60-trial variance to compute the required sample size (N) aiming for a **0.80 statistical power** at a **Cohen\'s d=0.5** (medium effect size).
- [ ] **Execute Remaining Trials:** Run the mathematically calculated remaining number of trials.
- [ ] **The Statistical Analysis:** Evaluate the crossover threshold (p*) for Hypothesis 1 by executing a Two-Way Analysis of Variance (ANOVA).
- [ ] **Family-Wise Error Control:** Apply the **Holm-Bonferroni correction** across all primary tests to prevent alpha inflation and false positives.

---

