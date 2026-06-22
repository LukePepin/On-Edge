# Project Schedule & TODOs

## Phase 1 (Weeks 1-4): Baseline Hardware Instrumentation
- [ ] Set up the Raspberry Pi 4 supervisor node with ROS2 Humble and CycloneDDS.
- [ ] Flash and verify standard operation of the 9 Arduino Nano 33 BLE edge nodes.
- [ ] Connect and configure the UR5 (using native ROS 2 drivers) and wrist-mounted IMU.
- [ ] Implement constant-time Schnorr ZKP and ECDSA on Cortex-M4 nodes.
- [ ] Isolate cryptographic latency metrics via DWT_CYCCNT hardware register.
- [ ] Execute 60-trial pilot study to compute statistical variance.

## Phase 2 (Weeks 5-8): Packet-Loss Sweep & Disruption
- [ ] Implement transport-layer network degradation (tc/iptables/Scapy).
- [ ] Execute physical packet-loss sweeps (0-30%).
- [ ] Measure crossover threshold (p*) between centralized OAuth and Edge-First MANET.
- [ ] Measure mechanical emergency-stop deceleration latency via IMU.
- [ ] Conduct partition-rejoin reconciliation testing (trust score synchronization).

## Phase 3 (Weeks 9-12): NS-3 Simulation & Scaling
- [ ] Parameterize NS-3 simulator with baseline arrival rate (λ) captured via transport-layer hooking.
- [ ] Map physical ROS2 CycloneDDS FIFO queue constraints to NS-3 DropTailQueue limits.
- [ ] Run M/M/1 queueing theory extrapolations up to N=100 nodes.
- [ ] Compile data and write thesis findings.
