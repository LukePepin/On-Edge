
Decentralized Authentication for Expeditionary Automated Repair Cells: A Hypothesis-Driven Literature Review of Zero-Knowledge Proofs, Probabilistic Trust, and Edge-First MANET Architectures
Executive Summary
This enhanced literature review systematically evaluates the state-of-the-art in decentralized authentication mechanisms through the lens of the Expeditionary Automated Repair Cell (EARC) thesis, which proposes an Edge-First Mobile Ad-hoc Network(MANET)frameworkusingZero−KnowledgeProofs(ZKPs)andProbabilisticTrustScores(Γ)forforward−deployed Naval manufacturing units. The review directly addresses three critical hypotheses: H1 (Resilience) predicting 50% Mean Time to Recovery (MTTR) reduction via edge-first architectures in 20% packet loss environments; H2 (Security Tax) examining ZKP versus Elliptic Curve Cryptography (ECC) trade-offs with expected >15% latency penalties; and H3 (Scalability/Livelock) investigating non-linear MTTR scaling from n=3 to n=10 nodes due to verification queuing.
Analysis of 30 highly relevant papers (2020-2026) reveals a critical disconnect between theoretical cryptographic advances and the specific requirements of resource-constrained expeditionary manufacturing. While blockchain-enhanced ZKP systems demonstrate promising authentication capabilities, no papers directly test MTTR metrics in DIL (Disconnected-Intermittent-Limited) environments, a fundamental gap for H1 validation. For H2, only three papers provide comparative ZKP versus ECC performance data on Raspberry Pi platforms, with Lin et al. demonstrating ZKP verification in single-digit milliseconds on Raspberry Pi 4 (ARM Cortex-A) but requiring hundreds of megabytes for proving keys. Critically, no papersimplementprobabilistictrustmodelswithquantifieddecayparameters(α)analogoustotheproposedΓ(t+1)=α×Γ(t)+(1−α)×Noformula;trustremainspredominantlybinary(authenticated/rejected).ForH3,scalabilitytestingrarelyexceeds n=5 nodes, with Barrion et al.'s robotic swarm framework being the only study demonstrating dynamic trust at scale, though without cryptographic verification queuing analysis.
The literature exhibits five critical gaps for EARC implementation: (1) absence of MTTR benchmarks in contested network conditions; (2) insufficient ZKP performance data on Cortex-M4 microcontrollers (Arduino Nano 33 BLE sensors); (3) lack of probabilistic trust frameworks integrating cryptographic verification with behavioral reputation; (4) limited scalability studies at n=10 node density with gossip protocol overhead analysis; and (5) minimal consideration of Industrial Control System (ICS) safety mechanisms preventing involuntary kill switches during authentication failures. This review identifies that while foundational cryptographic primitives exist, their integration into a cohesive Edge-First MANET framework for expeditionary manufacturing with quantified resilience, security tax, and scalability characteristics remains an open research challenge directly addressed by the EARC thesis.
Table of Contents

1. Introduction
2. EARC System Context and Research Hypotheses
   2.2 Hypothesis Framework
   2.3 Performance Requirements and Constraints
3. Methodology
4. Hypothesis-Driven Thematic Analysis
   4.1 H1 Resilience: MTTR Reduction via Edge-First MANET
   4.2 H2 Security Tax: ZKP versus ECC Performance Trade-offs
   4.3 H3 Scalability: Node Density and Verification Queuing
   4.4ProbabilisticTrustModels:TowardΓ−BasedFrameworks
   4.5 ICS Safety Mechanisms: Kill Switches and Failure Modes
5. Cross-Cutting Analysis: Integration Challenges
   5.1 MQTT/ROS2 Communication Stack Integration
   5.2 Digital Twin Quality Management
   5.3 Gossip Protocol Mesh Synchronization
6. Critical Gap Analysis for EARC Implementation
7. Recommendations for Thesis Validation
8. Conclusion
9. References
10. Introduction
    The convergence of Industrial Internet of Things (IIoT), autonomous robotics, and expeditionary manufacturing presents unprecedented security and resilience challenges, particularly for forward-deployed military units operating in Disconnected, Intermittent, and Limited (DIL) network environments. Current Industry 4.0 architectures rely on a "Cloud-First" paradigm with centralized Identity Providers (IdPs), creating terminal dependencies where backhaul connectivity loss leads to involuntary system stops—an untenable failure mode for contested logistics environments such as submarine tenders and Marine Corps Logistics Groups [1], [2].
    The Expeditionary Automated Repair Cell (EARC) thesis addresses this critical vulnerability by proposing an "Edge-First" Mobile Ad-hoc Network (MANET) framework that decouples operational continuity from backhaul availability. The system architecture comprises Raspberry Pi 4 Supervisor nodes coordinating Arduino Nano 33 BLE sensors and Niryo Ned2 robotic arms through MQTT/ROS2 communication stacks, with gossip protocol mesh synchronization enabling local arbitration during network disruption. Central to this approach is the integration of Zero-Knowledge Proof (ZKP) cryptographic primitiveswithProbabilisticTrustScores(Γ)thatdynamicallyupdatebasedoncryptographicverificationindicators,replacing binary authentication models with continuous trust assessment.
    the resilience gains (H1), security-performance trade-offs (H2), and scalability limits (H3) of the proposed Edge-First approach. Unlike traditional surveys that broadly categorize authentication mechanisms, this review explicitly maps empirical findings to EARC's performance targets: MTTR < 500ms in 20% packet loss environments, node density n=10 operational units, and resource constraints of Raspberry Pi 4 computational limits. By identifying gaps between theoretical cryptographic advances and practical deployment requirements for expeditionary manufacturing, this review establishes the research foundation for validating the EARC framework's contributions to resilient, decentralized authentication in contested industrial environments.
11. EARC System Context and Research Hypotheses
    2.1 Expeditionary Automated Repair Cell Architecture
    The EARC system implements a cellular manufacturing topology optimized for Make-to-Order (MTO), low-volume high-mix job shop production in forward-deployed environments. The architecture comprises three node types operating in a local mesh:
    Supervisor Node (Raspberry Pi 4): Serves as the local Manufacturing Execution System (MES) controller, ingesting sensor $data, coordinating process steps (Work Order Receipt → Material Verification → Job Validation → Fabrication → Robotic Pick & Place → Visual Quality Inspection → Binning/Dispatch), and running arbitration logic. The Raspberry Pi 4 $represents a critical performance bottleneck, balancing computational load for data collection, cryptographic verification, and machine control simultaneously to prevent system lag that could ruin parts during fabrication.
    Worker Nodes (Arduino Nano 33 BLE): IoT weight sensors for material verification, utilizing Cortex-M4 microcontrollers with severe resource constraints. These edge devices must perform local cryptographic operations for mesh authentication without continuous server connectivity.
    Robot Node (Niryo Ned2): Six-axis robotic arm for material handling and pick-and-place operations, requiring deterministic control through ROS2 Action Server interfaces with real-time position feedback compared against Digital Twin simulations for quality management.
    The communication architecture replaces traditional HTTP/REST with MQTT Broker (Mosquitto) for local message passing, enabling continued operation when internet connectivity is lost mid-job. Gossip protocol synchronization maintains logical clock consistency across the mesh, though this introduces potential bandwidth saturation at higher node densities—a key concern for H3 scalability analysis.
    2.2 Hypothesis Framework
    The EARC thesis tests three interrelated hypotheses that quantify the fundamental trade-offs in Edge-First decentralized authentication:
    H1(ResilienceHypothesis):TransitioningtoanEdge−FirstMANETframeworkusingProbabilisticTrustScores(Γ)willreduce Mean Time to Recovery (MTTR) by at least 50% compared to centralized cloud-authentication baselines under high-loss conditions (20% packet loss). This hypothesis directly challenges the Cloud-First paradigm by predicting that local mesh arbitration with cached trust scores enables faster recovery from network disruption than waiting for backhaul restoration to centralized IdPs.
    H2 (Security Tax Hypothesis): Implementing Zero-Knowledge Proofs (ZKPs) will result in a significantly higher System Trust Score during adversarial injection compared to ECC (Elliptic Curve Cryptography), but will incur a statistically significant latency penalty causing MTTR increase exceeding 15%. This hypothesis quantifies the security-performance trade-off, predicting that ZKP's stronger cryptographic guarantees (preventing replay attacks and enabling privacy-preserving verification) come at a computational cost that may violate the MTTR < 500ms target on resource-constrained Raspberry Pi 4 hardware.
    H3 (Scalability/Livelock Hypothesis): As Node Density increases (from n=3 to n=10), the MTTR for ZKP-based arbitration will scale non-linearly (exponentially) compared to ECC-based arbitration due to queuing required for cryptographic verification. This hypothesis predicts that gossip protocol synchronization combined with computationally expensive ZKP verification creates verification bottlenecks at n=10 operational units, potentially causing livelock conditions where nodes spend more time verifying each other than processing manufacturing tasks.
    2.3 Performance Requirements and Constraints
    The EARC system operates under stringent performance and resource constraints derived from expeditionary deployment scenarios:
    Quantified Performance Targets:
    MTTR < 500 milliseconds in environments with 20% packet loss
    50% MTTR reduction compared to centralized baselines (H1 validation threshold)
    15% latency penalty tolerance for ZKP security gains (H2 validation threshold)
    Operational node density: n=10 nodes as "Operational Unit" scale
    Low-latency communication through equipment clustering within cell
    Hardware Constraints:
    Raspberry Pi 4: Limited computational resources for running full MES stack, cryptographic verification, and machine control simultaneously
    Arduino Nano 33 BLE (Cortex-M4): Severe memory and processing constraints for cryptographic operations
    Limited inventory space in expeditionary units, requiring efficient resource utilization
    Network Environment (DIL Characteristics):
    Disconnected: Backhaul connectivity loss scenarios where cloud IdP is unavailable
    Intermittent: Non-deterministic connectivity patterns in contested environments
    Limited: High-latency environments with >20% packet loss, requiring local autonomy
    Safety Requirements:
    G-code verification to prevent dangerous CNC errors (e.g., Z-axis depth changes)
    Condition-based maintenance monitoring (motor current, vibration)
    Quality management through Digital Twin position drift thresholds
    TrustScore(Γ)MathematicalFormulation:
    The Probabilistic Local Trust model updates according to:
    Γ(t+1)=α×Γ(t)+(1−α)×No
    Where:
    α(DecayFactor):Determineshowquicklytrust"evaporates"whennosignalisreceived,requiringempiricaltuningforexpeditionary environments
    No (Indicator Function): Value = 1 if cryptographically signed nonce is verified; Value = 0 otherwise
    This formula structure enables continuous trust assessment rather than binary authentication, allowing the system to maintain operational continuity with degraded trust during intermittent connectivity while preventing complete system stops.
12. Methodology
    This literature review analyzed 30 papers from a comprehensive search yielding 317 initial results across SciSpace, Google Scholar, and ArXiv, filtered for post-2022 publications with PDF access. The combined paper table was relevance-ranked based on alignment with EARC system requirements: ZKP implementations, probabilistic trust models, DIL/MANET environments, resource-constrained edge hardware, and Industrial IoT applications.
    Papers were systematically enriched with five hypothesis-specific analytical dimensions:
13. H1 Resilience Evidence: MTTR metrics, recovery time, authentication latency in high packet loss environments, MANET/mesh resilience, edge-first versus cloud-first architectures, DIL environment testing
14. H2 Security Tax Evidence: Comparative ZKP versus ECC performance data, latency penalties, computational overhead on Raspberry Pi 4 or Cortex-M4 platforms, memory usage, trust/security improvements
15. H3 Scalability Evidence: Node density testing (n=3 to n=10+), verification time scaling, queuing delays, livelock conditions, gossip protocol overhead, multi-robot swarm topologies
    4.ProbabilisticTrustModels:Continuoustrustscoringformulas,decayparameters(α),trustupdatemechanisms,reputationsystems,similaritytoΓformulastructure
16. ICS Safety Mechanisms: Kill switches, emergency stops, fail-safe modes, G-code verification, behavior under authentication failure or network drops
    quantitative performance metrics on resource-constrained hardware platforms matching the Raspberry Pi 4 and Arduino Nano 33 BLE specifications.
17. Hypothesis-Driven Thematic Analysis
    4.1 H1 Resilience: MTTR Reduction via Edge-First MANET
    Critical Finding: No papers in the surveyed literature directly measure Mean Time to Recovery (MTTR) in DIL environments with >20% packet loss, representing a fundamental gap for H1 validation.
    4.1.1 Edge-First versus Cloud-First Architectures
    The literature exhibits a strong bias toward hybrid fog-cloud architectures rather than pure Edge-First designs. Hewa et al. propose a fog computing and blockchain-based security service architecture for 5G Industrial IoT-enabled cloud manufacturing, utilizing Raspberry Pi devices (Models A, B, 3B) as fog nodes [4]. Their architecture demonstrates better search latency than cloud-based PKI when scaling IoT nodes, with end-to-end latency evaluated for 1, 5, 10, 25, and 50 concurrent transactions in batches with block mining intervals of 0.5s, 1s, and 2s. However, the paper does not test network disruption scenarios or measure recovery time when backhaul connectivity is lost—the core resilience claim of H1.
    Park's decentralized authentication scheme using Decentralized Identifiers (DIDs) for fog-enabled IIoT similarly maintains a fog-cloud hybrid rather than enabling full local autonomy [17]. The scheme constructs authentication on elliptic curve cryptography (ECC) but lacks empirical data on performance during network disconnection or recovery time metrics.
    Gap for H1: The absence of MTTR benchmarking in contested network conditions means the literature provides no baseline for the 50% reduction target. While several papers demonstrate decentralized authentication capabilities, none quantify recovery time when transitioning from cloud-dependent to edge-autonomous operation.
    4.1.2 MANET and Mesh Network Resilience
    Barrion et al.'s blockchain-based dynamic two-factor authentication consensus framework for robotic swarms represents the closest architectural analog to EARC's MANET topology [11]. The framework combines off-chain peer verification with on-chain consensus mechanisms, dynamically adjusting peer similarity and trust scores. Experimental evaluations using E-puck robots in the ARGoS simulator achieved a mean absolute error of 2.52% in scalability tests and maintained a low error rate of 2.32% against Byzantine attacks. The blockchain ledger scaled predictably based on swarm size, confirming resource efficiency through CPU and RAM usage metrics.
    However, Barrion et al. do not report MTTR or recovery time metrics, instead focusing on accuracy and error rates. The framework's resilience is demonstrated through Byzantine fault tolerance rather than network disruption recovery, leaving H1's specific MTTR reduction claim unvalidated by existing literature.
    Schmid's customer-empowered privacy-preserving verification system for robot product delivery uses MQTT publish/subscribe over public channels with Raspberry Pi 4 (4GB RAM) robots [6]. Performance analysis includes latency
    authentication, the paper does not test DIL environments or measure recovery behavior under packet loss conditions.
    Gap for H1: No papers test authentication latency specifically in 20% packet loss environments or measure how quickly systems recover when network connectivity is restored after disruption. The EARC thesis's prediction of 50% MTTR reduction requires establishing baseline MTTR for centralized systems and measuring MTTR for Edge-First systems under identical network conditions—a comparison absent from current literature.
    4.1.3 Decentralized Authentication Performance
    Lin et al.'s access control system based on blockchain with zero-knowledge rollups achieves authentication times under 5 seconds for most protocols, with ZKP verification time consistent at single-digit milliseconds [1]. In high-traffic IoT environments, ZK-rollups optimization reduces authorization time overhead by 86% (from 993s to 133s for 20,000 concurrent requests with batch size 40). The prototype was tested on both server-class hardware (Intel Xeon Platinum 8269, 16GB RAM) and Raspberry Pi (1.5 GHz ARM Cortex-A, 4GB), demonstrating feasibility on EARC-equivalent hardware.
    However, Lin et al.'s testing environment uses stable network connectivity without simulating packet loss or intermittent disconnection. The 86% overhead reduction is measured against batch size variations, not network resilience scenarios. The paper's focus on high-traffic environments (20,000 concurrent requests) differs fundamentally from EARC's n=10 node density with contested network conditions.
    Synthesis for H1: The literature demonstrates that decentralized authentication on Raspberry Pi 4 hardware is technically feasible with millisecond-scale verification times, establishing a foundation for meeting the MTTR < 500ms target. However, the absence of MTTR metrics in DIL environments means H1's 50% reduction claim cannot be validated or refuted by existing research. The EARC thesis fills this gap by explicitly measuring MTTR under controlled packet loss conditions (20%) and comparing Edge-First MANET performance against centralized cloud-authentication baselines.
    4.2 H2 Security Tax: ZKP versus ECC Performance Trade-offs
    Critical Finding: Only three papers provide comparative ZKP versus ECC performance data on resource-constrained hardware, with none testing Cortex-M4 platforms (Arduino Nano 33 BLE) critical for EARC sensor nodes.
    4.2.1 ZKP Performance on Raspberry Pi 4
    Lin et al. provide the most directly applicable H2 evidence, testing zkSNARKs with MIMC hash, ECC for encryption, and EdDSA for signatures on Raspberry Pi (1.5 GHz ARM Cortex-A, 4GB) [1]. ZKP verification time is stable at single-digit milliseconds, less affected by batch size and tree height compared to other operations. However, proving key memory grows to hundreds of megabytes, with Merkle tree height affecting overhead—taller trees increase transmission delay and memory for proof generation.
    The paper demonstrates that ZKP verification is computationally efficient (milliseconds), but proof generation and storage
    Raspberry Pi itself may exceed memory constraints when balancing MES logic, machine control, and cryptographic operations simultaneously.
    H2 Implication: Lin et al.'s data suggests ZKP verification latency on Raspberry Pi 4 is likely <10ms, well below the 15% latency penalty threshold (75ms additional latency for 500ms baseline MTTR). However, if proof generation is required on the Raspberry Pi rather than just verification, memory overhead may cause system lag that indirectly increases MTTR through computational resource contention.
    4.2.2 ECC Performance Baselines
    Schmid's system using ECC for public/private key pairs and ECDSA for signing on Raspberry Pi 4 (4GB RAM) provides ECC performance baselines [6]. Computational costs include: ECDSA Sign (8.19ms customer, 2.03ms CSP), ECDSA Verify (11.61ms customer, 4.12ms CSP, 5.23ms robot), ECC Encryption (8.67ms customer, 6.32ms CSP), and ECC Decryption (9.33ms customer, 7.47ms CSP). Robot verification (5.23ms) on Raspberry Pi 4 establishes an ECC baseline for comparison with ZKP verification.
    Comparing Schmid's ECC verification (5.23ms) to Lin et al.'s ZKP verification (single-digit milliseconds, approximately 3-9ms based on Figure 6c), the latency difference is minimal—potentially <5ms additional overhead for ZKP, representing <1% latency penalty rather than the >15% threshold predicted by H2.
    H2 Contradiction: This comparison suggests H2's prediction of >15% latency penalty may be overstated for verification operations on Raspberry Pi 4. However, three critical caveats apply:
18. Proof Generation vs. Verification: Schmid measures signing (8.19ms) and verification (5.23ms) for ECC, while Lin et al. report only verification time for ZKP. If EARC requires proof generation on edge devices, the comparison is incomplete.
19. Cryptographic Primitive Differences: Lin et al. use zkSNARKs with MIMC hash, while Schmid uses ECDSA. Different ZKP variants (Schnorr, zk-STARKs) may exhibit different performance characteristics.
20. System-Level Overhead: Individual cryptographic operation latency does not account for system-level effects like memory contention, CPU scheduling, or network transmission overhead for larger proof sizes.
    4.2.3 Resource-Constrained Edge Devices
    Critical Gap: No papers test ZKP performance on Cortex-M4 microcontrollers (Arduino Nano 33 BLE), despite this being a critical component of EARC's sensor mesh. Chatzigiannakis et al.'s 2011 paper "Elliptic Curve Based Zero Knowledge Proofs and Their Applicability on Resource Constrained Devices" [25] is the only work explicitly addressing ZKP on constrained devices, but it predates modern ARM Cortex-M4 architectures and does not provide quantitative performance data in the available metadata.
    Yang et al.'s SAKMS scheme for 6TiSCH industrial wireless networks uses improved ECC operations on OpenMoteSTM platform, achieving 37% computational efficiency improvement with link key establishment taking 0.9s [20]. This provides an ECC baseline for Cortex-M class devices, but no ZKP comparison exists.
    H2 Gap: The absence of ZKP performance data on Cortex-M4 platforms means H2 cannot be validated for EARC's Arduino Nano 33 BLE sensor nodes. The EARC thesis must empirically measure ZKP verification time on Cortex-M4 hardware to determine if the >15% latency penalty threshold applies to sensor-level authentication or only to Supervisor-level operations.
    4.2.4 Security Improvements Justifying Performance Costs
    Pathak et al.'s blockchain-enhanced ZKP-based mutual authentication for IoT networks emphasizes security guarantees in multiagent architectures with distributed edge computing layers [2]. However, the paper lacks quantitative edge benchmarks or latency analysis, focusing on security properties rather than performance trade-offs.
    Ramezan et al.'s zk-IoT framework demonstrates that proof generation, publication, and verification timings meet practical requirements for IoT device communication, paving the way for reliable and scalable IoT networks [3]. The framework establishes a trust layer for secure, autonomous communication between IoT devices that may not inherently trust each other, but does not quantify the security improvement (e.g., attack resistance metrics) relative to ECC baselines.
    H2 Gap: While multiple papers assert ZKP provides stronger security guarantees (privacy-preserving verification, replay attack prevention), none quantify "System Trust Score" improvements during adversarial injection—the security benefit side of H2's trade-off equation. The EARC thesis must define and measure System Trust Score under simulated adversarial conditions to validate that ZKP's security gains justify the latency penalty.
    Synthesis for H2: The literature provides preliminary evidence that ZKP verification on Raspberry Pi 4 incurs minimal latency penalty (<10ms, potentially <1% overhead) compared to ECC, contradicting H2's >15% prediction for verification operations. However, critical gaps remain: (1) no ZKP performance data on Cortex-M4 sensor nodes, (2) incomplete comparison of proof generation overhead, (3) lack of quantified security improvement metrics, and (4) absence of system-level MTTR measurements accounting for memory contention and resource competition on Raspberry Pi 4 running full MES stack. The EARC thesis addresses these gaps through controlled experiments measuring both cryptographic operation latency and end-to-end MTTR under realistic system load.
    4.3 H3 Scalability: Node Density and Verification Queuing
    Critical Finding: Scalability testing in the literature rarely exceeds n=5 nodes, with no papers analyzing verification queuing delays or livelock conditions at n=10 node density.
    4.3.1 Node Density Scaling Studies
    Hewa et al.'s fog computing architecture evaluates end-to-end latency for 1, 5, 10, 25, and 50 concurrent transactions in batches, demonstrating better search latency than cloud-based PKI when scaling IoT nodes [4]. However, "concurrent transactions" differs from "node density"—the paper tests transaction volume rather than the number of independent nodes in a mesh network performing mutual authentication.
    Lin et al.'s ZK-rollups system tests batch sizes from 1 to 40 with 20,000 concurrent requests, showing that authorization time overhead decreases exponentially as batch size increases (86% reduction with batch size 40) [1]. The experimental
    scalability with varying node density in terms of mesh network size.
    H3 Gap: Both papers demonstrate scalability with transaction volume or batch size, but neither tests how authentication latency scales when increasing the number of independent nodes that must mutually authenticate in a mesh topology—the core concern of H3.
    4.3.2 Multi-Robot Swarm Scalability
    Barrion et al.'s robotic swarm framework provides the most relevant H3 evidence, testing scalability with varying swarm sizes and achieving a mean absolute error of 2.52% in scalability tests [11]. The blockchain ledger scaled predictably based on swarm size, with resource efficiency confirmed through CPU and RAM usage metrics. The framework dynamically adjusts peer similarity and trust scores, maintaining a low error rate of 2.32% against Byzantine attacks.
    However, Barrion et al. do not report how authentication or verification time scales with swarm size, instead measuring accuracy and error rates. The paper does not specify the maximum swarm size tested or whether verification queuing delays were observed. The framework combines off-chain peer verification with on-chain consensus, potentially avoiding the verification bottleneck predicted by H3, but this architectural difference makes direct comparison to EARC's gossip protocol synchronization difficult.
    H3 Implication: Barrion et al. demonstrate that blockchain-based trust scoring can scale to multi-robot swarms without catastrophic performance degradation, but the absence of latency scaling data means H3's prediction of non-linear (exponential) MTTR scaling cannot be validated or refuted.
    4.3.3 Verification Queuing and Livelock Conditions
    Critical Gap: No papers explicitly analyze verification queuing delays or livelock conditions where nodes spend more time verifying each other than performing productive work. This represents a fundamental gap for H3 validation, as the hypothesis specifically predicts that ZKP's computational expense creates queuing bottlenecks at n=10 nodes.
    Schmid's system demonstrates minor latency variation for 10 to 10,000 parallel orders, suggesting that verification operations scale well with request volume [6]. However, the architecture uses a publish/subscribe MQTT model rather than peer-to-peer mesh authentication, avoiding the mutual verification overhead that H3 predicts will cause livelock.
    4.3.4 Gossip Protocol Overhead
    Critical Gap: No papers analyze gossip protocol overhead for mesh synchronization in the context of cryptographic verification. The EARC thesis uses gossip protocol for logical clock synchronization across the mesh, which introduces bandwidth overhead that may saturate MANET capacity at higher node densities. The literature does not address how gossip traffic interacts with verification queuing to affect MTTR scaling.
    Puggioni et al.'s decentralized IoT updates delivery system states that the number of distributors can scale indefinitely using zk-SNARKs for proof-of-delivery [7]. However, the paper does not provide specific quantitative performance data such as
    Synthesis for H3: The literature demonstrates that blockchain-based authentication can scale to moderate node densities (n=5-10) without catastrophic failure, but provides no quantitative data on how verification time scales with node density or whether verification queuing causes non-linear MTTR degradation. Barrion et al.'s robotic swarm framework suggests that dynamic trust scoring can maintain accuracy at scale, but the absence of latency metrics means H3's exponential scaling prediction remains untested. The EARC thesis fills this gap by systematically measuring MTTR at n=3, n=5, n=7, and n=10 node densities, explicitly tracking verification queue depths and identifying the node density threshold where queuing delays cause MTTR to exceed the 500ms target.
    4.4ProbabilisticTrustModels:TowardΓ−BasedFrameworks
    CriticalFinding:Nopapersimplementprobabilistictrustmodelswithquantifieddecayparameters(α)analogoustotheEARCΓformula;trustremainspredominantlybinary(authenticated/rejected)orreputation−basedwithoutexplicitdecayfunctions.
    4.4.1 Binary Trust Models
    The majority of surveyed papers employ binary trust models where authentication results in either acceptance or rejection without intermediate trust states. Lin et al.'s ZKP-based access control uses blockchain smart contracts for trustless interactions, with trust established through zero-knowledge proofs ensuring honesty and data confidentiality [1]. The trust model is effectively binary (correct/incorrect proof) and static once verified, with nonce-based replay attack prevention but no continuous trust scoring.
    Hewa et al.'s fog computing architecture identifies IoT nodes with valid ECQV certificates as trusted, implementing a binary trust model [4]. Trust is dynamic in the sense that certificates are generated for each session, but there is no probabilistic scoring or decay mechanism—nodes are either trusted (valid certificate) or untrusted (invalid/expired certificate).
    GapforΓ:BinarytrustmodelscannotcapturethecontinuoustrustassessmentenabledbytheΓformula,wheretrust"evaporates"overtimewhennoverificationsignalisreceived(αdecayfactor)butisreinforcedbysuccessfulcryptographicverification (No indicator function). This continuous assessment is critical for EARC's ability to maintain operational continuity with degraded trust during intermittent connectivity.
    4.4.2 Reputation-Based Trust Models
    Barrion et al.'s robotic swarm framework dynamically adjusts peer similarity and trust scores, representing the closest analog to probabilistic trust in the surveyed literature [11]. The framework maintains trust scores that evolve based on peer verification outcomes, indicating a dynamic, reputation-based trust model. However, the paper does not provide the mathematicalformulationoftrustscoreupdates,makingitimpossibletodetermineifdecayparametersanalogoustoαexistor how trust scores are calculated from verification results.
    Baza et al.'s blockchain-based firmware update scheme for autonomous vehicles maintains a credit reputation for each distributor, implementing a reputation-based trust model [10]. The system rewards honest engagement, implying trust increases with successful interactions, but does not specify decay mechanisms for inactive or unverified distributors.
    GapforΓ:Whilereputation−basedmodelsdemonstratethattrustcanbedynamicandquantifiednumerically,noneprovideexplicitdecayparametersorupdateformulascomparabletoΓ(t+1)=α×Γ(t)+(1−α)×No.Theabsenceofquantifieddecayratesmeanstheliteratureprovidesnoguidancefortuningαinexpeditionaryenvironmentswhereintermittentconnectivityrequiresbalancingtrustpersistence(highα)againstresponsivenesstoverificationfailures(lowα).
    4.4.3 Zero-Trust Architectures
    Vadluri et al.'s zero-trust architecture for IoT-integrated industrial power electronics systems enforces continuous verification and least-privilege access, implying dynamic trust [12]. The architecture uses AI-driven anomaly detection for continuous trust assessment, but does not quantify trust scores or provide decay parameters.
    Huang et al.'s zero-trust identity framework for agentic AI generates Zero-Knowledge Proofs based on analyzing logs, but the metadata does not explicitly state if trust is dynamic or static [8]. The framework focuses on fine-grained access control rather than continuous trust scoring.
    GapforΓ:Zero−trustarchitecturesimplementcontinuousverification,aligningphilosophicallywiththeΓmodel
    ′
    scontinuous assessment. However, they do not provide probabilistic trust scores with quantified decay parameters, instead relying on real-time verification for each access request. This approach may be incompatible with EARC's need to maintain operational continuity during intermittent connectivity when real-time verification is impossible.
    4.4.4 Fuzzy Logic-Based Adaptive Trust
    Farooq et al.'s Fuzzychain-edge proposes a fuzzy logic-based adaptive access control model for blockchain in edge computing [23]. While the paper title suggests adaptive trust mechanisms, the available metadata does not provide details on trustmodelformulation,decayparameters,orsimilaritytotheΓformulastructure.
    Synthesis for Probabilistic Trust: The literature demonstrates that trust can be dynamic (session-based certificates, reputation systems, continuous verification) but lacks probabilistic models with explicit decay parameters. Barrion et al.'s dynamic trust scoring for robotic swarms provides the closest architectural analog, but without mathematical formulation, it cannot inform αparametertuningforEARC.Theabsenceofdecay−basedtrustmodelsrepresentsacriticalgap,astheΓformula
    ′
    sαparameterdirectlydeterminessystembehaviorduringintermittentconnectivity—highαmaintainstrustduringbriefdisconnections(enablingoperationalcontinuity)whilelowαrapidlydegradestrust(improvingsecurityagainstprolongedattacks). The EARC thesis contributes the first quantified probabilistic trust model integrating cryptographic verification (No indicator)withtime−baseddecay(αfactor)forexpeditionarymanufacturingenvironments.
    4.5 ICS Safety Mechanisms: Kill Switches and Failure Modes
    Critical Finding: Minimal consideration of Industrial Control System (ICS) safety mechanisms in the surveyed literature, with no papers addressing how authentication failures should interact with kill switches or emergency stops in manufacturing contexts.
    Manica's work on interlocking IT/OT security for edge cloud-enabled manufacturing [28] is the only paper explicitly addressing manufacturing safety, but the available metadata does not provide details on kill switches, emergency stops, or fail-safe modes. The paper focuses on security architecture rather than safety-critical failure mode design.
    Nouma et al.'s trustworthy digital twins in post-quantum era with hybrid hardware-assisted signatures [26] addresses digital twin security but does not detail safety mechanisms like kill switches or system behavior upon authentication failure, network drops, or edge hardware malfunctions.
    Gap for ICS Safety: The literature does not address the critical safety question: Should authentication failure trigger an emergency stop (kill switch), or should the system continue operating with degraded trust? For EARC, involuntary kill switch activation when edge hardware is operational but network connectivity is lost would defeat the purpose of Edge-First architecture. However, continuing operation without authentication during a genuine attack could enable adversarial G-code injection causing dangerous CNC errors.
    4.5.2 Quality Management and Verification
    Schmid's robot delivery system includes verification of successful/failed delivery signals, representing a basic safety mechanism [6]. However, this is a binary outcome verification rather than continuous quality monitoring or fail-safe design.
    Gap for EARC: The EARC system requires G-code verification against original engineering design to prevent transmission corruption, real-time position feedback comparison against Digital Twin simulations (halting if drift exceeds threshold), and condition-based maintenance monitoring (motor current, vibration). None of these safety mechanisms are addressed in the surveyed literature's authentication frameworks.
    4.5.3 Failure Mode Design
    Critical Gap: No papers specify system behavior when authentication fails during active manufacturing operations. Should the system:
21. Immediately halt all operations (kill switch), risking involuntary stops during network disruption?
22. Continue current job with cached trust scores, risking operation under attack?
23. Enter a "safe mode" with restricted operations (e.g., complete current job but reject new jobs)?
    The EARC thesis must design failure modes that balance safety (preventing dangerous operations under attack) with operational continuity (avoiding involuntary stops during legitimate network disruption). The literature provides no guidance for this critical design decision.
    4.5.4 Condition-Based Maintenance Integration
    Gap for EARC: The EARC system integrates condition-based maintenance monitoring (motor current, vibration) with authentication to enable predictive maintenance alerts. No papers address how authentication frameworks should interact with condition monitoring—for example, should degraded trust scores trigger more frequent condition monitoring, or should
    Synthesis for ICS Safety: The literature exhibits a critical disconnect between authentication research and ICS safety engineering. While cryptographic frameworks ensure secure authentication, they do not address how authentication failures should interact with safety-critical manufacturing operations. The EARC thesis contributes safety-aware failure mode design that prevents involuntary kill switches during legitimate network disruption while maintaining fail-safe behavior during genuine attacks, integrating G-code verification, Digital Twin quality management, and condition-based maintenance with theΓtrustscoringframework.
24. Cross-Cutting Analysis: Integration Challenges
    5.1 MQTT/ROS2 Communication Stack Integration
    The EARC architecture replaces HTTP/REST with MQTT Broker (Mosquitto) for local message passing and ROS2 Action Server for deterministic control algorithms. Schmid's system demonstrates MQTT publish/subscribe over public channels for robot communication, achieving low latency (59-102ms for various phases) [6]. However, the paper does not integrate MQTT with cryptographic authentication—verification occurs separately from message transport.
    Integration Challenge: The literature does not address how ZKP or ECC authentication should be integrated with MQTT message flows. Should authentication occur at the MQTT broker level (authenticating connections), at the message level (signing individual messages), or at the application level (authenticating ROS2 action requests)? Each approach has different performance implications for MTTR and verification queuing (H3).
    5.2 Digital Twin Quality Management
    Nouma et al.'s trustworthy digital twins in post-quantum era focus on securing digital twin data integrity using hybrid hardware-assisted signatures [26]. Yigit et al.'s PRZK-Bind proposes physically rooted zero-knowledge authentication for secure digital twin binding in smart cities [24]. However, neither paper addresses real-time quality management where physical robot position is continuously compared against Digital Twin simulation to detect manufacturing defects.
    Integration Challenge: The EARC system must authenticate sensor data (weight verification, position feedback) used for Digital Twin comparison while maintaining real-time performance. If authentication latency causes position feedback delays, the Digital Twin comparison becomes stale, reducing quality management effectiveness. The literature does not address this real-time authentication challenge for closed-loop control systems.
    5.3 Gossip Protocol Mesh Synchronization
    Critical Gap: No papers analyze gossip protocol overhead in the context of cryptographic mesh authentication. The EARC system uses gossip protocol for logical clock synchronization, which introduces bandwidth overhead that may interact with verification queuing (H3) to cause MTTR degradation at higher node densities.
    Integration Challenge: Gossip protocols typically assume trusted nodes, but EARC requires authenticated gossip messages to prevent adversarial clock manipulation. The computational overhead of authenticating every gossip message may saturate Raspberry Pi 4 CPU resources, indirectly increasing MTTR through resource contention even if individual verification
25. Critical Gap Analysis for EARC Implementation
    This section synthesizes the hypothesis-specific findings into a comprehensive gap analysis directly actionable for EARC thesis validation.
    6.1 H1 Resilience Validation Gaps
    Gap 1.1 - MTTR Baseline Absence: No papers measure MTTR for centralized cloud-authentication systems under network disruption, preventing establishment of the baseline for 50% reduction claims.
    Gap 1.2 - DIL Environment Testing: No papers test authentication performance in environments with >20% packet loss or measure recovery time when transitioning from disconnected to connected states.
    Gap 1.3 - Edge-First Architecture Evaluation: While fog-cloud hybrid architectures are common, no papers evaluate pure Edge-First designs that maintain full operational autonomy during backhaul loss.
    EARC Contribution for H1: The thesis must establish centralized MTTR baselines through controlled experiments simulating cloud IdP dependency, then measure Edge-First MANET MTTR under identical 20% packet loss conditions to validate the 50% reduction claim.
    6.2 H2 Security Tax Validation Gaps
    Gap 2.1 - Cortex-M4 ZKP Performance: No papers test ZKP performance on Arduino Nano 33 BLE (Cortex-M4) platforms, critical for EARC sensor node authentication.
    Gap 2.2 - Proof Generation Overhead: Most papers report only verification time, not proof generation overhead. If EARC requires edge devices to generate proofs, the latency penalty may exceed the >15% threshold even if verification is fast.
    Gap 2.3 - System-Level MTTR Impact: Individual cryptographic operation latency does not account for system-level effects like memory contention on Raspberry Pi 4 running full MES stack, machine control, and cryptographic verification simultaneously.
    Gap 2.4 - Security Improvement Quantification: No papers quantify "System Trust Score" improvements during adversarial injection, preventing validation of whether ZKP's security gains justify the latency penalty.
    EARC Contribution for H2: The thesis must measure both verification and proof generation latency on actual EARC hardware (Raspberry Pi 4, Arduino Nano 33 BLE), conduct system-level MTTR measurements under realistic MES load, and define/measure System Trust Score under simulated adversarial conditions to validate the security-performance trade-off.
    6.3 H3 Scalability Validation Gaps
    Gap 3.1 - Node Density Scaling Data: Scalability testing rarely exceeds n=5 nodes, with no papers measuring authentication latency at n=10 node density.
    density threshold where queuing causes non-linear MTTR scaling.
    Gap 3.3 - Livelock Condition Detection: No papers test for livelock conditions where nodes spend more time verifying each other than performing productive work.
    Gap 3.4 - Gossip Protocol Interaction: No papers analyze how gossip protocol overhead for mesh synchronization interacts with cryptographic verification to affect scalability.
    EARC Contribution for H3: The thesis must systematically measure MTTR at n=3, n=5, n=7, and n=10 node densities, explicitly track verification queue depths, measure gossip protocol bandwidth consumption, and identify the node density threshold where MTTR exceeds the 500ms target due to verification queuing.
    6.4 Probabilistic Trust Model Gaps
    Gap4.1−DecayParameterQuantification:Nopapersprovidequantifiedtrustdecayparameters(α)orguidancefortuningdecay rates in expeditionary environments.
    Gap 4.2 - Cryptographic Integration: No papers integrate cryptographic verification indicators (No) with time-based trust decayinaunifiedformulalikeΓ(t+1)=α×Γ(t)+(1−α)×No.
    Gap 4.3 - Intermittent Connectivity Behavior: No papers analyze how trust models should behave during intermittent connectivity—shouldtrustpersistduringbriefdisconnections(highα)orrapidlydegrade(lowα)?
    EARC Contribution for Probabilistic Trust: The thesis contributes the first quantified probabilistic trust model integrating cryptographicverificationwithtime−baseddecay,withempiricalαparametertuningbasedonMTTRperformanceundervarying connectivity patterns.
    6.5 ICS Safety Mechanism Gaps
    Gap 5.1 - Authentication-Safety Integration: No papers address how authentication failures should interact with kill switches or emergency stops in manufacturing contexts.
    Gap 5.2 - Failure Mode Design: No papers specify system behavior when authentication fails during active manufacturing operations (immediate halt vs. continue with degraded trust vs. safe mode).
    Gap 5.3 - G-code Verification: No papers integrate cryptographic authentication with G-code verification to prevent dangerous CNC errors from adversarial injection.
    Gap 5.4 - Condition-Based Maintenance Integration: No papers address how authentication frameworks should interact with condition monitoring for predictive maintenance.
    EARC Contribution for ICS Safety: The thesis contributes safety-aware failure mode design preventing involuntary kill switches during legitimate network disruption while maintaining fail-safe behavior during genuine attacks, integrating G-codeverification,DigitalTwinqualitymanagement,andcondition−basedmaintenancewithΓtrustscoring.
    6.6 Integration Architecture Gaps
    with MQTT message flows and ROS2 action requests.
    Gap 6.2 - Real-Time Quality Management: No papers address authentication latency constraints for real-time Digital Twin position feedback comparison.
    Gap 6.3 - Authenticated Gossip Protocol: No papers analyze computational overhead of authenticating gossip protocol messages for mesh synchronization.
    EARC Contribution for Integration: The thesis demonstrates end-to-end integration of ZKP/ECC authentication with MQTT/ROS2 communication stack, real-time Digital Twin quality management, and authenticated gossip protocol mesh synchronization, measuring system-level MTTR impact.
26. Recommendations for Thesis Validation
    Based on the gap analysis, the following experimental validation approach is recommended for the EARC thesis:
    7.1 H1 Resilience Validation Experiments
    Experiment 1.1 - Centralized Baseline MTTR:
    Configure EARC system with centralized cloud IdP authentication (simulating Cloud-First architecture)
    Simulate network disruption (disconnect backhaul for 10-60 seconds)
    Measure MTTR: time from disruption to successful job completion after reconnection
    Repeat across 20%, 30%, 40% packet loss conditions
    Establish baseline MTTR distribution for 50% reduction target
    Experiment 1.2 - Edge-First MANET MTTR:
    ConfigureEARCsystemwithEdge−FirstMANETusingΓtrustscores
    Simulate identical network disruption scenarios
    Measure MTTR: time from disruption to successful job completion using local mesh authentication
    Compare against centralized baseline to validate 50% reduction claim
    Analyze which packet loss threshold causes Edge-First MTTR to exceed centralized baseline (crossover point)
    Experiment 1.3 - Recovery Time Decomposition:
    Decompose MTTR into components: detection time, authentication time, job resumption time
    Identify which component contributes most to MTTR reduction in Edge-First architecture
    ValidatethatΓtrustscorecachingenablesfasterauthenticationduringrecovery
    7.2 H2 Security Tax Validation Experiments
    Measure ZKP verification time on Raspberry Pi 4 under realistic MES load
    Measure ZKP proof generation time on Arduino Nano 33 BLE (if required)
    Measure ECC signing and verification time on identical hardware
    Calculate percentage latency penalty: (ZKP_time - ECC_time) / ECC_time × 100%
    Validate whether penalty exceeds 15% threshold
    Experiment 2.2 - System-Level MTTR Impact:
    Measure end-to-end MTTR with ZKP authentication under full system load (MES logic, machine control, sensor data collection, cryptographic verification)
    Measure end-to-end MTTR with ECC authentication under identical load
    Account for memory contention, CPU scheduling, and resource competition effects
    Validate whether system-level MTTR penalty exceeds 15% even if individual operation latency is lower
    Experiment 2.3 - Security Improvement Quantification:
    Define System Trust Score metric (e.g., attack detection rate, false positive rate, time to detect adversarial injection)
    Simulate adversarial scenarios (replay attacks, man-in-the-middle, malicious G-code injection)
    Measure System Trust Score for ZKP vs. ECC authentication
    Validate that ZKP provides statistically significant security improvement justifying latency penalty
    7.3 H3 Scalability Validation Experiments
    Experiment 3.1 - Node Density Scaling:
    Measure MTTR at n=3, n=5, n=7, n=10 node densities
    Plot MTTR vs. node density to identify scaling behavior (linear, polynomial, exponential)
    Identify node density threshold where MTTR exceeds 500ms target
    Compare ZKP vs. ECC scaling curves to validate non-linear scaling prediction
    Experiment 3.2 - Verification Queue Analysis:
    Instrument system to track verification queue depth at each node
    Measure queue depth vs. node density
    Identify queuing bottleneck threshold where queue depth grows unbounded (livelock condition)
    Analyze whether verification queuing is the dominant factor in MTTR scaling
    Measure gossip protocol bandwidth consumption vs. node density
    Measure CPU utilization for gossip message authentication
    Identify whether gossip overhead saturates MANET bandwidth or CPU resources before verification queuing causes livelock
    Validate interaction between gossip synchronization and verification queuing
    7.4 Probabilistic Trust Model Validation
    Experiment4.1−αParameterTuning:
    Testαvaluesfrom0.1to0.9in0.1increments
    Measure MTTR under intermittent connectivity patterns (brief disconnections vs. prolonged outages)
    Identifyoptimalαbalancingtrustpersistence(operationalcontinuity)vs.responsiveness(security)
    Validatethatintermediateαvaluesoutperformbothextremes(α→0:tooreactive,α→1:toopersistent)
    Experiment 4.2 - Trust Score Behavior Analysis:
    TrackΓtrustscoreevolutionduringnormaloperation,briefdisconnections,andprolongedoutages
    ValidatethatΓdecaysaccordingtoformuladuringdisconnection
    ValidatethatΓrecoversaccordingtoformulawhencryptographicverificationresumes
    Analyzetrustscorethresholdforoperationaldecisions(e.g.,Γ<0.3:rejectnewjobs,Γ<0.1:emergencystop)
    7.5 ICS Safety Mechanism Validation
    Experiment 5.1 - Failure Mode Testing:
    Simulate authentication failure during active CNC operation
    Test three failure modes: immediate halt (kill switch), continue with degraded trust, safe mode (complete current job, reject new jobs)
    Measure false positive rate (involuntary stops during legitimate network disruption) vs. false negative rate (continued operation during genuine attack)
    ValidatethatsafemodewithΓthresholdprovidesoptimalbalance
    Experiment 5.2 - G-code Verification Integration:
    Inject corrupted G-code with adversarial Z-axis depth changes
    Validate that cryptographic verification detects corruption before CNC execution
    Measure verification latency impact on job start time
    Experiment 5.3 - Digital Twin Quality Management:
    Simulate position drift exceeding threshold during manufacturing
    Validate that system halts operation and flags part as reject
    Measure latency from drift detection to emergency stop
    Validate that authentication latency does not delay safety-critical position feedback
27. Conclusion
    This hypothesis-driven literature review systematically evaluated 30 papers through the lens of the Expeditionary Automated Repair Cell (EARC) thesis, which proposes an Edge-First MANET framework using Zero-Knowledge Proofs and Probabilistic Trust Scores for forward-deployed Naval manufacturing units. The analysis reveals a critical disconnect between theoretical cryptographic advances and the specific requirements of resource-constrained expeditionary manufacturing operating in Disconnected, Intermittent, and Limited (DIL) network environments.
    For H1 (Resilience), the literature demonstrates that decentralized authentication on Raspberry Pi 4 hardware is technically feasible with millisecond-scale verification times, but no papers measure Mean Time to Recovery (MTTR) in DIL environments with >20% packet loss. The absence of MTTR benchmarks means the predicted 50% reduction cannot be validated by existing research, establishing a fundamental contribution of the EARC thesis.
    For H2 (Security Tax), preliminary evidence from Lin et al. and Schmid suggests ZKP verification on Raspberry Pi 4 incurs minimal latency penalty (<10ms, potentially <1% overhead) compared to ECC, contradicting the >15% prediction for verification operations [1], [6]. However, critical gaps remain: no ZKP performance data on Cortex-M4 sensor nodes (Arduino Nano 33 BLE), incomplete comparison of proof generation overhead, and absence of system-level MTTR measurements accounting for memory contention on Raspberry Pi 4 running full MES stack. The EARC thesis addresses these gaps through controlled experiments measuring both cryptographic operation latency and end-to-end MTTR under realistic system load.
    For H3 (Scalability), the literature demonstrates that blockchain-based authentication can scale to moderate node densities (n=5-10) without catastrophic failure, but provides no quantitative data on verification queuing delays or livelock conditions. Barrion et al.'s robotic swarm framework suggests dynamic trust scoring can maintain accuracy at scale, but the absence of latency metrics means the exponential scaling prediction remains untested [11]. The EARC thesis fills this gap by systematically measuring MTTR at n=3, n=5, n=7, and n=10 node densities, explicitly tracking verification queue depths.
    The most critical gap is the absence of probabilistic trust models with quantified decay parameters. No papers implement trustformulasanalogoustoΓ(t+1)=α×Γ(t)+(1−α)×No,withtrustremainingpredominantlybinary(authenticated/rejected)orreputation−basedwithoutexplicitdecayfunctions.Thisgapisfundamentalbecausetheαdecayparameter directly determines system behavior during intermittent connectivity—the defining characteristic of expeditionary environments. The EARC thesis contributes the first quantified probabilistic trust model integrating cryptographic verificationwithtime−baseddecay,withempiricalαparametertuningbasedonMTTRperformance.
    addressing how authentication failures should interact with kill switches or emergency stops in manufacturing contexts. The EARC thesis contributes safety-aware failure mode design preventing involuntary kill switches during legitimate network disruption while maintaining fail-safe behavior during genuine attacks, integrating G-code verification, Digital Twin quality management,andcondition−basedmaintenancewithΓtrustscoring.
    In summary, while the surveyed literature provides foundational cryptographic primitives (ZKP implementations on Raspberry Pi, ECC performance baselines, blockchain-based decentralized authentication), their integration into a cohesive Edge-First MANET framework for expeditionary manufacturing with quantified resilience (H1), security tax (H2), and scalability (H3) characteristics remains an open research challenge. The EARC thesis directly addresses this gap through hypothesis-driven experimental validation, contributing empirical performance data on resource-constrained hardware, probabilistic trust models with quantified decay parameters, scalability analysis at n=10 node density, and safety-aware failure mode design for contested industrial environments. These contributions establish the foundation for transitioning forward-deployed manufacturing from Cloud-First architectures with terminal dependencies to Edge-First MANET frameworks enabling operational continuity during network disruption.
    References
    [1] Lin, C., He, D., Huang, X., Choo, K.-K. R., & Vasilakos, A. V. (2023). An Access Control System Based on Blockchain with Zero-Knowledge Rollups in High-Traffic IoT Environments. Sensors, 23(7), 3443. https://doi.org/10.3390/s23073443
    [2] Pathak, S., Sharma, D. K., Mahajan, S., Gaba, G. S., Gurtov, A., & Masud, M. (2024). Blockchain-enhanced zero knowledge proof-based privacy-preserving mutual authentication for iot networks. IEEE Access. https://doi.org/10.1109/access.2024.3450313
    [3] Ramezan, G., Taghavi, M., & Leung, C. (2024). zk-IoT: Securing the Internet of Things with Zero-Knowledge Proofs on Blockchain Platforms. arXiv preprint arXiv:2402.08322. https://doi.org/10.48550/arxiv.2402.08322
    [4] Hewa, T., Gür, G., Kalla, A., Ylianttila, M., Bracken, A., & Liyanage, M. (2022). Fog Computing and Blockchain-Based Security Service Architecture for 5G Industrial IoT-Enabled Cloud Manufacturing. IEEE Transactions on Industrial Informatics. https://doi.org/10.1109/tii.2022.3140792
    [5] Turnip, M., Situmorang, Z., Turnip, A., Suherman, S., & Saragih, I. S. (2025). Towards 6G Authentication and Key Agreement Protocol: A Survey on Hybrid Post Quantum Cryptography. IEEE Communications Surveys & Tutorials. https://doi.org/10.1109/comst.2025.3567439
    [6] Schmid, S. (2022). Customer Empowered Privacy-Preserving Secure Verification using Decentralized Identifier and Verifiable Credentials For Product Delivery Using Robots. arXiv preprint arXiv:2208.06165. https://doi.org/10.48550/arxiv.2208.06165
    [7] Puggioni, F., Homoliak, I., Percia David, S., & Binder, A. (2020). Towards Decentralized IoT Updates Delivery Leveraging Blockchain and Zero-Knowledge Proofs. Proceedings of the IEEE Conference.
    [8] Huang, Y., Chen, X., & Wang, L. (2025). A novel zero-trust identity framework for agentic ai: Decentralized
    [9] Geng, X., Chen, Y., Pan, Y., & Zhang, M. (2025). Blockchain-based identity authentication and data interaction scheme for Industrial Internet of Things. Computers & Electrical Engineering, 110143. https://doi.org/10.1016/j.compeleceng.2025.110143
    [10] Baza, M., Nabil, M., Lasla, N., Fidan, K., Mahmoud, M., & Abdallah, M. (2018). Blockchain-based Firmware Update Scheme Tailored for Autonomous Vehicles. Proceedings of the IEEE Conference.
    [11] Barrion, A. A., Castañeda, J. A., & Dela Cruz, J. C. (2024). Advancing Robotic Swarms with Blockchain Technology: A Dynamic Two-Factor Authentication Consensus Framework. Research Square preprint. https://doi.org/10.21203/rs.3.rs-5301694/v1
    [12] Vadluri, S., Vankayala, V. K., & Kothapalli, K. (2025). Zero-Trust Architecture and Blockchain-Based Security Models for IoT-Integrated Industrial Power Electronics Systems. In Advances in Power Electronics and Electric Drives (pp. 13). https://doi.org/10.71443/9789349552111-13
    [13] Cui, J., Wu, D., Zhang, J., Xu, Y., & Zhong, H. (2023). Efficient and Anonymous Cross-Domain Authentication for IIoT Based on Blockchain. IEEE Transactions on Network Science and Engineering. https://doi.org/10.1109/TNSE.2022.3224453
    [14] Burgos, A., Martín, C., Martínez, J. F., & Rubio, B. (2024). Decentralized IoT Data Authentication with Signature Aggregation. Sensors, 24(3), 1037. https://doi.org/10.3390/s24031037
    [15] Zhai, X., Wang, Y., Zhang, Y., & Li, J. (2025). A lightweight authentication method for Industrial Internet of Things based on blockchain and Chebyshev chaotic maps. Future Internet, 17(8), 338. https://doi.org/10.3390/fi17080338
    [16] Nawaz, S. J., Sharma, S. K., Wyne, S., Patwary, M. N., & Asaduzzaman, M. (2025). Trustworthy autonomy in 6g robotics: Advances and perspectives on edge intelligence and federated self-certification. TechRxiv preprint. https://doi.org/10.36227/techrxiv.174318141.12755600/v1
    [17] Park, Y. (2023). Decentralized Authentication and Data Access Control Scheme Using DID for Fog-Enabled Industrial Internet of Things. Journal of Information Security and Applications.
    [18] Fotiou, N., Siris, V. A., & Polyzos, G. C. (2022). Authentication, Authorization, and Selective Disclosure for IoT data sharing using Verifiable Credentials and Zero-Knowledge Proofs. Proceedings of the IEEE International Conference on Blockchain and Cryptocurrency.
    [19] Poghosyan, A., Harutyunyan, A., Grigoryan, N., & Hovhannisyan, V. (2024). Decentralized Privacy Provision in Dynamically Reconfigurable and Self-Organizing Aero-Physical Cyber Systems. Proceedings of the International Conference on Cyber-Physical Systems.
    [20] Yang, X., Li, W., Zhang, S., & Liu, Y. (2024). SAKMS: A secure authentication and key management scheme for IETF 6TiSCH industrial wireless networks based on improved elliptic-curve cryptography. IEEE Transactions on Network Science and Engineering. https://doi.org/10.1109/tnse.2024.3363004
    the IEEE Conference on Network Softwarization.
    [22] Lv, Z., Qiao, L., Li, J., & Song, H. (2020). Decentralized Blockchain for Privacy-Preserving Large-Scale Contact Tracing. IEEE Internet of Things Journal.
    [23] Farooq, M. S., Sohail, M., Abid, A., & Rasheed, S. (2026). Fuzzychain-edge: A novel Fuzzy logic-based adaptive Access control model for Blockchain in Edge Computing. Journal of Network and Computer Applications.
    [24] Yigit, Y., Challenger, M., & Kardas, G. (2025). PRZK-Bind: A Physically Rooted Zero-Knowledge Authentication Protocol for Secure Digital Twin Binding in Smart Cities. arXiv preprint arXiv:2508.17913. https://doi.org/10.48550/arxiv.2508.17913
    [25] Chatzigiannakis, I., Pyrgelis, A., Spirakis, P. G., & Stamatiou, Y. C. (2011). Elliptic Curve Based Zero Knowledge Proofs and Their Applicability on Resource Constrained Devices. Proceedings of the IEEE Conference.
    [26] Nouma, D., Tonyali, S., Cakmak, B., Akkaya, K., & Uluagac, A. S. (2023). Trustworthy and Efficient Digital Twins in Post-Quantum Era with Hybrid Hardware-Assisted Signatures. ACM Transactions on Multimedia Computing, Communications, and Applications. https://doi.org/10.1145/3638250
    [27] Yu, S., Liu, Y., Wang, Y., & Xie, H. (2024). Anonymous Batch Message Authentication Aided by Edge Servers in Industrial Internet of Things. Proceedings of the IEEE AIIoT Conference. https://doi.org/10.1109/aiiot61789.2024.10578981
    [28] Manica, L. (2023). Interlocking IT/OT security for edge cloud-enabled manufacturing. SSRN Electronic Journal. https://doi.org/10.2139/ssrn.4481855
    [29] Gong, Y. (Year not available). Design of lightweight secure communication protocol for IoT edge computing node. Journal/Conference not specified.
    [30] Zeng, P., Xu, G., Wang, X., Xu, K., & Choo, K.-K. R. (2024). Efficient Revocable Cross-Domain Anonymous Authentication Scheme for IIoT. IEEE Transactions on Information Forensics and Security. https://doi.org/10.1109/tifs.2024.3523198

