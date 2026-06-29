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
- "Crucially, we achieve microsecond-precision latency measurement by directly hooking into the ARM Cortex-M4 `DWT_CYCCNT` hardware register—a core feature of our IP disclosure."
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

## Slide 6: Physical Demonstration: Securing the ISO 500ms Ceiling
**Visuals:** **[EMBED YOUR RECORDED LAB VIDEO HERE - SHOWING THE SUCCESSFUL STOP]**. Include a small Picture-in-Picture of the UR Teach pendant, and split-screen terminals showing the ROS 2 logs.
**Speaker Notes:**
- "Let's look at the physical validation on the UR5."
- "Here, the robot is executing a high-speed 50Hz kinematic pick-and-place stream."
- "At 15 seconds, we simulate a Byzantine injection by feeding a massive 256-byte payload into the Sentry."
- "Notice the ROS 2 logs: the execution time spikes to 610ms, the Trust Score drops below 30, and the system instantly preempts the kinematics and violently arrests the robot's momentum."

---

## Slide 7: Overcoming the Kinematic Bottleneck
**Visuals:** Telemetry graphs showing the initial 720ms software failure vs the final sub-500ms successful deceleration curve. 
**Speaker Notes:**
- "Achieving this sub-500ms stop required overcoming a massive engineering hurdle."
- "Initially, we used a standard `stopj(5.0)` trajectory deceleration. However, transitioning from ROS 2 forward trajectory planning to the URScript interpreter introduced over 368ms of software mode-switching overhead."
- "This caused our initial tests to fail the ISO standard, taking 1.3 seconds to halt."
- "To solve this, we aggressively tuned the deceleration parameter up to `stopj(20.0)` [or implemented the direct GPIO Safe Torque Off], successfully bypassing the computational bloat and crushing the deceleration curve to fit within the safety budget."

---

## Slide 8: The Core Architecture Success
**Visuals:** A clean summary slide highlighting the "SentryC2" architecture and the patentable features.
**Speaker Notes:**
- "Our final telemetry proves the SentryC2 architecture works."
- "By coupling the `DWT_CYCCNT` hardware register profiling with the EWMA ROS 2 Trust Monitor and aggressive hardware-level preemption, we successfully isolated a Denial-of-Service attack and halted an industrial robot before a collision could occur."
- "This system provides a robust, patentable framework for securing decentralized MANET robotics."

---

## Slide 9: Continued Work: NS-3 Simulation & Extrapolation
**Visuals:** A visual of an M/M/1 Queueing Model alongside a 100-node NS-3 simulation topology.
**Speaker Notes:**
- "Now that the physical latency budget is secured, our next step is large-scale extrapolation."
- "Rather than physically provisioning a cluster, we are currently extracting the baseline service rates (μ) from our 10-node data."
- "We will feed this empirical data into an NS-3 discrete-event simulation utilizing an M/M/1 queueing model."
- "This will allow us to mathematically prove the queue saturation limits and Livelock thresholds for a 100-node robotic swarm."
- "Thank you. I will now take any questions."
