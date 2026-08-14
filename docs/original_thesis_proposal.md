# Original Thesis Proposal (Reconstructed)

*Note: This document has been reconstructed from the early architectural state of the repository to serve as the baseline proposal for contrast against the final empirical findings.*

## Title
Decentralized ZKP Authorization Meshes for Industrial Robotics in DIL (Disconnected, Intermittent, Limited) Environments

## 1. Problem Statement
Current industrial robotics and manufacturing execution systems (MES) rely on centralized Cloud Identity Providers (IdP) for cryptographic authorization. In expeditionary or contested environments (such as USMC automated repair cells), active Electronic Warfare (EW) jamming severs the backhaul link. The loss of authorization leases causes robotic cells to trigger involuntary safety shutdowns, halting all kinetic operations.

## 2. Proposed Solution
This research proposes a decentralized edge-compute framework utilizing Zero-Knowledge Proofs (ZKP) to maintain robotic authorization locally. By shifting from "Permission-Based" cloud authority to "Persistence-Based" peer-to-peer authority, robotic cells can continue machining operations under 100% network partitions without compromising Operational Security (OPSEC).

## 3. Methodology & Baseline Theoretical Assumptions
1.  **Phase 1**: Establish a baseline Cloud IdP architecture using ROS 2 and a **Niryo Ned2 (15V educational stepper architecture)**. Simulate DIL jamming to map the baseline failure modes, assuming standard **stochastic M/M/1 queuing models** for network saturation.
2.  **Phase 2**: Introduce a continuous trust-evaluation mechanism (Exponentially Weighted Moving Average) to bridge network health to physical safety limits.
3.  **Phase 3**: Implement Zero-Knowledge Proofs on constrained edge devices (Arduino Nano 33 BLE) to test verification latencies.
4.  **Phase 4**: Physically integrate the framework to benchmark the MTTR (Mean Time to Recovery) and Safety Eviction Latencies against the ISO 13849-1 500ms safety limit.

## 4. Expected Contributions
1.  A novel methodology for mapping probabilistic cryptographic network trust into physical kinetic safety limits.
2.  Empirical benchmarking of the "Security Tax" of ZKP algorithms on constrained ARM Cortex-M4 architectures.
3.  An open-source reference implementation of a hardware-bypass safety intercept for collaborative robotics in contested logistics.
