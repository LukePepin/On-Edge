DECENTRALIZED ZKP AUTHORIZATION MESHES FOR INDUSTRIAL ROBOTICS IN DIL ENVIRONMENTS OUTLINE V2
BY  
LUKE PEPIN

**ADMIN** \- Format for Thesis was downloaded online from URI website along with Harishjitu’s and Stephen’s Theses for reference. The current plan is to write chapters here and import the text over to limit issues with formatting until they become critical.  
**ABSTRACT** \- I plan to fully rewrite my abstract once the paper is completed so it acts as a true summary of the work completed, however for review purposes I did include a very early version of what it may look like on page 5\.  
**ACKNOWLEDGMENTS** \- Harishjitu has a very nice Acknowledgement section I intend to base mine off. Obviously Dr. Sodhi is my primary acknowledgement. I would however like to make the addition of thanking the lab group as whole as well as more specific maybe 1 sentence individual thankful messages to both outside committee members given it was Dr. Maier-Speredelozzi’s recommendation which led me here to URI and for Dr. Sun thanks her for allowing me to participate in CYPHER.

**LIST OF TABLES** 
* Table 1: System Hardware and Star Topology Parameters
* Table 2: QoS Middleware Optimization Comparison
* Table 3: 18-Config Transition and Latency Results
* Table 4: Statistical Security Tax Analysis
* Table 5: NS-3 M/D/1 Queue Saturation Data

**LIST OF FIGURES** 
* Figure 1: Centralized Security Fragility vs. Decentralized Edge Star Topology
* Figure 2: H1' Trust Score Decay Under Jamming
* Figure 3: Supervisor Cryptographic Latency Comparison
* Figure 4: Embedded Worker Computational Feasibility
* Figure 5: Queue Saturation Boundary and Network Latency Divergence
* Figure 6: Integrated Safety Response Budget Waterfall

**CHAPTERS \-** Here is my ‘table of contents’ for the outline.

* **CHAPTER 1 \- INTRODUCTION & THREAT MODEL:** Define the "Cloud-First Kill Switch" and the Coalition Logistics Threat Model.
* **CHAPTER 2 \- LITERATURE REVIEW & DIL GAP:** Establish the critical academic gaps in decentralized ICS authentication and safety mechanisms under network degradation.  
* **CHAPTER 3 \- EDGE-COMPUTE STAR TOPOLOGY METHODOLOGY:** Document the physical hardware layout and mathematical formulation of the decentralized "Cloud-Edge-Cloud" state machine.  
* **CHAPTER 4 \- EMPIRICAL VALIDATION: RESILIENCE (H1') & SECURITY TAX (H2a/b):** Present the physical testing results, Cortex-M4 ZKP profiling, and the Central Limit Theorem payload stabilization phenomenon.  
* **CHAPTER 5 \- QUEUE SATURATION & HARDWARE OPTIMIZATION:** Detail the Randomized Queue testing methodology, M/M/1 Queue Saturation Livelocks, and QoS middleware optimization.  
* **CHAPTER 6 \- KINEMATIC DECELERATION & THE HARDWARE STO BYPASS:** Resolve mechanical-computational isolation boundaries and the integration of the Latching Cryptographic Halt (C192A4) on the UR5.  
* **CHAPTER 7 \- COMMERCIAL & DEFENSE IMPLICATIONS:** Translate the empirical safety-boundary and queueing results into a dual-use USMC and Commercial transition strategy.

# **Start of Writing**

**ABSTRACT**   
When completed, this abstract will state that traditional Cloud-First Identity Providers (IdPs) create catastrophic "kill switch" vulnerabilities in DoD Contested Logistics, causing involuntary safety halts during network jamming. To mitigate this, the thesis proposes a Decentralized Edge-Compute Star Topology utilizing Zero-Knowledge Proof (ZKP) selective disclosure. Empirical profiling demonstrates that segmenting payloads invokes the Central Limit Theorem, bounding Cortex-M4 execution variance to securely operate within the strict ISO 13849-1 500ms fail-safe boundary. Furthermore, this research corrects traditional queueing assumptions by identifying ROS 2 FIFO Livelock vulnerabilities and optimizing CycloneDDS QoS profiles to expose true deterministic M/D/1 processing limits. The thesis concludes by proving that an Opto-Isolated 24V Safe Torque Off (STO) hardware bypass successfully arrests the Universal Robots UR5 manipulator beneath the 500ms ceiling, utilizing a novel Latching Cryptographic Halt to guarantee human-in-the-loop security verification.

**CHAPTER 1 \- INTRODUCTION & THREAT MODEL**  
* **1.1 The Industry 4.0 Authentication Paradigm (Cloud-First Fragility):** Modern MES systems rely almost exclusively on centralized architectures. In undisturbed network topologies, this is highly efficient. In DIL environments, it is a catastrophic vulnerability.
* **1.2 The Threat Model: Contested Logistics, Kill Switches, and Coalition Privacy:** In DoD Contested Logistics theaters subjected to EW jamming, reliance on a central server transforms the IdP into a catastrophic single point of failure (a "Kill Switch"). Furthermore, allied/multi-tenant nodes must prove authorization without exposing classified keys (The Coalition Requirement).
* **1.3 The Kinematic Boundary: ISO 13849-1 Functional Safety:** Industrial safety standard ISO 13849-1 mandates a strict temporal ceiling of 500ms to prevent kinetic damage during authorization loss. Any decentralized mechanism must have an MTTR < 500ms.
* **1.4 The Proposed Solution: Decentralized Edge-Compute Star Topology:** An "Edge-First" framework utilizing a Star Topology to protect edge microcontroller memory limits. Nodes verify each other utilizing ZKP attribute selective disclosure, and network integrity is tracked locally using an Exponentially Weighted Moving Average (EWMA) Trust Score.

**CHAPTER 2 \- LITERATURE REVIEW & DIL GAP**  
*This chapter systematically maps current research against the constraints of Expeditionary Automated Repair Cells (EARC) to expose 5 critical academic gaps:*
* **2.1 Gap 1: Absence of MTTR Baselines in DIL Environments:** Existing literature predominantly focuses on hybrid fog-cloud architectures without measuring Mean Time To Recovery (MTTR) under high-latency, >20% packet loss conditions.
* **2.2 Gap 2: The Security Tax Gap (Cortex-M4 Profiling):** While ZKP feasibility on Cortex-A (Raspberry Pi 4) is documented, no literature tests ZKP performance on strictly constrained Cortex-M4 platforms (Arduino Nano 33 BLE), creating an unquantified security tax.
* **2.3 Gap 3: The Probabilistic Trust Gap:** Current decentralized trust models remain binary (authenticated/rejected) or use abstract reputation. No existing frameworks implement continuous, mathematically quantified trust decay parameters ($\alpha$) analogous to the $\Gamma$ formula structure.
* **2.4 Gap 4: The Scalability Gap (Queuing & Livelocks):** Scalability testing rarely exceeds n=5 nodes, entirely ignoring verification queuing delays, gossip protocol bandwidth overhead, and network-layer Livelock conditions at higher node densities.
* **2.5 Gap 5: ICS Safety Mechanisms (Disconnect from Cryptography):** A critical disconnect exists between cryptographic authentication research and physical ICS safety engineering. Current literature fails to address whether authentication failure should trigger an involuntary kill switch or degrade trust, ignoring G-code verification and Digital Twin quality management.

**CHAPTER 3 \- EDGE-FIRST TOPOGRAPHICAL METHODOLOGY**  
* **3.1 Localized Hardware Configuration (Edge-Compute Star Topology):** Abandoning peer-to-peer wireless mesh routing (MANET) in favor of a Star Topology using a Raspberry Pi 4 Supervisor and Arduino Nano 33 BLE worker nodes.
* **3.2 The SRAM Constraint & Serial JSON Bridge Pivot:** To mathematically protect the 256KB memory boundary of the Cortex-M4, micro-ROS middleware is stripped in favor of a lightweight Serial JSON Bridge.
* **3.3 Cryptographic Action Script Verification (Kinematic Triggering):** Cryptographic verification mathematically unlocks predefined ROS 2 kinematic trajectory hashes on the Pi 4 supervisor.
* **3.4 Probabilistic Trust & The EWMA Formulation:** Replacing binary authentication with the continuous EWMA trust score: $\Gamma(t+1) = \alpha \times \Gamma(t) + (1-\alpha) \times N_0$.

**CHAPTER 4 \- EMPIRICAL VALIDATION: RESILIENCE (H1') & SECURITY TAX (H2)** 
* **4.1 H1' Validation: The Crossover Threshold ($p^*$) Under DIL Conditions:** Using `tc` and Scapy to simulate EW jamming, isolating the exact packet-loss crossover threshold ($p^*$) where the decentralized architecture MTTR becomes superior to cloud IdP.
* **4.2 H2a/b Validation: The Coalition Privacy Tax (Cortex-M4 Profiling):** Using the `DWT_CYCCNT` hardware register (64 MHz) to isolate true CPU algorithmic tax, quantifying the 22.85% "Security Tax" of Schnorr/ZKP selective disclosure.
* **4.3 The 64-Byte Stabilization Phenomenon & The Central Limit Theorem (CLT):** 
  * Initial testing revealed single highly complex ZKP attributes caused sporadic ~540ms latency spikes, violating the 500ms safety ceiling.
  * By segmenting payloads and injecting independent algorithmic jitter for each byte, the execution variance perfectly adhered to the **Central Limit Theorem (CLT)**.
  * ZKPs with multiple independent constraints (attributes) are statistically *safer* from RTOS jitter because the variances average out, bounding the 64-byte payload execution into a deterministic 301ms-346ms window.

**CHAPTER 5 \- QUEUE SATURATION & HARDWARE OPTIMIZATION**  
* **5.1 The Randomized Queue Methodological Pivot:** 
  * To guarantee rigorous ANOVA statistical validity, we structurally abandoned sequential block testing in favor of a **Randomized Queue with Dynamic Reshuffling (seed=42)**.
  * This pivot proved crucial in eliminating temporal confounding—specifically thermal drift on the Cortex-M4 and time-varying RF interference—securing independent and identically distributed (i.i.d.) error bounds for the trial data.
* **5.2 The M/M/1 Queue Saturation Vulnerability & Livelock:**
  * During integration, we discovered a critical Denial-of-Service vulnerability: ROS 2 FIFO network queues suffer catastrophic saturation when processing heavy cryptographic payloads alongside a 50Hz kinematic stream.
  * A 256-byte payload caused a 610ms execution delay, artificially dropping the Service Rate ($\mu$) below the Arrival Rate ($\lambda$). The Traffic Intensity ($\rho$) exploded, causing a mathematical Livelock that dropped physical safety kill-switch packets.
* **5.3 The M/D/1 Deterministic Queue Correction & QoS Optimization:** Transitioning QoS reliability from `RELIABLE` to `BEST_EFFORT` with `Depth = 1` immediately drops stale authentication requests, eliminating Head-of-Line (HoL) blocking.
* **5.4 NS-3 Extrapolation & True Saturation Boundary ($n^*$):** Ingesting the deterministic M/D/1 service rate ($\mu$) into an NS-3 simulator to pinpoint the true maximum node density ($n^*$) before genuine queue saturation occurs under EW jamming.

**CHAPTER 6 \- KINEMATIC DECELERATION & THE HARDWARE STO BYPASS**
* **6.1 Trajectory Instability and Spline Explosions:** Resolving ROS 2 trajectory planner quintic spline interpolations by under-constraining boundary conditions to natural cubic splines.
* **6.2 The Software Bottleneck (The 368ms Mode-Switch Penalty):** Empirical telemetry revealing a catastrophic 368ms overhead when mode-switching to URScript interpreters.
* **6.3 The 24V PNP Optocoupler Bypass (Hardware STO):** Utilizing an "Active-High" hardware fail-safe to physically sever the 24V supply to the UR5's safety ports when the EWMA Trust Score drops below 30.0.
* **6.4 The C192A4 Electromechanical Timing Fault:**
  * Integration revealed a severe electromechanical timing limitation: Because the hardware bypass uses dual-channel safety, microscopic timing discrepancies between Channel 1 and Channel 2 during Trust Score restoration force the UR5 to deliberately latch a **C192A4 Safeguard Stop Disagreement** fault.
  * This highlights the profound mechanical trade-offs of utilizing an uncontrolled Category 0 STO (Safe Torque Off) to meet cryptographic latency goals, risking severe joint shearing on heavy industrial manipulators compared to controlled Category 1 decelerations.
* **6.5 Odometry Fusion and the Latency Boundary Proof:** Using an Extended Kalman Filter (EKF) on the wrist-mounted IMU to mathematically prove $T_{total} \le 500ms$.

**CHAPTER 7 \- COMMERCIAL & DEFENSE IMPLICATIONS**
* **7.1 The USMC EARC Beachhead Market (Defense Application):** Outfitting EARC systems with the "Tactical Fortress" tier (ZKP) for A2/AD contested environments.
* **7.2 The Commercial Manufacturing Liability ($400B Downtime):** Offering the "Industrial Sprint" tier (ECC) to prevent expensive unplanned downtime caused by routine backhaul drops.
* **7.3 The Dual-Use De-risking Strategy:** Proving survival under active EW jamming on a 256KB SRAM budget is the strategic wedge for commercial expansion.
* **7.4 The Persistence-Based Paradigm Shift:** Shifting the industry baseline from "Permission-Based" (Cloud-dependent) to "Persistence-Based" (Edge-autonomous) control.
