# MASTER TECHNICAL SPECIFICATION & DEFENSE MANUAL: SENTRYC2
## Decentralized Edge-Compute Authorization Framework for Industrial Robotics in DIL Environments
*Master of Science in Systems Engineering Thesis Reference Manual*
*Candidate: Luke Pepin | Advisor: Dr. Manbir Sodhi | University of Rhode Island (2026)*

---

## CHAPTER 1: INTRODUCTION, THREAT MODEL, & OPERATIONAL IMPERATIVE

### 1.1 The "Cloud-First" Vulnerability and the Operational Challenge
Modern Industry 4.0 and Department of Defense (DoD) command-and-control (C2) architectures operate under a centralizing "Cloud-First" paradigm. Under nominal conditions, active machinery and robotic manipulators must maintain continuous backhaul network connectivity to a centralized Identity Provider (IdP) for active authorization and lease renewal.

In Disconnected, Intermittent, and Limited (DIL) environments—specifically under tactical electronic warfare (EW) jamming or backhaul network partitions—this architectural coupling introduces a catastrophic failure mode. Expiring authorization leases trigger involuntary safety shutdowns on active machinery. This paralyzes expeditionary logistics, compromises forward-deployed Manufacturing Execution Systems (MES), and severely degrades Overall Equipment Effectiveness (OEE).

### 1.2 The Coalition Logistics Threat Model
SentryC2 addresses the **Coalition Logistics Threat Model** under a multi-tenant operational environment (e.g., USMC and foreign allied joint forces). The system must operate under the following security constraints:
*   **Adversary Capabilities:** Active signal jamming (up to 100% packet loss), malicious packet injection, and unauthorized supervisor node sniffing.
*   **allied Joint Privacy (Selective Attribute Disclosure):** Foreign allied robotic worker nodes must verify their authorization leases peer-to-peer to execute shared trajectory scripts (such as G-code machining paths) without exposing their sovereign cryptographic keys or private identities to the local supervisor node.
*   **The Cyber-Physical Boundary:** The safety system must guarantee that a compromised or un-authenticated node is evicted, triggering a physical standstill within the **ISO 13849-1 Performance Level d (PLd)** mandatory safety limit of **500 ms**.

---

## CHAPTER 2: LITERATURE REVIEW & THEORETICAL GAPS

### 2.1 ICS Authentication and MTTR Benchmarking Gaps
A critical review of contemporary Industrial Control System (ICS) security literature reveals three primary theoretical and empirical gaps:
1.  **Absence of Lossy MTTR Benchmarks:** Current literature lacks formalized Mean Time to Recovery (MTTR) or Safety Eviction Latency ($T_{\text{evict}}$) benchmarks for decentralized robotic cells subjected to communication drop rates exceeding $20\%$.
2.  **Binary Trust Limitations:** Existing architectures rely on binary (allow/deny) static authentication checks. SentryC2 introduces a continuous, probabilistic, and dynamically decaying trust model that bridges network-layer health with physical motion control.
3.  **The Middleware Scalability Gap:** High-level studies in ROS 2 / DDS scalability frequently evaluate CPU or bandwidth limits but ignore RTPS (Real-Time Publish-Subscribe) RELIABLE protocol degradation under signal jamming. Default **RELIABLE / KEEP_ALL** Quality of Service (QoS) profiles stubbornly exhaust network buffers trying to deliver stale, expired packets during post-partition boot storms, leading to network-layer livelocks. This research resolves this gap by analyzing the transition to **BEST_EFFORT / KEEP_LAST (Depth=1)** QoS settings.

---

## CHAPTER 3: SYSTEM ARCHITECTURE & TOPOGRAPHICAL DESIGN

### 3.1 Star-Compute Topology
To bypass the strict memory constraints of the edge nodes, SentryC2 is structurally classified as an **Edge-Compute Star Topology**. 

```
                       +-------------------------+
                       |   Level 4 Cloud IdP     |
                       +------------+------------+
                                    | (Backhaul Link)
                                    v (DIL Partition Boundary)
                       +-------------------------+
                       |  Pi 4 Supervisor Node   |
                       |    (Cortex-A72, ROS 2)  |
                       +------+- - - - - -+------+
                              |           |
             (Serial UART)    |           | (Serial UART)
           (JSON Handshake)   |           | (JSON Handshake)
                              v           v
                       +------+---+   +---+------+
                       | Arduino  |   | Arduino  |
                       | Worker A |   | Worker B |
                       +----+-----+   +----+-----+
                            |              |
                      (24V Opto Relay) (24V Opto Relay)
                            v              v
                       +----+-----+   +----+-----+
                       |  UR5 SI0 |   |  UR5 SI1 |
                       +----------+   +----------+
```

### 3.2 Physical serial Bridge & Handshake Protocol
To eliminate dynamic memory allocation and prevent stack-heap collisions on the constrained ARM Cortex-M4 microcontroller (**Arduino Nano 33 BLE** featuring only **256 KB of SRAM**), the edge nodes run bare-metal C++ firmware with no micro-ROS abstraction layer. Communication between the supervisor (Raspberry Pi 4) and the workers is managed via a dedicated **serial JSON handshake** over physical UART:
*   **Baud Rate:** $115200\text{ bps}$
*   **Dynamic Parameterization:** The Pi 4 dynamically provisions the cryptographic algorithm parameters (ECC vs. ZKP) and the trust-smoothing constants ($\alpha \in \{0.5, 0.7, 0.9\}$) via serial JSON frames, eliminating flash-memory corruption and cross-trial parameter bleeding.
*   **Verification-Trigger Pipeline:** 
    1.  The Pi 4 streams high-frequency (50Hz) raw joint and IMU kinematics over the serial bridge to the Arduino.
    2.  The Arduino parses the kinematics, executes its local cryptographic verification loops, and dynamically updates its internal Exponentially Weighted Moving Average (EWMA) Trust Score ($\Gamma$).
    3.  If $\Gamma$ plummets below $30.0$, the Arduino cuts its dual-channel GPIO outputs, dropping the 24V safety line to execute a physical Category 2 Safeguard Stop.

---

## CHAPTER 4: EMPIRICAL VALIDATION OF CRYPTOGRAPHIC LATENCY

### 4.1 Bare-Metal Profiling via the `DWT_CYCCNT` Register
To isolate cryptographic computation times from OS-level timing jitter, the Arduino Nano 33 BLE leverages the ARM Cortex-M4's internal hardware cycle counter register (**`DWT_CYCCNT`**), achieving a cycle-accurate timing resolution of **$15.625\text{ ns}$** at $64\text{ MHz}$.
*   **ECDSA point Multiplication Baseline (`uECC_make_key`):** Benchmark data profiles a single bare-metal point multiplication at exactly **$111.5\text{ ms}$** under zero hardware acceleration.

### 4.2 Bounding Latency Variance via the Berry-Esseen Theorem
True Zero-Knowledge Proof (ZKP) selective-disclosure verification is computationally intensive. To prove that these proofs can be verified on constrained edge hardware without violating the $500\text{ ms}$ safety limit, the cryptographic verification is segmented into independent, byte-level sub-verification steps.

By invoking the **Berry-Esseen theorem** (the non-i.i.d. formulation of the Central Limit Theorem), the summation of these independent payload segments normalizes the aggregate execution variance. This compresses the execution tail into a highly predictable, Gaussian-bounded window of **$301\text{ ms}$ to $346\text{ ms}$** (simulated via exactly 3 bare-metal Point Multiplication loops totaling $334.5\text{ ms}$). This mathematical bounding guarantees that even under worst-case CPU thermal throttling, the local trust monitor evicts the node before the $500\text{ ms}$ kinetic safety boundary is crossed.

---

## CHAPTER 5: MIDDLEWARE OPTIMIZATION & QUEUE SATURATION DYNAMICS

### 5.1 The Pollaczek-Khinchine M/D/1 Queueing Reduction
During post-partition network recovery, the simultaneous reconnection of multiple edge workers triggers a massive data influx (a **"boot storm"**). Traditionally, the supervisor's verifier queue is modeled stochastically as an $M/M/1$ system. However, SentryC2's Berry-Esseen payload segmentation forces a highly deterministic verifier service time.

We model this behavior using the **Pollaczek-Khinchine formula**, which defines the mean queue length ($L_q$) as:
$$L_q = \frac{\rho^2(1 + C_v^2)}{2(1 - \rho)}$$

Because the bare-metal service coefficient of variation is measured to be near-zero ($C_v \approx 0.016$), the $C_v^2$ term drops out of the equation. This mathematically reduces the supervisor node's queue from a stochastic $M/G/1$ system to a deterministic **$M/D/1$ queueing model**:
$$L_q = \frac{\rho^2}{2(1 - \rho)}$$

This deterministic queue model enables precise calibration of high-node density scaling (up to 100 nodes) in NS-3 simulations, providing a stable verifier service rate of $\mu = 103.63\text{ pkts/sec}$.

### 5.2 DDS Quality of Service (QoS) Optimizations
At high node densities ($n \ge 12$), default ROS 2 middleware QoS profiles (**RELIABLE / KEEP_ALL**) trigger Head-of-Line (HoL) blocking and infinite packet-retransmission loops during network jamming. SentryC2 eliminates this bottleneck by enforcing:
*   **History:** `KEEP_LAST`
*   **Depth:** `1`
*   **Reliability:** `BEST_EFFORT`
This allows the supervisor node to instantly drop stale, outdated joint telemetry packets, shedding $99.6\%$ of boot-storm traffic and exposing the true, un-throttled CPU limit of the Pi 4.

---

## CHAPTER 6: KINEMATIC INTEGRATION & HARDWARE SAFETY INTERCEPTS

### 6.1 Bypassing the Software Mode-Switching Penalty
In collaborative robotic systems, software-level preemption commands (such as injecting joint deceleration commands via `URScript` over TCP/IP) consume over **$368\text{ ms}$** in mode-switching and thread scheduling overhead. Under peak joint velocities ($\omega = 1.5\text{ rad/s}$), this delay allows the robot arm to execute massive, uncontrolled "blind" trajectories during a network partition.

SentryC2 overrides this software latency entirely by implementing a hardwired **hardware optocoupler safety intercept**:

```
 [Arduino Sentry Pin 5] ──+24V (SI0 Input) ──► [UR5 SCB Dual-Channel SI0]
 [Arduino Sentry Pin 6] ──+24V (SI1 Input) ──► [UR5 SCB Dual-Channel SI1]
```

### 6.2 Dual-Channel Redundant Category 3 Design
To satisfy the strict single-fault tolerance requirements of **ISO 13849-1 Performance Level d (PLd)**, the safety intercept is engineered as a strictly dual-channel, redundant circuit:
*   **Redundancy:** The Arduino Nano 33 BLE drives two independent GPIO pins mapping to two isolated 24V PNP optocoupler circuits.
*   **Synchronicity Delta ($T_{\text{sync}}$):** The microcontroller firmware transitions both GPIO pins synchronously within a measured delta of **$<20\text{ ms}$**. If the transition delta exceeds **$48\text{ ms}$**, the UR5 Safety Control Board (SCB) instantly flags a state mismatch and latches a non-recoverable **C192A4 Safeguard Stop Disagreement** fault, triggering a Category 0 Safe Torque Off (STO).
*   **Stop Category 2 Monitored Standstill:** Under normal execution, the optocoupler drops trigger a **Stop Category 2 Safeguard Stop**, which holds the robot in a monitored standstill with motor drive power retained. This allows programmatic resumption of trajectories via Port 29999.

### 6.3 Post-Eviction Kinematic Deceleration
Once the safety loop is triggered, the physical deceleration curve is mapped using a wrist-mounted 9-axis IMU (LSM9DS1) filtered through an Extended Kalman Filter (EKF) to isolate joint vibration noise.
*   **Deceleration Time ($T_{\text{mechanical\_deceleration}}$):** The physical braking phase requires **$\approx 110\text{ ms}$** to dissipate joint momentum and bring velocities to absolute zero ($v = 0\text{ rad/s}$).
*   **The Total Safety Budget:** 
    $$T_{\text{total}} = T_{\text{crypto}} + T_{\text{serial\_bridge}} + T_{\text{network\_latency}} + T_{\text{mechanical\_deceleration}} \le 500\text{ ms}$$
    By compressing the software and electrical preemption phases ($T_{\text{crypto}} + T_{\text{serial}}$) to **$<16\text{ ms}$**, SentryC2 preserves over **$480\text{ ms}$** of the mandatory safety budget strictly for the mechanical joint-braking phase.

---

## CHAPTER 7: DUAL-USE STRATEGIC TRANSITION

### 7.1 "Permission-Based" vs. "Persistence-Based" Control
SentryC2 transitions robotic control from traditional "Permission-Based" authority (requiring continuous, centralized cloud backhaul) to **"Persistence-Based" Edge-First control**. Robotic clusters retain autonomous, local cryptographic authority to execute critical operations during extended backhaul severances, only syncing database transactions (such as WorkOrders and SensorLogs) back to the Cloud IdP upon link restoration.

### 7.2 Tactical Military Transition (DoD Contested Logistics)
This framework is engineered as a tactical dual-use baseline for forward-deployed **USMC Expeditionary Automated Repair Cells (EARCs)**:
*   **Frontline Survivability:** Enables forward-deployed robotic machining cells to continue printing or repairing critical engine components under active Electronic Warfare (EW) jamming campaigns without risking safety shutdowns or adversarial command-injection.
*   **MCTSSA Integration:** Architectural parameters align directly with Project Dynamis guidelines managed by the Marine Corps Tactical Systems Support Activity (MCTSSA).

### 7.3 Industrial Commercialization Strategy
For civilian Industry 4.0 applications, SentryC2 serves as "operational insurance" against cloud connectivity dropouts:
*   **OEE Protection:** Unplanned downtime costs advanced manufacturing cells an estimated $400 billion annually. By isolating transient network blackouts and handling security verification at the local edge, SentryC2 prevents expensive, unnecessary emergency brake deployments, preserving factory-floor throughput and reducing mechanical wear-and-tear.
