# Experimental Pivots & Engineering Evolution

A chronological map of the major architectural pivots that shaped the decentralized verification framework, justifying the final system topology.

### Pivot 1: Dropping TCP/IP for Physical UART
*   **Initial Design:** We attempted to run `micro-ROS` natively on the Arduino Nano 33 BLE to subscribe directly to the UR5's kinematic topics.
*   **The Pivot:** The Arduino's 256KB SRAM was immediately exhausted by the RTPS DDS abstraction layer, leading to stack-heap collisions and kernel panics. We pivoted to a "Vault & Broker" Star Topology. The Pi 4 runs standard ROS 2 and bridges the hashed telemetry over a physical UART serial line to the bare-metal Arduino.

### Pivot 2: Cryptographic Payload Segmentation
*   **Initial Design:** Evaluating massive, single-constraint ZKP payloads.
*   **The Pivot:** Massive payloads suffered extreme latency spikes (~540ms), triggering false-positive evictions, and the verification workload was restructured. The earlier account of this pivot — that segmenting into 64-byte chunks with independent constraints invoked the Central Limit Theorem and bounded execution between 301ms and 346ms — is **withdrawn** (see `ground_truth.md` §5.2): the firmware never executed 64 independent constraints, and the eventual workload was deterministic (sd 0.17ms). What survives is the engineering lesson that verification cycle time must be controlled and measured; the workloads actually run were ~111.5ms (ECC) and ~334.7ms (the "ZKP" stub).

### Pivot 3: Probabilistic EWMA Trust Decay
*   **Initial Design:** Binary authentication state (authenticated vs. rejected) triggered upon a single dropped packet.
*   **The Pivot:** Binary states caused extreme kinetic jitter during transient signal loss. We pivoted to a continuous Exponentially Weighted Moving Average (EWMA) Trust Score, mapping probabilistically smoothed network health to physical safety limits.

### Pivot 4: Overcoming the ROS 2 Boot-Storm Livelock
*   **Initial Design:** Default ROS 2 `RELIABLE / KEEP_ALL` QoS profiles.
*   **The Pivot:** During post-jamming boot storms, the Pi 4 queue grew unboundedly as the edge nodes bottlenecked on the cryptographic math. This Head-of-Line blocking dropped safety packets. We pivoted to `BEST_EFFORT / KEEP_LAST (Depth=1)`, which sheds stale boot-storm traffic and resolved the livelock. (The queueing-theory characterization previously given here — a stable M/D/1 model and a 99.6% shedding figure — does not trace to retained data [WITHDRAWN — see ground_truth.md]; the QoS change survives as an engineering fix.)

### Pivot 5: Trajectory Generation offloading (Kinematics)
*   **Initial Design:** Using ROS 2 `scaled_joint_trajectory_controller` to compute splines on the Pi 4.
*   **The Pivot:** The cryptographic load on the Pi 4 caused CPU jitter, which misaligned the spline timestamps. The UR5 controller detected the timing failure and threw a Protective Stop `Error Code: -1`. We pivoted to `passthrough_trajectory_controller`, offloading all spline math directly to the native UR5 hardware.

### Pivot 6: Inertial Scaling (Niryo Ned2 to UR5)
*   **Initial Design:** Establishing the baseline DIL failure modes using a Niryo Ned2 (15V educational stepper architecture).
*   **The Pivot:** The educational stepper motor lacked the severe mechanical inertia and ISO 13849-1 compliance profiles of heavy industrial robotics. We pivoted the physical empirical testing to the Universal Robots UR5 (24V servo architecture) to accurately measure the kinematic deceleration curves and the physical hardware shearing trade-offs of inducing a Category 0 vs Category 1 stop.

### Pivot 7: Software Preemption vs. Hardware Optocouplers
*   **Initial Design:** When the edge node detected an attack, it sent a `stopl()` command back over the network to the UR5's TCP/IP interface.
*   **The Pivot:** Network transit and the URScript internal scheduler consumed ~368ms. At 1.5 rad/s, the UR5 moved blindly during this window. We pivoted to a dual-channel 24V PNP Optocoupler circuit wired directly into the UR5's SCB `SI0/SI1` safety ports, achieving a near-instant software-bypass halt.

### Pivot 8: The C192A4 Electromechanical Timing Limitation
*   **Initial Design:** Assuming a clean resumption of robotic motion after a DIL outage.
*   **The Pivot:** Integration revealed a severe electromechanical timing limitation. Because the hardware bypass uses dual-channel safety, microscopic timing discrepancies between Channel 1 and Channel 2 during Trust Score restoration force the UR5 to trigger a **C192A4 Safeguard Stop Disagreement** fault. While effectively locking down the machinery and enforcing a "Human-in-the-Loop" reset, this is formally recognized as a hardware *timing fault on restoration*, not a designed latching stop. The designed stop through the SI0/SI1 safeguard inputs is a **Category 2** safeguard stop (auto-resuming on restore); once the C192A4 fault latches, however, the controller's safety-fault state performs a **Category 0 halt** until manual reset (`ground_truth.md` §5.3). The fault highlights the mechanical trade-offs of driving dual-channel safety inputs from cryptographic trust logic.
