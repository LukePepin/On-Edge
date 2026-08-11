# Theoretical Vulnerabilities and Future Work

While the Decentralized Verification Framework successfully achieved the Phase 5 Capstone parameters, rigorous systems-engineering audits reveal several unmitigated vulnerabilities and theoretical gaps. These gaps serve as the foundation for the "Future Work" section of the thesis.

---

## 1. Local UART Serial Unencryption
The Decentralized Edge-Compute Star Topology relies on a Raspberry Pi 4 (the "Vault") to route JSON payloads via a physical UART serial bridge to the Arduino Nano 33 BLE worker nodes. 
**The Gap:** This serial connection is entirely unencrypted (plaintext). If an adversary physically compromises the Pi 4 or intercepts the UART data lines (via side-channel wiretapping), they can completely bypass the mesh cryptography and inject falsified `{"algo": "ECC"}` packets directly into the Arduinos.
**Future Work:** The UART bridge must be secured using a hardware-accelerated symmetrical cipher (e.g., AES-128-GCM) or a physically un-clonable function (PUF) to authenticate the physical transmission layer between the Pi and the microcontrollers.

## 2. Static EWMA Alpha Parameterization
The Exponentially Weighted Moving Average (EWMA) Trust Score engine utilizes a statically defined Alpha parameter ($\alpha = 0.5$) to balance historical trust with contemporary execution latency.
**The Gap:** A static Alpha is highly vulnerable in highly volatile, Disconnected, Intermittent, and Limited (DIL) tactical environments. Sudden spikes in ambient Electromagnetic Interference (EMI) or severe atmospheric degradation could cause transient latency spikes. A static Alpha penalizes these environmental fluctuations equivalently to malicious computational attacks, risking elevated False-Positive eviction rates.
**Future Work:** Future iterations must implement an adaptive, reinforcement-learned Alpha that dynamically adjusts its sensitivity based on environmental packet-loss ratios and ambient network volatility, preserving functional safety without unnecessary operational downtime.

## 3. Lack of Token Bucket Admission Control
While the Star Topology physically resolved the M/M/1 Queue Saturation vulnerability (Phase 3.5) by moving cryptography off the primary kinematic processor, the network ingress layer remains unprotected.
**The Gap:** The Raspberry Pi 4 supervisor currently accepts all inbound cryptographic payloads without pre-filtering. In the event of a volumetric Distributed Denial of Service (DDoS) attack, the Pi's TCP socket buffer could saturate, resulting in memory exhaustion or Kernel panics before the malicious packets ever reach the Arduino worker nodes for evaluation.
**Future Work:** Network-layer traffic shaping is required. The implementation of a Token Bucket admission control algorithm or Topology-Embedded Routing Algorithms (TERA) would strictly throttle inbound cryptographic requests, explicitly separating identity-verification streams from deterministic kinetic C2 traffic at the physical switch layer.

## 4. EMI Susceptibility on ZKP Bootstrapping
The Phase 5 Capstone proved that Zero-Knowledge Proof bootstrapping executes at a mean of $224.86$ ms, safely under the $400$ ms out-of-band initialization threshold.
**The Gap:** While this leaves an operational headroom of $175$ ms ($43.7\%$), this measured figure is a mathematical lower-bound proxy (timing two raw scalar multiplications without the associated hashing and point additions required for a complete Schnorr verification). Real-world Schnorr verification will consume a portion of this margin. Furthermore, expeditionary operations routinely experience extreme physical shock, vibration, and EMI that can marginally slow clock cycles or interrupt the RTOS scheduler. If ambient interference consumes the remaining headroom, the edge node will fail to initialize the mesh and latch a Category 0 Protective Stop during deployment.
**Future Work:** The cryptographic budget must be expanded. Migrating the worker nodes from the 64MHz Cortex-M4 (Arduino Nano) to a dedicated FPGA or ASIC would drastically accelerate the modular exponentiation required for ZKP, expanding the true safety margin to >80% and immunizing the node against environmental timing anomalies.

## 5. EWMA Hold-Down State Machine Suspension
The hold-down state machine suspends EWMA trust decay while the Cortex-M4 is actively computing a legitimate cryptographic hash. This exists so the node does not penalize itself for the latency of its own work.

**The Gap:** the suspension is unbounded. An adversary who can keep the crypto node continuously busy — by flooding it with verification requests that appear legitimate enough to begin processing — holds the trust score frozen indefinitely. The safety stop is never triggered, because the mechanism that detects degraded verification has been placed in suspension by the attack it is meant to detect. This is a denial-of-safety condition: the attacker does not need to defeat the cryptography, only to saturate the processor. It is distinct from the M/M/1 queue saturation vulnerability, which concerns dropped packets rather than a suspended safety mechanism.

**Future Work:** the hold-down must be bounded — capped at N consecutive suspended cycles or M milliseconds of cumulative suspension, after which decay resumes regardless of CPU state. Choosing that cap is a measurable tradeoff between false-positive evictions under legitimate load and exposure window under attack. Because the vulnerability is one of logic and timing rather than kinematics, it can be characterized entirely in simulated multi-node experiments without robot hardware, with a single confirmation run on the physical cell afterward.
