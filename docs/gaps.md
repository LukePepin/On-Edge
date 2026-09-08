# Theoretical Vulnerabilities and Future Work

Open gaps in the built system and in the design it stands in for. Sections 1-3 are design-level gaps carried from the proposal; sections 4-6 were rewritten on 2026-09-08 to match `ground_truth_v2.md`. Everything here is future work; nothing here is a measured result.

---

## 1. Local UART Serial Unencryption
The Decentralized Edge-Compute Star Topology relies on a Raspberry Pi 4 supervisor to send configuration and attack/recover keywords via a physical UART serial bridge to the Arduino Nano 33 BLE worker nodes. 
**The Gap:** This serial connection is entirely unencrypted (plaintext). If an adversary physically compromises the Pi 4 or intercepts the UART data lines (via side-channel wiretapping), they can completely reconfigure the trust monitor (a configuration message resets trust to 100 and re-closes the safeguard loop) or withhold `ATTACK` so that trust never decays. See section 6.
**Future Work:** The UART bridge must be secured using a hardware-accelerated symmetrical cipher (e.g., AES-128-GCM) or a physically un-clonable function (PUF) to authenticate the physical transmission layer between the Pi and the microcontrollers.

## 2. Static EWMA Alpha Parameterization
The Exponentially Weighted Moving Average (EWMA) Trust Score engine utilizes a statically defined Alpha parameter ($\alpha = 0.5$) to balance historical trust with contemporary execution latency.
**The Gap:** A static Alpha is highly vulnerable in highly volatile, Disconnected, Intermittent, and Limited (DIL) tactical environments. Sudden spikes in ambient Electromagnetic Interference (EMI) or severe atmospheric degradation could cause transient latency spikes. A static Alpha penalizes these environmental fluctuations equivalently to malicious computational attacks, risking elevated False-Positive eviction rates.
**Future Work:** Future iterations must implement an adaptive, reinforcement-learned Alpha that dynamically adjusts its sensitivity based on environmental packet-loss ratios and ambient network volatility, preserving functional safety without unnecessary operational downtime.

## 3. Lack of Token Bucket Admission Control
While the Star Topology physically resolved the M/M/1 Queue Saturation vulnerability (Phase 3.5) by moving cryptography off the primary kinematic processor, the network ingress layer remains unprotected.
**The Gap:** The Raspberry Pi 4 supervisor currently accepts all inbound cryptographic payloads without pre-filtering. In the event of a volumetric Distributed Denial of Service (DDoS) attack, the Pi's TCP socket buffer could saturate, resulting in memory exhaustion or Kernel panics before the malicious packets ever reach the Arduino worker nodes for evaluation.
**Future Work:** Network-layer traffic shaping is required. The implementation of a Token Bucket admission control algorithm or Topology-Embedded Routing Algorithms (TERA) would strictly throttle inbound cryptographic requests, explicitly separating identity-verification streams from deterministic kinetic C2 traffic at the physical switch layer.

## 4. Headroom of ZKP-class verification on 64 MHz-class hardware
The ZKP-cost proxy (two secp256r1 scalar multiplications, the arithmetic of a minimal Schnorr verification without hash, point addition or comparison) costs 224.86 ms (sd 0.21, n = 300) on the Nano 33 BLE without hardware acceleration, and the full trust-loop period with that workload is 232.1 ms (bench, n = 10). No proof was verified; the figure is a lower bound on any real verification.

**The Gap:** with that period, eviction takes n(alpha) x 232 ms plus a partial cycle: 624 ms mean at alpha = 0.5, and no alpha tested reaches a 500 ms mean. (500 ms is a self-imposed design budget; ISO 13849-1 sets no stop time.) A real selective-disclosure verification would add several more scalar multiplications per hidden attribute. Environmental effects (EMI, thermal) were not measured; the 300-run profile shows no drift, but it was taken on a bench.

**Future Work:** (a) measure a complete Schnorr verification and a small selective-disclosure verification on the same device; (b) use the nRF52840's CryptoCell-310 or a faster core and re-measure the loop period; (c) decouple the verification cadence from the trust-update cadence so that the trust loop can run at ECC-class period while verification runs less often; (d) re-profile under interrupt load (serial flood) and across temperature.

## 5. Hold-down suspension (proposed mechanism, not built)
Earlier design documents describe a hold-down state that suspends EWMA decay while the node is busy with legitimate cryptographic work. **No such mechanism exists in the firmware**; under `ATTACK` the trust observation is forced to zero regardless of CPU state. This section analyses the proposal.

**The Gap:** if decay were suspended during verification, an adversary who keeps the node busy with verification requests that look legitimate enough to start would hold trust frozen indefinitely: denial of safety without defeating the cryptography. Any bound on the suspension (N cycles or M ms) trades false stops under legitimate load against exposure under attack.

**Future Work:** analyse the proposal on paper with the measured periods (120.4 / 232.1 ms) and alpha in {0.1, 0.3, 0.5}; simulate; and compare with the watchdog design in section 6. This is Draft 2 material (chapter 5 of the thesis).

## 6. Trust decays only on the supervisor's signal (built system)
In the built firmware the trust observation is 0 when the supervisor has asserted `ATTACK` and 100 otherwise; the workload's own execution-time penalty (thresholds 400 / 150 ms) never fires because the workloads run at about 60 % of those thresholds. The edge node therefore detects nothing on its own.

**The Gap:** a supervisor that is silenced, crashed, or compromised leaves trust at 100 and the safeguard loop closed forever. A compromised supervisor can also send a configuration message that resets trust and re-closes the loop after an eviction. This is the code-traceable denial-of-safety condition in the system as built.

**Future Work:** a wall-clock watchdog on the edge node: if no well-formed heartbeat (or no completed verification of supervisor-supplied data) arrives within W ms, treat the cycle as failed and let trust decay. Predicted stop latency becomes W + n(alpha) x T_cycle + partial cycle. Bench-testable with one Arduino (withhold the heartbeat, time the pin). Configuration messages after boot should require authentication, which folds back into section 1.
