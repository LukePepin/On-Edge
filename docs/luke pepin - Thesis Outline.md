DECENTRALIZED ZKP AUTHORIZATION MESHES FOR INDUSTRIAL ROBOTICS IN DIL ENVIRONMENTS OUTLINE  
BY  
LUKE PEPIN

**ADMIN** \- Format for Thesis was downloaded online from URI website along with Harishjitu’s and Stephen’s Theses for reference. The current plan is to write chapters here and import the text over to limit issues with formatting until they become critical.  
**ABSTRACT** \- I plan to fully rewrite my abstract once the paper is completed so it acts as a true summary of the work completed, however for review purposes I did include a very early version of what it may look like on page 5\.  
**ACKNOWLEDGMENTS** \- Harishjitu has a very nice Acknowledgement section I intend to base mine off. Obviously Dr. Sodhi is my primary acknowledgement. I would however like to make the addition of thanking the lab group as whole as well as more specific maybe 1 sentence individual thankful messages to both outside committee members given it was Dr. Maier-Speredelozzi’s recommendation which led me here to URI and for Dr. Sun thanks her for allowing me to participate in CYPHER (I’ll find a better way to phrase it, hopefully Dr. Sodhi has suggestions).  
**PREFACE \-** The thesis is most likely going to be a standard format, unlike Harishjitu’s with 2 manuscripts, there is a slight possibility that mine could be a 2 manuscript paper dividing the UR5 in person summer work and the NS-3 simulations to be run over the fall break but it's unlikely. I will also most likely not be using the CYPHER AI markings which they would be here if I did, no requirement I would prefer to omit them, they are no benefit and no harm missing. A small note on AI usage may be included for academic transparency. Any notes on security/CUI may be placed here. Lastly, over the fall if I investigate property disclosure and have any substantial progress there with a potential business then I will include that note. Overall this section most likely wouldn’t exist but there is a possibility that it could include all those elements.  
**LIST OF TABLES** The following tables index the empirical data extracted from the physical validation campaigns and NS-3 network simulations. These datasets provide the quantitative foundation required to assess the cyber-physical trade-offs of decentralized edge-first authentication

* Table 1: System Hardware and Star Topology Parameters – This table defines the physical, memory, and electrical parameters of the supervisor node, the edge microcontrollers, and the industrial robotic manipulator within the star topology. Expected Location: Chapter 3 (System Architecture) .   
* Table 2: QoS Middleware Optimization Comparison – A performance matrix comparing default reliable middleware profiles against optimized best-effort settings to show how buffer-induced bottlenecks are removed. Expected Location: Chapter 5 (Middleware Optimization) .   
* Table 3: 18-Config Transition and Latency Results – This table compiles the mean recovery times, trust eviction latency, and physical joint overruns recorded across our 18 fractional factorial experimental configurations. Expected Location: Chapter 4 (Empirical Validation).   
* Table 4: Statistical Security Tax Analysis – An evaluation of the bare-metal computational overhead of zero-knowledge selective disclosure compared to elliptic curve cryptography on the edge hardware. Expected Location: Chapter 4 (Empirical Validation) .   
* Table 5: NS-3 M/D/1 Queue Saturation Data – This table logs the traffic intensity and average packet delay used to mathematically map the true deterministic stability limit of the edge nodes. Expected Location: Chapter 5 (Middleware Optimization) .

**LIST OF FIGURES** The subsequent list indexes the figures and diagrams compiled directly from empirical telemetry and simulated network runs . These visual assets illustrate the mechanical and digital transition states of the cyber-physical system under adversarial network stress.

* Figure 1: Centralized Security Fragility vs. Decentralized Edge Star Topology – A schematic comparing the backhaul dependency of cloud-managed industrial networks against local, serial-tethered edge architectures . Expected Location: Chapter 3 (System Architecture).   
* Figure 2: H1' Trust Score Decay Under Jamming – A timeseries timeline plotting the decay of the probabilistic trust score against the eviction threshold under 25%, 50%, and 75% packet loss. Expected Location: Chapter 4 (Empirical Validation) .   
* Figure 3: Supervisor Cryptographic Latency Comparison – Grouped bar charts visualizing the absolute verification latency differences between elliptic curve and zero-knowledge algorithms on the supervisor workstation . Expected Location: Chapter 4 (Empirical Validation).   
* Figure 4: Embedded Worker Computational Feasibility – Boxplots demonstrating the execution time distribution of segmented cryptographic payloads running on the bare-metal microcontroller . Expected Location: Chapter 4 (Empirical Validation).   
* Figure 5: Queue Saturation Boundary and Network Latency Divergence – A dual-axis plot demonstrating the queue saturation limits and timeout rates of optimized and unoptimized middleware configurations as node density scales . Expected Location: Chapter 5 (Middleware Optimization).   
* Figure 6: Integrated Safety Response Budget Waterfall – A stacked budget waterfall chart mapping processing, serial transmission, and mechanical stopping delays of our 18-config trials against the functional safety limit . Expected Location: Chapter 6 (Kinematic Deceleration).

**CHAPTERS \-** Here is my ‘table of contents’ for the outline, below are the chapters listed and their titles. Each chapter's individual outlines will be written below after abstract. I’ve opted to include specific titles for each chapter to better frame my work.

* **CHAPTER 1 \- INTRODUCTION & THREAT MODEL:** Define the "Cloud-First Kill Switch" and the Coalition Logistics Threat Model (this probably needs to be professionalized for academic integrity, I can use the example but I think I need a professional threat model to use) to justify decentralized, privacy-preserving edge-first authentication.  
* **CHAPTER 2 \- LITERATURE REVIEW & DIL GAP:** Establish the critical academic gaps in decentralized Industrial Control Systems (ICS) authentication and real-time middleware performance under network degradation .  
* **CHAPTER 3 \- EDGE-COMPUTE STAR TOPOLOGY METHODOLOGY:** Document the physical hardware layout and mathematical formulation of the decentralized "Cloud-Edge-Cloud" state machine .  
* **CHAPTER 4 \- EMPIRICAL VALIDATION: RESILIENCE (H1') & SECURITY TAX (H2a/b):** Present the physical testing results of the 2×3×3 Fractional Factorial matrix and cycle-accurate silicon-level profiling .  
* **CHAPTER 5 \- QUEUE SATURATION & HARDWARE OPTIMIZATION:** Map the queuing dynamics of the Pi 4 supervisor node during multi-node post-partition network recovery (boot storm) .  
* **CHAPTER 6 \- KINEMATIC DECELERATION & THE HARDWARE STO BYPASS:** Resolve the mechanical-computational isolation boundaries and the integration of the hardware fail-safe bypass on the Universal Robots UR5 .  
* **CHAPTER 7 \- COMMERCIAL & DEFENSE IMPLICATIONS:** Translate the empirical safety-boundary and queueing results into a dual-use technical transition strategy .

**PLANS & UPDATES \-** This section formally documents the structural systems engineering pivots from the Thesis Proposal with the current finalized Outline.

* **Architectural & Hardware Pivots:**  
  * **Topology Reclassification (Star vs. MANET):** The architecture has been formally reclassified from a Mobile Ad-hoc Network (MANET) to a Decentralized Edge-Compute Star Topology. This pivot strips the heavy micro-ROS middleware from the edge nodes in favor of a raw serial JSON bridge, mathematically protecting the 256KB SRAM constraint of the Cortex-M4 and preventing stack-heap collisions during Zero-Knowledge Proof (ZKP) execution.  
  * **Hardware STO Lock (UR5 vs. Niryo):** The robotic hardware specification has been permanently upgraded from the Niryo Ned2 to the Universal Robots UR5. This is electrically mandated to execute the 24V PNP Optocoupler Safe Torque Off (STO) hardware bypass, which cannot be physically modeled on the Niryo's 15V stepper architecture.  
  * **18 Config Pivot**: This research delivers a dynamic, resilient "Cloud-Edge-Cloud" state machine designed to reinforce centralized industrial backhaul by enabling autonomous, edge-first cryptographic survival during backhaul connection partitions . To evaluate this full-system transition, we implement a 2×3×3 fractional factorial design across 18 distinct configurations, systematically analyzing the cyber-physical sensitivity of localized authentication tiers (ECC vs. ZKP) under varying jamming rates (25%, 50%, 75% loss) and trust decay parameters (α∈{0.1,0.3,0.5}) . By stripping the threshold-based sentinel rejoin window from the main ANOVA matrix to prevent statistical smearing, we relegate the final "partition-then-rejoin" phase to a qualitative demonstration proving that local transactions can securely reconcile with the cloud IdP upon connection restoration . This unified architecture resolves the "Safety-Reliability Paradox" by demonstrating that local edge-meshes successfully enforce the ISO 13849-1 500ms safety limit under severe jamming, while preserving continuous data integrity and state-synchronization for the broader enterprise network .  
* **The 9-Day In-Person Hardware Sprint:**  
  * With laboratory access concluding in 9 days, the immediate operational focus is strictly limited to extracting all physical UR5 kinematic deceleration telemetry and isolating the true M/D/1 queueing service rate ($\\mu$) of the Raspberry Pi 4 under optimized QoS middleware profiles.  
* **Hardware Gating Factor:**  
  * The critical $n=10$ concurrent node saturation sweep is currently gating upon the delivery of a 60W externally powered USB 3.0 hub. This external power delivery is electrically mandated to prevent under-voltage brownouts and CPU throttling across the Raspberry Pi supervisor during simultaneous cryptographic boot storms.  
* **Fall Semester Transition:**  
  * Once the physical baseline hardware telemetry is completely frozen and extracted to the repository, the Fall semester will pivot entirely to remote work. The focus will be ingesting these empirical baselines into the NS-3 discrete-event simulator to mathematically extrapolate the queueing stabilization boundaries under simulated Electronic Warfare (EW) conditions.

# **Start of Writing**

**ABSTRACT**   
When completed, this abstract will state that traditional Cloud-First Identity Providers (IdPs) create catastrophic "kill switch" vulnerabilities in DoD Contested Logistics, causing involuntary safety halts during network jamming. To mitigate this, the thesis proposes a Decentralized Edge-Compute Star Topology utilizing Zero-Knowledge Proof (ZKP) selective disclosure. This architecture specifically addresses the Coalition Logistics threat model, allowing foreign allied robotic nodes to prove authorization lease possession without exposing classified cryptographic keys to the local supervisor. Empirical profiling demonstrates that segmenting payloads invokes the Central Limit Theorem, bounding Cortex-M4 execution variance to securely operate within the strict ISO 13849-1 500ms mechanical fail-safe boundary. Furthermore, this research corrects traditional M/M/1 queueing assumptions by optimizing ROS 2 CycloneDDS QoS profiles (BEST\_EFFORT), eliminating artificial Head-of-Line blocking and exposing the true deterministic M/D/1 processing limits of the network. The thesis concludes by proving that an Opto-Isolated 24V Safe Torque Off (STO) hardware bypass, driven by an Exponentially Weighted Moving Average (EWMA) Trust Score, successfully arrests the Universal Robots UR5 manipulator's momentum beneath the 500ms ceiling, overriding software serialization delays entirely

**CHAPTER 1 \- INTRODUCTION & THREAT MODEL**  
This chapter establishes the irrefutable operational reality: Cloud-dependent architectures are fundamentally incompatible with Disconnected, Intermittent, and Limited (DIL) environments because network loss triggers involuntary kinetic halts . By mathematically defining the "Cloud-First Kill Switch" and the strict 500ms ISO 13849-1 functional safety boundary, this section frames the exact physical vulnerabilities that the Decentralized Edge-Compute Star Topology was engineered to solve.

**1.1 The Industry 4.0 Authentication Paradigm (Cloud-First Fragility)**

* Modern autonomous supply chains and Manufacturing Execution Systems (MES) rely almost exclusively on centralized architectures utilizing standardized protocols (e.g., OAuth 2.0) for identity verification and authorization.  
* In undisturbed network topologies, this centralized Identity Provider (IdP) model is highly efficient, allowing for rapid scaling and credential management.  
* *Note to self:* Ensure the distinction between routine factory network latency and explicit "denied environments" is established early.

**1.2 The Threat Model: Contested Logistics, Kill Switches, and Coalition Privacy**

* In DoD Contested Logistics theaters subjected to Electronic Warfare (EW) and targeted signal jamming, the reliance on a central server transforms the IdP into a catastrophic single point of failure, triggering an involuntary "Kill Switch" that paralyzes functional equipment .  
* Commercially, this fragility translates to massive financial liability, contributing to the estimated $400 billion annual cost of unplanned downtime.  
* **The Coalition Requirement:** In joint-force deployments, allied or multi-tenant robotic nodes must prove they hold a valid authorization lease to the supervisor *without* exposing classified cryptographic keys or proprietary identity protocols over contested airwaves. This mandates a privacy-preserving authentication mechanism.

**1.3 The Kinematic Boundary: ISO 13849-1 Functional Safety**

* Industrial functional safety standard ISO 13849-1 mandates that if a safety constraint or authorization lease is violated, the heavy robotic actuator (e.g., Universal Robots UR5) must be halted within a strict temporal ceiling to prevent kinetic damage.  
* For this architecture, this fail-safe boundary is defined as an absolute maximum latency of $500ms$.  
* Therefore, any localized authentication recovery mechanism must execute its complete cryptographic pipeline and network transmission in under 500ms (Mean Time To Recovery $\<500ms$) to safely bypass a Category 0 safeguard stop.

**1.4 The Proposed Solution: Decentralized Edge-Compute Star Topology**

* To decouple operational continuity from backhaul availability, this thesis proposes an "Edge-First" decentralized framework utilizing a Star Topology to protect the 256KB SRAM limits of edge microcontrollers.  
* Nodes verify each other utilizing Zero-Knowledge Proofs (ZKP) with attribute selective disclosure. This explicitly solves the Coalition Threat Model by allowing mathematical proof of authorization without key exposure.  
* Network integrity is tracked locally using an Exponentially Weighted Moving Average (EWMA) Probabilistic Trust Score.  
* *Note to self:* Must emphasize that mathematically proving the hardware can process this ZKP "security tax" fast enough to satisfy the $500ms$ ISO 13849-1 constraint is the core systems engineering challenge of this thesis.

**CHAPTER 2 \- LITERATURE REVIEW & DIL GAP**  
This chapter systematically evaluates the state-of-the-art in decentralized authentication mechanisms, explicitly identifying the disconnect between theoretical cryptographic advances and the physical realities of expeditionary manufacturing. By mapping current research against the constraints of Disconnected, Intermittent, and Limited (DIL) environments, this section exposes critical academic gaps regarding Cortex-M4 execution limits, Mean Time to Recovery (MTTR) baselines under severe packet loss, and the absence of mathematically quantified probabilistic trust models.

**2.1 The Resilience Gap (MTTR in DIL Environments)**

* Existing literature predominantly focuses on hybrid fog-cloud architectures rather than achieving pure Edge-First autonomy.  
* Current decentralized authentication studies completely fail to empirically measure Mean Time to Recovery (MTTR) under high-latency, \>20% packet loss conditions.  
* *Note to self:* Emphasize that without established MTTR baselines under physical network disruption, theoretical recovery claims cannot be validated against the $500ms$ functional safety threshold.

**2.2 The Security Tax Gap (Cortex-M4 Limits & Coalition Privacy)**

* While recent studies demonstrate Zero-Knowledge Proof (ZKP) feasibility on Cortex-A (Raspberry Pi 4\) hardware, they frequently ignore the massive memory overhead required for proof generation and entirely fail to benchmark on constrained Cortex-M4 architectures.  
* Existing literature fails to justify the computational penalty of ZKPs by mapping it to the privacy-preserving selective disclosure requirements necessary for allied Coalition Logistics environments.  
* *Note to self:* This dual gap directly justifies the necessity of Phase 2 hardware profiling to quantify the true algorithmic security tax of ZKPs on the Arduino Nano 33 BLE.

**2.3 The Probabilistic Trust Gap (Binary vs. Decay Models)**

* State-of-the-art decentralized trust models remain predominantly binary (authenticated/rejected) or rely on abstract, unquantified reputation systems.  
* No existing frameworks implement continuous, mathematically quantified trust decay parameters ($\\alpha$) to gracefully handle intermittent connectivity gaps  
* The absence of these parameters requires the formulation of the novel Exponentially Weighted Moving Average (EWMA) model ($\\Gamma(t+1) \= \\alpha \\times \\Gamma(t) \+ (1-\\alpha) \\times N\_0$) to maintain operational continuity safely.

**2.4 The Scalability and Safety Gap (Middleware QoS & ICS Integration)**

* Scalability testing in current decentralized robotics rarely exceeds $n=5$ nodes and fails to evaluate middleware Quality of Service (QoS) saturation .  
* The literature ignores artificial Head-of-Line (HoL) blocking caused by default `RELIABLE` DDS profiles, failing to evaluate the true deterministic M/D/1 processing limits of edge supervisors .  
* Furthermore, the literature completely ignores the integration of authentication failures with Industrial Control System (ICS) safety mechanisms, providing no architectural guidance for triggering 24V Safe Torque Off (STO) hardware failsafes to prevent adversarial kinetic injections.

**CHAPTER 3 \- EDGE-FIRST TOPOGRAPHICAL METHODOLOGY**  
This chapter defines the physical hardware topology and mathematical architecture required to execute decentralized authentication at the tactical edge. By offloading cryptographic verification to severely constrained microcontrollers via a Star Topology, integrating a time-decaying probabilistic trust equation, and strictly bridging cryptographic verification to robotic kinematics, this section operationalizes the framework capable of defending the $500ms$ ISO 13849-1 safety boundary.

**3.1 Localized Hardware Configuration (Edge-Compute Star Topology)**

* The physical architecture abandons peer-to-peer wireless mesh routing (MANET) in favor of a Decentralized Edge-Compute Star Topology.  
* A single Raspberry Pi 4 (ARM Cortex-A72) functions as the central routing arbiter and Supervisor Node, handling the ROS 2 DDS middleware.  
* Nine Arduino Nano 33 BLE microcontrollers (ARM Cortex-M4) function as the compute spokes, severely resource-constrained worker nodes executing the privacy-preserving ZKP selective disclosure.

**3.2 The SRAM Constraint & Serial JSON Bridge Pivot**

* Theoretical cryptographic frameworks frequently ignore physical silicon constraints. The Cortex-M4 processors are limited to an absolute maximum of 256KB of Static RAM (SRAM).  
* Native micro-ROS middleware consumes over 150KB of memory, which triggers silent, catastrophic stack-heap collisions during ZKP dynamic memory allocation.  
* To mathematically protect the 256KB memory boundary, the heavy middleware is stripped from the edge. Nodes output lightweight cryptographic telemetry via a Raw Serial JSON Bridge to the Pi 4 supervisor, completely isolating algorithmic execution from transport overhead.

**3.3 Cryptographic Action Script Verification (Kinematic Triggering)**

* To translate cryptographic authentication into physical motion, the architecture mandates a strict verification pipeline. Predefined ROS 2 kinematic trajectories are cryptographically hashed and stored on the Pi 4 supervisor.  
* A valid ZKP attribute disclosure from an edge node successfully validates the Probabilistic Trust Score ($\\Gamma$) and mathematically unlocks the specific trajectory hash.  
* *Note to self:* Detail the exact middleware transition here. Explain how this cryptographic unlock transitions from the Python-based ZKP verifier into dispatching a goal via the ROS 2 `FollowJointTrajectory` Action Server directly to the Universal Robots UR5 controller.

**3.4 Probabilistic Trust & The EWMA Formulation**

* To replace binary authentication, the architecture implements a continuous Exponentially Weighted Moving Average (EWMA) trust score to evaluate node integrity: $\\Gamma(t+1) \= \\alpha \\times \\Gamma(t) \+ (1-\\alpha) \\times N\_0$.  
* The $\\alpha$ (decay factor) dictates how rapidly trust evaporates during network disconnection, while $N\_0$ represents the binary success of the cryptographic verification.

**CHAPTER 4 \- EMPIRICAL VALIDATION: RESILIENCE (H1) & SECURITY TAX (H2)** 

This chapter transitions from architectural theory to physical empirical validation by explicitly testing the corrected core hypotheses. First, it evaluates **Hypothesis 1' (Crossover):** *"There exists a packet-loss threshold ($p^*$) below which centralized OAuth 2.0 has lower MTTR than the Edge-First Star Topology, and above which the ordering reverses"\*. Second, it evaluates **Hypothesis 2a/b (Selective Disclosure Cost):** *"Schnorr ZKP incurs a higher latency than ECDSA, representing the quantifiable computational tax required to enable the non-disclosure privacy properties necessary for Coalition Logistics"*. By subjecting the physical testbed to synthetic signal jamming and cycle-accurate hardware profiling, this section mathematically proves the decentralized framework's viability.

**4.1 H1' Validation: The Crossover Threshold ($p^\*$) Under DIL Conditions**

* To validate H1', the physical testbed is subjected to a packet-loss sweep (0% to 30%) utilizing Linux Traffic Control (`tc`) and Scapy manipulation at the transport layer to simulate active Electronic Warfare (EW) jamming.  
* By comparing the Mean Time To Recovery (MTTR) of the centralized Cloud-IdP baseline against the local Edge-Compute Star Topology, this section mathematically isolates the exact packet-loss crossover threshold ($p^\*$) where the decentralized architecture becomes operationally superior.  
* *Note to self:* Emphasize that finding $p^\*$ provides the exact telemetry threshold required for an autonomous robotic cluster to sever its reliance on a jammed centralized server and fall back to the edge.

**4.2 H2a/b Validation: The Coalition Privacy Tax (Cortex-M4 Profiling)**

* To validate H2a/b, cryptographic operations are empirically benchmarked natively on the Arduino Nano 33 BLE (ARM Cortex-M4) worker nodes and Raspberry Pi 4 supervisor  
* Standard timing functions (`millis()`) are bypassed in favor of the `DWT_CYCCNT` hardware register. Operating at 64 MHz, this isolates the true CPU algorithmic tax with deterministic 15.625-nanosecond precision by ignoring RTOS interrupt jitter.  
* Results confirm that upgrading from baseline ECC/ECDSA to Schnorr/ZKP selective disclosure incurs a 22.85% "Security Tax" (latency overhead).  
* *Note to self:* Explicitly state that this 22.85% penalty is not merely an inefficient delay, but the mandatory, mathematically quantified cost of enabling the privacy-preserving attribute selective disclosure required for multi-tenant Coalition Logistics.

**4.3 Payload Stabilization and The Central Limit Theorem (CLT)**

* Initial hardware profiling reveals that processing a single, highly complex ZKP attribute causes severe, unpredictable latency spikes, threatening the 500ms safety ceiling and causing false-positive EWMA trust evictions.  
* By segmenting the payload into distinct bytes—each possessing an independent algorithmic complexity—the architecture invokes the Central Limit Theorem (CLT).  
* **CRITICAL CORRECTION:** The computational variances do *not* "cancel out." Rather, as the number of independent cryptographic operations ($n$) increases, the sum of these operations converges to a normal Gaussian distribution, bounding the variance by a factor of $\\frac{\\sigma}{\\sqrt{n}}$ according to the Berry-Esseen theorem.  
* *Note to self:* Conclude by graphing how this statistical normalization drastically reduces the probability of long-tail latency spikes, mathematically tightening the execution into a deterministic window that safely operates within the 500ms ISO 13849-1 mechanical fail-safe boundary.

**CHAPTER 5 \- QUEUE SATURATION & LIVELOCK VALIDATION (H'3)**  
This chapter subjects the Decentralized Edge-Compute Star Topology to concurrent node density stress testing to identify the true mathematical failure boundaries of the network. It explicitly evaluates **Hypothesis 3' (Queue Saturation):** *"As node density ($n$) increases, authentication latency follows an M/D/1 queue formula due to deterministic ZKP service times ($\\mu$), diverging exponentially as arrival rates ($\\lambda$) reach the true physical saturation boundary ($n^*$) once artificial middleware bottlenecks are removed"\* . By eradicating default middleware misconfigurations, this section establishes the true processing limits of the Pi 4 supervisor within the Coalition Threat Model.

**5.1 The Artificial "Scalability Wall" (QoS Misconfiguration)**

* Initial boot storm testing (simulating concurrent reconnects following a network partition) falsely identified a Livelock threshold at exactly $n=12$ nodes.  
* Deploying a ROS 2 `MultiThreadedExecutor` (with 4 parallel threads) failed to reduce the 45% timeout rate, proving the failure was not CPU saturation, but First-In-First-Out (FIFO) Head-of-Line (HoL) blocking.  
* *Note to self:* Emphasize that this HoL blocking was an artificial bottleneck caused by default ROS 2 CycloneDDS Quality of Service (QoS) profiles (`RELIABLE` / `KEEP_ALL`), which stubbornly exhausted network buffers attempting to deliver stale, expired authentication packets .

**5.2 The M/D/1 Deterministic Queue Correction**

* Traditional scalability evaluations frequently assume exponential service times, incorrectly mapping behavior to an M/M/1 queue model.  
* However, because Chapter 4 successfully invokes the Central Limit Theorem (CLT) to bound the Cortex-M4 ZKP execution into a strict 301ms to 346ms window, the cryptographic service time ($\\mu$) is highly deterministic.  
* Therefore, the architecture's queueing dynamics must be mathematically corrected and evaluated strictly as an **M/D/1 (Deterministic) queue**.

**5.3 Middleware Optimization (BEST\_EFFORT & Depth=1)**

* To isolate the true M/D/1 processing limit, the ROS 2 CycloneDDS XML profiles are structurally optimized.  
* Transitioning the QoS reliability from `RELIABLE` to `BEST_EFFORT`, and modifying the history to `KEEP_LAST` with `Depth = 1`, forces the middleware to immediately drop stale authentication requests.  
* This specific optimization destroys the artificial network-layer HoL blocking, preventing the infinite timeout cascade and allowing the Pi 4 supervisor to process concurrent ZKP selective disclosures at its absolute maximum hardware capacity.

**5.4 NS-3 Extrapolation & True Saturation Boundary ($n^\*$)**

* Because physical provisioning caps the hardware testbed at 10 nodes, the deterministic M/D/1 service rate ($\\mu$) established via the QoS optimization must be ingested into an NS-3 discrete-event network simulator.  
* *Note to self:* Conclude this chapter by detailing how the NS-3 simulation applies Coalition Threat Model EW jamming characteristics to mathematically extrapolate the queueing stabilization boundaries, pinpointing the true maximum node density ($n^\*$) before the Star Topology suffers legitimate queue saturation

**CHAPTER 6 \- KINEMATIC DECELERATION & THE HARDWARE STO BYPASS**

This chapter bridges the gap between digital cryptographic verification and physical robotic kinematics. Software-based anomaly detection is operationally useless if the mechanical actuator cannot safely dissipate its kinetic energy before colliding with a human or workpiece. By integrating the Arduino's Probabilistic Trust Score ($\\Gamma$) with the Universal Robots UR5 industrial control box, this section details the engineered circumvention of ROS 2 software bottlenecks and mathematically proves that the Edge-Compute Star Topology successfully halts the manipulator within the strict 500ms ISO 13849-1 Category 0 safety ceiling.

**6.1 Trajectory Instability and Spline Explosions**

* Initial attempts to preempt the UR5 using strict $0.0$ velocity boundary conditions across temporally sparse waypoints forced the ROS 2 trajectory planner into quintic (5th-degree) spline interpolations.  
* This triggered a mathematical "whip-crack" anomaly, where the controller demanded a physically impossible acceleration spike of $82.3 \\text{ rad/s}^2$, forcing an involuntary trajectory abort and violating joint safety limits.  
* By deliberately under-constraining the boundary conditions, the system safely downgraded to a natural cubic spline interpolation, guaranteeing positional and velocity continuity during nominal execution prior to an attack.

**6.2 The Software Bottleneck (The 368ms Mode-Switch Penalty)**

* Initial safety preemption tests relied on injecting a high-priority native URScript command (`stopj(5.0)`) into the UR5 controller upon a trust eviction.  
* However, empirical telemetry revealed that transitioning from ROS 2 forward trajectory planning to the URScript interpreter introduced a catastrophic 368ms software mode-switching overhead .  
* This computational bloat caused early deceleration tests to completely fail the functional safety standard, requiring 1.3 seconds to achieve absolute zero velocity.

**6.3 The 24V PNP Optocoupler Bypass (Hardware STO)**

* *Note to self:* This is a critical cyber-physical engineering contribution. Software alerts are insufficient for mitigating cyber-attacks on high-speed industrial machinery.  
* To bypass the ROS 2 software latency, the architecture utilizes an "Active-High" hardware fail-safe. The Cortex-M4 Arduino worker node constantly outputs a 3.3V signal to a 24V PNP Optocoupler.  
* If the EWMA Trust Score drops below the eviction threshold of $30.0$ (due to simulated ZKP failure or network jamming), the Arduino immediately cuts the GPIO voltage.  
* This physically severs the 24V supply to the UR5's SI0/SI1 safety ports, triggering an un-hackable, instantaneous Category 0 Safeguard Stop (Safe Torque Off) completely independent of the ROS 2 software stack.

**6.4 Odometry Fusion and the Latency Boundary Proof**

* To irrefutably prove ISO 13849-1 compliance, a wrist-mounted 9-axis IMU continuously records the violent negative acceleration spike of the mechanical halt.  
* The raw telemetry is processed through an Extended Kalman Filter (EKF) to mathematically subtract the gravitational vector and integrate the true linear velocity over time.  
* The total system latency is mathematically verified using the equation: $T\_{total} \= T\_{crypto} \+ T\_{serial\_bridge} \+ T\_{network} \+ T\_{mechanical\_deceleration}$.  
* *Note to self:* Conclude the chapter by graphing this $T\_{total}$ curve to definitively prove that the hardware bypass crushes the deceleration timeline, successfully arresting the robot's momentum well under the 500ms safety boundary.

**CHAPTER 7 \- COMMERCIAL & DEFENSE IMPLICATIONS**

This chapter synthesizes the empirical hardware validations, M/D/1 queueing proofs, and cyber-physical STO bypass telemetry into a concrete, dual-use commercialization strategy. By proving that the Decentralized Edge-Compute Star Topology can maintain a Mean Time To Recovery (MTTR) below the strict 500ms ISO 13849-1 fail-safe boundary, this section demonstrates how the technology directly solves the "Cloud-First Kill Switch" vulnerability across both Department of Defense (DoD) contested theaters and commercial manufacturing sectors.

**7.1 The USMC EARC Beachhead Market (Defense Application)**

* The commercialization strategy establishes the USMC Combat Logistics Battalion (CLB) Expeditionary Automated Repair Cells (EARC) operating in A2/AD (Anti-Access/Area Denial) environments as the primary beachhead market.  
* Capturing this highly concentrated, networked community represents a calculated $5M Total Addressable Market (TAM), derived from outfitting approximately 25 active EARC systems at an estimated $200,000 per unit.  
* For these forward-deployed units, the architecture deploys the "Tactical Fortress" tier, utilizing the full Zero-Knowledge Proof (ZKP) selective disclosure to guarantee mission persistence and allied privacy under the Coalition Logistics Threat Model during intense Electronic Warfare (EW) jamming.

**7.2 The Commercial Manufacturing Liability ($400B Downtime)**

* The global commercial manufacturing sector suffers an estimated $400 billion in annual losses due to unplanned downtime, driven heavily by cloud-dependent authorization lease expirations and backhaul fragilities.  
* In high-throughput environments where unplanned downtime is a lethal financial liability, the architecture offers an "Industrial Sprint" tier.  
* This tier utilizes Elliptic Curve Cryptography (ECC) for environments where the primary operational threat is transient network instability (e.g., routine factory connectivity drops) rather than state-sponsored electronic warfare, optimizing for ultra-low latency recovery.

**7.3 The Dual-Use De-risking Strategy**

* The USMC combat deployment serves as the ultimate technical crucible to validate the systems engineering.  
* *Note to self:* Emphasize that proving the architecture can maintain a $500ms$ MTTR on a severely constrained 256KB SRAM Cortex-M4 budget under active EW jamming definitively de-risks the technology.  
* This combat-validated empirical proof is the mandatory strategic wedge required to successfully expand into the \>$10 billion commercial biopharmaceutical and heavy industry markets.

**7.4 The Persistence-Based Paradigm Shift**

* The chapter concludes by defining the necessary evolution of Industry 4.0 architectures.  
* By decoupling operational continuity from backhaul availability, the framework shifts the fundamental operational logic of industrial control systems from "Permission-Based" (Cloud-dependent) to "Persistence-Based" (Edge-autonomous).  
* This transition is not merely a localized software feature; it is a mandatory architectural baseline for national resilience and logistics in a contested world