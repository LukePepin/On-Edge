# Experimental Design V2 (Deterministic Automation)

This document outlines the revised experimental campaign designed to eliminate statistical variance and directly answer the four core hypotheses of the thesis.

## 1. The Resilience & Crossover Threshold Question ($H_1'$)
* **Objective:** Identify the exact deterministic network-degradation threshold ($p*$) where ZKP outperforms centralized Cloud authentication (OAuth 2.0).
* **Variable:** Deterministic Block-Outage Duration ($T_{outage}$).
* **Method:** Instead of random probabilistic drops, we completely sever the Cloud port (TCP 8080) for a precise duration (e.g., 500ms, 1000ms, 2000ms, 5000ms) during Phase 1.
* **Measurement:** Time elapsed from outage onset to physical Safeguard Stop engagement. We seek the exact $T_{outage}$ where the Cloud system fails but the Edge mesh maintains continuity.

## 2. The Cryptographic "Security Tax" Question ($H_2$)
* **Objective:** Isolate the computational overhead ($T_{recon}$) of ZKP selective attribute disclosure compared to standard ECC verification on the constrained Cortex-M4 edge hardware.
* **Variable:** Cryptographic Algorithm (`ZKP` vs `ECC`).
* **Method:** Performed locally on the Arduino during the static handshake, completely isolated from network jamming.
* **Measurement:** Pure bare-metal CPU cycles (`exec_time_ms`) logged during the authentication payload decryption. Verifying if ZKP fits within the 500ms ISO 13849-1 ceiling.

## 3. The Scalability & Queue Saturation Question ($H_3'$)
* **Objective:** Identify the node density ($n*$) that overwhelms the Edge Supervisor's deterministic service rate ($\mu$), causing an M/D/1 livelock.
* **Variable:** Concurrent Authenticating Nodes ($N$).
* **Method:** Simulated via `iperf` or high-frequency ROS 2 `topic pub` stress testing, blasting the Edge Supervisor with concurrent re-authentication requests (e.g., $N=5, 10, 25, 50$).
* **Measurement:** Queue delay divergence and packet drop rate. Validated against the theoretical M/D/1 queuing model.

## 4. The Partition-Rejoin Stabilization Question (Qualitative Proof)
* **Objective:** Determine the optimal Sentinel Stabilization Window ($W_{sentinel}$) required to prevent route-flapping safety halts.
* **Variable:** Rejoin latency tracking.
* **Method:** Trigger a long-term network partition, allowing the local SQLite ledger to accumulate off-chain work orders. Restore the network and measure the exact time required to flush the ledger to the cloud before operations resume.
* **Measurement:** Ledger sync latency ($T_{sync}$). This empirical data proves that setting $W_{sentinel} > T_{sync}$ safely latches the robot state to prevent rapid toggling.
