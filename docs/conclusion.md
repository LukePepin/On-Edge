# Master Conclusion: Decentralized Edge Verification Framework

This document synthesizes the definitive academic and mathematical conclusions established throughout the physical hardware-in-the-loop (HIL) integration of this thesis. It traces the chronological resolution of each vulnerability discovered during the integration of Zero-Knowledge Proofs (ZKP) and Elliptic Curve Cryptography (ECC) into industrial robotic safety loops.

---

## 1. The 64-Byte Stabilization Phenomenon (Phase 2) — WITHDRAWN
This section previously claimed that segmenting the ZKP payload into 64 independent byte-level constraints invoked the **Central Limit Theorem (via the Berry-Esseen theorem)**, compressing execution time into a deterministic 301–346 ms window and satisfying an "ISO 13849-1 500ms safety threshold."

That claim is withdrawn in full (see `ground_truth.md` §5.2). The firmware never executed 64 independent constraints: the "ZKP" workload was a single loop executed three times, and its measured standard deviation was 0.17 ms across 300 cycles — a deterministic workload with no variance to compress. (Note also that the variance of a sum of n independent terms *grows* as n·σ²; only the coefficient of variation shrinks.) Separately, ISO 13849-1 sets no stop-time ceiling; the 500 ms figure is a self-imposed design budget.
**Conclusion:** None retained from this section.

## 2. Queue Saturation & The QoS Livelock (Phase 3.5)
Integration with the UR5 robotic kinematic stream (50Hz) exposed a Denial-of-Service (DoS) failure mode. When a single-threaded processor handles heavy cryptographic payloads alongside real-time kinematic data, the verification queue backs up: the node suffered Head-of-Line (HOL) blocking, dropping critical kinematic safety packets. The specific queueing-theory figures previously cited here (Service Rate $\mu$ = 3.10 packets/second, Traffic Intensity $\rho$ = 16.14, M/M/1 unbounded growth) do not trace to retained data and are withdrawn [WITHDRAWN — see ground_truth.md].
**Conclusion:** The livelock is real and was resolved as an engineering fix: retuning ROS 2 QoS from `RELIABLE/KEEP_ALL` to `BEST_EFFORT/KEEP_LAST(1)`, and separating cryptographic processing from real-time kinematic routing in the final topology. The queueing-theory characterization is not a retained result.

## 3. The Safeguard Stop & The C192A4 Latching Fault (Phase 4.3)
Bridging the 3.3V microcontroller logic to the 24V industrial safety panel of the UR5 produced the hardware safety intercept. When the EWMA Trust Score detected an anomaly and dropped the 24V PNP signal to the `SI0` and `SI1` ports, the robot initiated a Safeguard Stop — a **Category 2** stop that auto-resumes on signal restoration. (Earlier drafts described this as a designed "Category 0" or "Latching Cryptographic Halt"; that is incorrect. Category 0 requires the `EI0`/`EI1` emergency inputs or cutting power to the safety relays.)

However, because industrial dual-channel safety monitoring detects sub-millisecond discrepancies between channels, the briefest temporal misalignment in signal restoration latched a **C192A4 Safeguard Stop Disagreement** fault into the UR5 controller.
**Conclusion:** The latching behavior is a genuinely observed *timing fault on restoration*, not a designed feature. Once the C192A4 fault latches, the controller's safety-fault state performs a **Category 0 halt** that holds until a manual reset (`ground_truth.md` §5.3, amended 2026-08-14). In practice it forces a "Human-in-the-Loop" reset after a trust collapse, but the designed stop itself is a Category 2 safeguard stop, fail-safe on power loss.

## 4. The Decentralized Verification Framework (Phase 5 Capstone)
To resolve the single-threaded queue saturation, the final architecture deployed a **Decentralized Edge-Compute Star Topology** over USB serial. A Raspberry Pi 4 Supervisor Node orchestrated the campaign and logged telemetry over the physical serial JSON UART bridge; independent Arduino Nano 33 BLE worker nodes executed the localized cryptographic verification loops. (The Pi is not a cryptographic "Vault" and does not hash the 50Hz kinematic stream; verification runs on the Arduinos.)

During a 20-repetition scripted swapover sequence, the edge nodes hot-swapped from out-of-band "ZKP" bootstrapping to continuous ECC verification.
- **"ZKP"-path mean cycle time:** 334.66 ms — this was a **stub** (three ECC keypair generations tuned to sit under a self-imposed 400 ms bootstrap budget), not a ZKP measurement. The real ZKP proxy, profiled later, runs at 224.86 ms (sd 0.21, p95 225.18, 300 runs).
- **ECC mean cycle time:** 111.54 ms (~123 ms loop period).

The swapover log contains $N=1940$ crypto cycles (1640 ECC + 300 stub); 1940 is a cycle count, not a trial count. The trial campaigns total 335 physical trials: 120 (V5) + 120 (V6) + 75 (V7) + 20 (end-to-end).
**Conclusion:** The framework kept the robot operating through simulated network loss in the swapover sequence, and the measured cycle times feed the validated latency model. Claims of "mathematically unassailable" variance proof and guaranteed false-positive-free operation are not retained.
