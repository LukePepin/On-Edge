# On-Edge: Thesis Project Execution Plan

## Phase 1: Infrastructure Initialization and Network Baseline
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

## Phase 2: Bare-Metal Cryptography and Cycle Profiling
- [x] **Phase 2.1: Constant-Time Cryptography Porting**
  - Integrate custom Schnorr ZKP and standard ECDSA libraries.
  - Verify implementations compile without overflowing the 256KB SRAM.
- [x] **Phase 2.2: Hardware Register Initialization**
  - Expose ARM Core Debug registers (DWT_CYCCNT) for cycle counting.
- [x] **Phase 2.3: Latency Profiling Wrapper Construction**
  - Construct C++ timing wrapper around cryptographic functions.
  - Extract execution latency with 15.625-nanosecond precision.
- [x] **Phase 2.4: Selective Disclosure Sweeps**
  - Execute the 60-trial pilot study.
  - Incrementally increase payload size (1 to 256 bytes) and map to CPU clock cycles.
- [x] **Phase 2.5: Trust Score Logic Integration**
  - Implement EWMA trust score logic using integer arithmetic.
  - Evict simulated Byzantine node dropping below 0.3 exclusion threshold.

## Phase 3: Robotic Kinematics and Software Preemption (UR5 Integration)
- [x] **Phase 3.1: UR5 Baseline Configuration**
  - Connect the Universal Robots UR5 to the local management network.
  - Verify baseline movement via the Teach Pendant.
- [x] **Phase 3.2: Native ROS 2 Integration**
  - Install and launch the `Universal_Robots_ROS2_Driver` on the Supervisor.
  - Verify ROS 2 Humble can successfully publish `JointTrajectory` commands to the UR5.
- [x] **Phase 3.2b: Windows PC Cloud Supervisor Networking**
  - *Pivot Note: WSL2 internal networking proved too unstable for real-time ROS 2 RTDE streams. We will abandon Windows and commandeer a native high-power Linux machine (or a secondary Raspberry Pi) to act as the Cloud Supervisor.*
- [ ] **Phase 3.3: IMU Telemetry Integration**
  - Mount the 9-axis IMU directly to the wrist of the UR5.
  - Route IMU data through a dedicated Arduino edge node to the ROS 2 environment.
- [x] **Phase 3.4: Emergency-Stop Injection**
  - Develop the software trigger simulating an authorization failure/ZKP timeout.
  - Wire trigger to issue an immediate priority HALT command to the UR5 trajectory planner.
- [x] **Phase 3.5: Multi-Threaded Integration and Kinematic Deceleration Telemetry**
  - **[SAFETY CRITICAL]: Unmount the robot from the desk and place it in the center of the room to ensure a completely clear 360-degree range of motion.**
  - [x] Objective 1: Implement Edge-Computed Kinematic Stream (`forward_position_controller`).
  - [x] Objective 2: Create a faster 50Hz kinematic script simulating a pick-and-place "cut" motion.
  - [x] Objective 3: Multi-Threaded Node Integration (Run Trust Monitor + Kinematic Stream concurrently).
  - [x] Objective 4: Mathematical Trigger Logic Implementation (EWMA Thresholding).
  - [x] Objective 5: Stream Preemption and Emergency Halt Injection.
  - [x] Objective 6: IMU Data Fusion and CSV Telemetry Logging.
  - [x] Objective 7: Latency Ceiling Mathematical Verification (Verify latency < 500ms ISO fail-safe ceiling).
  - *Empirical Findings: During Phase 3.5, two critical vulnerabilities were discovered:*
    1. *Queue Saturation:* A single-threaded Arduino blocked the network FIFO queue for 610ms, proving physical CPU execution cannot out-scale queue saturation (HOL blocking).
    2. *Structural Deceleration Overhead:* Using software preemption (`stopj`), the UR5 controller consumed >750ms just to switch from `forward_position_controller` to the URScript interpreter, rendering the software path mathematically incapable of beating the 500ms safety ceiling.

## Phase 4: The Hardware IT/OT Bypass (Current Active Phase)
- **[SAFETY CRITICAL] The Electrical Reality Check:** The 3.3V Arduino cannot wire directly into the 24V UR5 control box. 
- [ ] **Phase 4.1: Hardware Procurement & Photography**
  - Procure a high-speed 3.3V-to-24V opto-isolated solid-state relay.
  - Revisit hardware integration to capture high-quality photos for IP presentation slides.
- [ ] **Phase 4.2: Dual-Channel Actuation Wiring**
  - Wire the opto-isolated relay across the UR5 Safeguard Stop terminals for true Category 0/1 hardware bypassing.
- [ ] **Phase 4.3: Edge Node Firmware Integration**
  - Update Arduino C++ firmware to drop the GPIO pin LOW the microsecond the EWMA trust score falls below Γ=30.0.
- [ ] **Phase 4.4: Physical Extrapolation Testing**
  - Execute the physical test to completely circumvent the ROS 2 software stack and extract the sub-500ms CSV telemetry.

## Phase 5: NS-3 Simulation Extrapolation
- [ ] **Phase 5.1: M/M/1 Queueing Simulation**
  - [ ] Objective 1: Extract baseline service rates (μ) and arrival rates (λ) from the ROS 2 cluster data.
  - [ ] Objective 2: Model the SentryC2 architecture as an M/M/1 queue in NS-3.
  - [ ] Objective 3: Extrapolate node density (N) to N=100 to map strict Livelock saturation thresholds.
  - [ ] Objective 4: Validate Token Bucket admission control algorithms within the simulation.
