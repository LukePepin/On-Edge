# Lab Presentation: Cryptographic Edge Robotics

**Title:** On-Edge: Securing ISO-13849 Robotic Actuators via Cryptographic Edge Nodes and ROS 2 EWMA Trust Architectures  
**Presenter:** [Your Name]  
**Target Duration:** ~10-15 Minutes  

---

## Slide 1: Title Slide & Introduction
**Visuals:** Title text, university/lab logo, perhaps a high-level graphic of a robotic arm connected to a network.
**Speaker Notes:**
- "Hello everyone, today I'll be presenting my thesis work on securing safety-critical industrial robotics at the network edge."
- "As industrial robots transition from isolated cells to distributed, cloud-managed MANETs (Mobile Ad-hoc Networks), they become vulnerable to network injection, Byzantine faults, and Denial-of-Service attacks."
- "My research proposes a localized cryptographic 'sentry' system to guarantee fail-safe state operation without relying on high-latency cloud supervision."

---

## Slide 2: The Problem: Networked Robotics vs ISO-13849
**Visuals:** A diagram showing a cloud server communicating with a ROS 2 robot, with a red lightning bolt indicating a network delay or hacker injection.
**Speaker Notes:**
- "Industrial functional safety (ISO-13849) demands that if a safety constraint is violated, the robot must halt within a strict, sub-500 millisecond fail-safe latency ceiling."
- "Traditional authentication relies on centralized servers or heavy cryptography. If the network degrades, or a bad actor injects packets, traditional authentication pipelines suffer from queue saturation and livelock."
- "If a robot is moving at high speed and the network stalls, that 500ms ceiling is easily breached, resulting in catastrophic physical collisions."

---

## Slide 3: Our Solution: The Cryptographic Edge Sentry
**Visuals:** Architecture diagram. A Raspberry Pi (ROS 2 Supervisor) connected to an Arduino Nano 33 BLE (Sentry), which regulates traffic to a Universal Robots UR5.
**Speaker Notes:**
- "To solve this, we physically detached the cryptographic authentication from the network middleware and placed it on a dedicated bare-metal microcontroller (an Arduino Nano 33 BLE)."
- "This 'Sentry' node sits at the absolute edge of the network. It processes Zero-Knowledge Proofs (ZKPs) locally and reports its execution time."
- "By using the Central Limit Theorem across 64-byte payloads, we proved that valid cryptographic processing stabilizes into a highly deterministic execution window of roughly 325ms."

---

## Slide 4: The EWMA Trust Monitor
**Visuals:** Graph showing an Exponentially Weighted Moving Average (EWMA) curve dropping rapidly when execution time exceeds 500ms.
**Speaker Notes:**
- "Instead of binary pass/fail mechanics, our ROS 2 supervisor utilizes an Exponentially Weighted Moving Average (EWMA) Trust Score."
- "The ROS 2 node constantly monitors the Sentry's execution latency."
- "If a node is compromised and flooded with a malicious payload, the cryptographic execution time instantly spikes. The EWMA trust score plummets, isolating the node and immediately triggering a hardware preemption."

---

## Slide 5: Validating the H3 Livelock Hypothesis (Software Limitation)
**Visuals:** A chart from your H3_LIVELOCK_VALIDATION_REPORT showing 54% timeout failure at High Saturation (n=24) despite using a 4-thread MultiThreadedExecutor.
**Speaker Notes:**
- "Before running physical tests, we conducted heavy software profiling."
- "We discovered that physical CPU multi-threading provides zero mitigation against network queue saturation (Head-of-Line blocking) in ROS 2."
- "This proved that future robotic networks cannot rely on CPU scaling to survive DoS attacks; they must use priority-based Token Bucket admission control to drop malicious packets before they even enter the queue."

---

## Slide 6: Physical Demonstration (Video)
**Visuals:** **[EMBED YOUR RECORDED LAB VIDEO HERE]**. Include a small Picture-in-Picture of the UR Teach pendant, and split-screen terminals showing the ROS 2 logs.
**Speaker Notes:**
- "Let's look at the physical validation on the UR5."
- "Here, the robot is executing a high-speed 50Hz kinematic pick-and-place stream."
- "At 15 seconds, we simulate a Byzantine injection by feeding a massive 256-byte payload into the Sentry."
- "Notice the ROS 2 logs: the execution time spikes to 610ms, the Trust Score drops below 30, and the system instantly preempts the kinematics and commands a `stopj()` hardware brake."

---

## Slide 7: The Single-Threaded Microcontroller Vulnerability
**Visuals:** A timeline graphic showing the Arduino blocking for 610ms, while the UR5 continues moving forward blindly. 
**Speaker Notes:**
- "While the safety system successfully halted the robot, our CSV telemetry revealed an incredible edge-case vulnerability."
- "Because the Arduino is a single-threaded microcontroller, the massive payload locked its execution loop for 610ms."
- "During this 610ms window, the ROS 2 supervisor was starved of data, and the robot continued moving blindly, breaching the ISO 500ms ceiling before the kill-switch could fire."
- "This proves that single-threaded microcontrollers are physically incapable of surviving DoS attacks in safety-critical robotics; they require multi-threaded RTOS architectures or hardware interrupts."

---

## Slide 8: The Kinematic Parameter Flaw (Current State)
**Visuals:** Velocity/Deceleration graph (v(t) = v0 + ∫a(t)dt) showing the 720ms braking overhead.
**Speaker Notes:**
- "Our telemetry also revealed a secondary, hardware-level deceleration failure."
- "Initially, we commanded a `stopj(5.0)` brake. Theoretically, this should stop the robot in 352ms. However, switching from ROS 2 trajectory planning to the URScript interpreter introduced massive controller overhead, extending the physical stop to over 720ms."
- "Our current state of development is actively resolving this 'Kinematic Parameter Flaw'. We are escalating the deceleration parameter to `stopj(20.0)`."

---

## Slide 9: Continued Work & Future Integration
**Visuals:** Bulleted list of next steps, perhaps a CAD rendering or photo of a 9-node MANET cluster.
**Speaker Notes:**
- "If escalating the deceleration parameter fails to beat the URScript switching latency, we will pivot to a direct GPIO hardware bypass, triggering the UR5's Safe Torque Off (STO) directly from the Arduino."
- "Once the 500ms fail-safe ceiling is mathematically secured, we will move to Phase 3.6 of the roadmap."
- "This involves provisioning a 9-node edge cluster to test MANET saturation, and porting our findings into an NS-3 discrete-event simulation to map large-scale swarm behaviors."
- "Thank you. I will now take any questions."
