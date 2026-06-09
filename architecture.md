# Architecture & Topology

## 10-Node MANET Cluster Testbed
The physical testbed is constrained to a 10-node localized autonomous robotic cluster, functioning as a Mobile Ad-hoc Network (MANET).

### 1. Supervisor Node
- **Hardware:** 1x Raspberry Pi 4 (Cortex-A architecture, 8GB RAM).
- **Role:** Authentication arbiter, cluster supervisor, and network telemetry collector.
- **Software:** Ubuntu 22.04 LTS, ROS2 Humble, Eclipse CycloneDDS.

### 2. Edge Compute Nodes
- **Hardware:** 9x Arduino Nano 33 BLE (ARM Cortex-M4).
- **Role:** Severely resource-constrained sensors and worker nodes executing cryptographic verification.
- **Cryptographic Stack:** Schnorr Zero-Knowledge Proofs and ECDSA with constant-time implementations. Timing extracted via DWT_CYCCNT hardware registers.

### 3. Robotic Manipulator
- **Hardware:** 1x Niryo Ned2 6-axis collaborative robot.
- **Role:** Physically executes trajectories to measure kinetic disruption (emergency-stop deceleration latency) due to network saturation/authentication failure.
- **Sensors:** Wrist-mounted 9-axis IMU to record deceleration curves.

## Software Architecture
- **Middleware:** ROS2 Humble with Eclipse CycloneDDS.
- **Simulation:** NS-3 discrete-event network simulator to extrapolate the 10-node physical results to N=100 nodes.
- **Network Degradation:** Linux Traffic Control (`tc`), `iptables`, and Scapy for inducing synthetic packet loss and transient network partitions.
