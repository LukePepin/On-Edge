# On-Edge: Thesis Project Execution Plan

## Week 1: Infrastructure Initialization and Network Baseline
- [x] **Phase 1.1: Supervisor OS Provisioning**
  - Flash Ubuntu 22.04 LTS natively onto the Raspberry Pi 4.
  - Install ROS 2 Humble Hawksbill.
  - Configure mDNS hostname (`on-edge-pi.local`) for dynamic lab network access.
- [x] **Phase 1.2: Micro-ROS Build Environment**
  - Initialize PlatformIO environment for the Cortex-M4 edge nodes.
  - Configure `micro_ros_platformio` library dependencies.
- [x] **Phase 1.3: Agent-Client Broker Deployment**
  - Deploy the Micro XRCE-DDS Agent natively on the Raspberry Pi 4 (Docker moved to future work).
- [x] **Phase 1.4: Edge Node Enrollment**
  - *Pivot Note: micro-ROS was dropped due to Arduino Mbed OS RAM constraints (Nano 33 BLE). We will use a pure Serial-JSON bridge instead, or pivot hardware entirely to an ESP32 if native ROS 2 DDS is required later.*
  - Flash Nano 33 BLEs with a basic raw Serial JSON publisher script.
  - Bind them to the Raspberry Pi 4 agent via a Python Serial-to-ROS bridge node.
  - Verify continuous uncorrupted data streams via `ros2 topic echo`.
- [x] **Phase 1.5: Synthetic Network Degradation**
  - Deploy Linux Traffic Control (`tc`) and Scapy scripts on the wired backend.
  - Induce artificial 15% packet-loss rate and capture baseline with `tshark`.

## Week 2: Bare-Metal Cryptography and Cycle Profiling
- [ ] **Phase 2.1: Constant-Time Cryptography Porting**
  - Integrate custom Schnorr ZKP and standard ECDSA libraries.
  - Verify implementations compile without overflowing the 256KB SRAM.
- [ ] **Phase 2.2: Hardware Register Initialization**
  - Expose ARM Core Debug registers (DWT_CYCCNT) for cycle counting.
- [ ] **Phase 2.3: Latency Profiling Wrapper Construction**
  - Construct C++ timing wrapper around cryptographic functions.
  - Extract execution latency with 15.625-nanosecond precision.
- [ ] **Phase 2.4: Selective Disclosure Sweeps**
  - Execute the 60-trial pilot study.
  - Incrementally increase payload size (1 to 256 bytes) and map to CPU clock cycles.
- [ ] **Phase 2.5: Trust Score Logic Integration**
  - Implement EWMA trust score logic using integer arithmetic.
  - Evict simulated Byzantine node dropping below 0.3 exclusion threshold.

## Week 3: Robotic Kinematics and UR5 Integration
*(Note: Phases adapted from original Niryo proposal to reflect the UR5 ROS 2 upgrade)*
- [ ] **Phase 3.1: UR5 Baseline Configuration**
  - Connect the Universal Robots UR5 to the local management network.
  - Verify baseline movement via the Teach Pendant.
- [ ] **Phase 3.2: Native ROS 2 Integration**
  - Install and launch the `Universal_Robots_ROS2_Driver` on the Supervisor.
  - Verify ROS 2 Humble can successfully publish `JointTrajectory` commands to the UR5.
- [ ] **Phase 3.3: IMU Telemetry Integration**
  - Mount the 9-axis IMU directly to the wrist of the UR5.
  - Route IMU data through a dedicated Arduino edge node to the ROS 2 environment.
- [ ] **Phase 3.4: Emergency-Stop Injection**
  - Develop the software trigger simulating an authorization failure/ZKP timeout.
  - Wire trigger to issue an immediate priority HALT command to the UR5 trajectory planner.
- [ ] **Phase 3.5: Deceleration Curve Mapping**
  - Execute rapid trajectories while artificially triggering the E-stop.
  - Plot the physical deceleration curve and verify total latency is below the 500ms ISO fail-safe ceiling.
