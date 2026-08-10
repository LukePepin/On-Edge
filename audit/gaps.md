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
The Phase 5 Capstone proved that Zero-Knowledge Proof bootstrapping executes at a mean of $334.66$ ms, safely under the $400$ ms out-of-band initialization threshold.
**The Gap:** This leaves an operational headroom of exactly $64.97$ ms ($16.2\%$). While mathematically sufficient in a sterile laboratory environment, expeditionary operations routinely experience extreme physical shock, vibration, and EMI that can marginally slow clock cycles or interrupt the RTOS scheduler. If ambient interference consumes this $65$ ms margin, the edge node will fail to initialize the mesh and latch a Category 0 Protective Stop during deployment.
**Future Work:** The cryptographic budget must be expanded. Migrating the worker nodes from the 64MHz Cortex-M4 (Arduino Nano) to a dedicated FPGA or ASIC would drastically accelerate the modular exponentiation required for ZKP, expanding the safety margin from 16% to >80% and immunizing the node against minor environmental timing anomalies.
