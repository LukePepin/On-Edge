# Master Research Summary

The proposed decentralized framework is an edge-compute authorization mesh engineered for industrial robotics operating in Disconnected, Intermittent, and Limited (DIL) environments.

## The Operational Threat Model
Modern Industry 4.0 and DoD expeditionary manufacturing (e.g., USMC EARCs) rely heavily on "Cloud-First" Identity Providers (IdP). When tactical Electronic Warfare (EW) jamming or network partitions sever the backhaul link, active robotic machinery involuntarily halts as authorization leases expire. This paralyses production and compromises the physical security of the robotic cell. 

Furthermore, in multi-tenant coalition environments, sovereign nodes cannot broadcast raw identities or telemetry to untrusted local peers without violating Operational Security (OPSEC).

## The Decentralized Solution
The proposed framework transitions robotic control from "Permission-Based" (cloud-tethered) to **"Persistence-Based" (edge-first) authority**. It implements a dual-mesh, decentralized architecture:
1.  **Zero-Knowledge Proofs (ZKP)**: Used selectively for coalition attribute disclosure, allowing sovereign nodes to verify shared robotic trajectories (e.g., G-Code hashes) peer-to-peer without exposing private keys.
2.  **Elliptic Curve Cryptography (ECC)**: Used for the real-time, 50Hz kinematic safety loop.

## The Cyber-Physical Intercept
Because ROS 2 middleware software preemption (e.g., TCP/IP URScript commands) takes over 368ms, the proposed framework completely bypasses the software stack. The Arduino Nano 33 BLE edge nodes are hardwired directly into the UR5's 24V Safety Control Board via a PNP optocoupler block. 

A continuous Exponentially Weighted Moving Average (EWMA) Trust Score grades the network's health. To prevent self-inflicted penalties when local QoS configurations shed traffic, a "Hold-Down" state machine temporarily suspends the EWMA decay parameter while the Cortex-M4 CPU is actively processing a legitimate cryptographic hash. If a malicious packet injection or true DIL jamming attack delays the verification beyond this hold-down window, the Trust Score bleeds down. At $<30.0$, the edge node drops the 24V line, triggering a hardware Category 0 Safeguard Stop in under 500ms (ISO 13849-1 compliant).

## Theoretical Contributions
1.  **The 64-Byte Stabilization Phenomenon**: Provided the segmented ZKP payloads are mathematically proven to possess finite variance via Shapiro-Wilk testing, the Central Limit Theorem compresses execution variance and prevents worst-case RTOS jitter.
2.  **M/D/1 Livelock Mitigation**: Proved that cryptographic processing on single-threaded edge devices creates a processing bottleneck, causing Head-of-Line (HoL) blocking within the **DDS network buffers (CycloneDDS subscription queues) on the Raspberry Pi 4 supervisor**. The proposed architecture mitigates this by aggressively tuning ROS 2 QoS to `BEST_EFFORT` (Depth=1). Crucially, NS-3 simulations of this queueing model must be constrained by the UART serial baud rate bottleneck, not abstract wireless mesh transit limits.
3.  **The Security Tax**: Empirically proved via a 120-run ANOVA (Cohen's d = 2.39 for pairwise comparisons) that *unsegmented* ZKP algorithms violate 500ms safety constraints on bare-metal controllers, mandating the use of the Dual-Mesh ECC fallback or 64-byte CLT segmentation (which successfully stabilizes at ~325ms).
