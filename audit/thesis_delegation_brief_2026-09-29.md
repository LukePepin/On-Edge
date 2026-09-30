# Cryptographic Delegation for a Robotic Workcell in DIL Environments

Working research brief — September 29, 2026, revised after Luke's decisions. Luke approves the original-proposal/continuation scope mapping below. Dr. Sodhi has not yet approved this revision. This is a planning document, not an implementation specification or a claim of new results.

## Problem and candidate question

A robotic workcell can lose access to a central authorization service while its local equipment remains usable. Pre-issued permissions may cover some work, but a new job or operator assignment may require a fresh local authorization decision. The study would examine how a cell can make that decision within authority granted before disconnection.

**Candidate research question:** How do central authorization, pre-issued offline permissions, and constrained local delegation affect the continuity and correct execution of robot jobs under DIL connectivity?

The central outcome is correct authorization and physical job execution under disruption. Increased throughput is not assumed, and observed rejection tests do not establish a universal security guarantee. Cryptography is an implemented security mechanism; a standalone comparison of signature algorithms is removed at Luke's request.

## Proposed system

Use one robot. Delegation depth is not a fixed scope boundary; the number of permitted hops and the evidence needed to justify them remain open for advisor discussion. The initial example has a central authority sign a grant identifying a local issuer and its permitted robot operations, parameter limits, and validity period. That issuer signs narrower job permits during an outage. Any additional hop would need to preserve the same scope and deadline constraints. A robot-side verifier checks the grant chain, job permit, requester binding, and replay protection before admitting a specific approved routine.

A child permit cannot expand the parent's rights or extend its deadline for admitting new jobs. Permissions must bind the actual routine and parameters executed. Luke prefers admission-based expiry: a job admitted and started while authorized may finish, while expiry blocks the next job. The parent policy must explicitly authorize that bounded completion allowance; it is not an implicit extension of expired authority. A separate maximum job duration/completion deadline is recommended, with the exact value and fault response still to be designed. Queued jobs must be checked at dispatch, and an active job cannot be extended by appending more work. Long outages eventually exhaust authority to start new jobs. Central revocation cannot be learned instantaneously during isolation.

Luke accepts Pi-side verification and prefers retaining the Nano and safeguard interface. Recommended division: the Pi verifies grants/permits, binds them to a job, checks admission deadlines, and prevents replay; the Nano supervises a bounded local execution allowance and drives the safeguard output. The Nano is not an independent cryptographic verifier, does not inspect the physical task, and relies on the trusted Pi for admission and completion information. Its exact protocol, timeout, and restart behavior remain open. Headquarters disconnection must be distinguished from loss of local Pi/Nano supervision. Remove the EWMA trust-score decision. Invalid unrelated requests must not interrupt a separately authorized job; restored connectivity alone must not restart paused motion. Existing wiring is not a safety-rated authorization system.

Luke reports an attached, connected gripper with demonstrated physical pick-and-place capability. The current experiment only implements arm trajectories: `v8/onedge_v8/motion.py` uses Pick/Transfer/Place pose names but does not actuate the gripper. A complete grasp/transfer/release routine is new work. Luke has selected job approvals and accepts one object transfer as one job. The existing Towers of Hanoi apparatus is the proposed physical testbed: calibrated peg poses and disk dimensions can be stored in arrays, with a separate stack-state model and checked physical completion. A fixed Hanoi solution can be fully preauthorized, so it does not by itself demonstrate a delegation advantage.

## Comparisons and evidence

- **Authorization architectures:** central approval of new requests; pre-issued offline permissions; constrained local delegation. Hold the root policy, maximum validity, request trace, and robot routines constant where applicable. Include known-in-advance and newly arriving requests. Report differences in who is trusted to issue permissions; equal root limits do not make the trust architectures identical. A capable cached-permission baseline may match delegation.
- **Cryptography:** select one established signature scheme/library after a bounded feasibility check. Implement signed delegation and task permits with requester binding, scope restriction, integrity, freshness, and replay protection. Resource and timing measurements support system feasibility rather than a separate algorithm hypothesis. Do not invent a new primitive.
- **DIL:** controlled backhaul disconnection, intermittent availability, and limited/delayed communication, plus a connected control. Measure the achieved conditions. Treat any degradation of the local permit-delivery link separately; do not infer RF-jamming behavior from network emulation.
- **Robot evidence:** authorized jobs admitted and physically completed; invalid, over-scoped, expired-at-admission, or replayed requests rejected; an active job completes across backhaul loss or admission expiry; subsequent jobs remain blocked after authority expires. Test reconnection/retry behavior without duplicate physical execution, and selected local-supervision faults separately. Preserve distinct device output commands, controller reports, and fresh motion telemetry. Apply the same completion policy to architecture comparisons to avoid confounding delegation with stop policy.

## Continuity and scope

Luke-approved continuity mapping: retain the proposal's DIL motivation, local authority, central/local comparison, real cryptographic processing, and physical robot enforcement. Replace the assumed packet-loss crossover with a conditional comparison; replace proxy workloads with real verification. Remove the ZKP/selective-disclosure, multi-node mesh, Byzantine detection, and queue-saturation hypotheses. Cryptographic overhead can be supporting characterization, with no standalone algorithm-comparison study. This remains a substantive amendment for advisor discussion. Prior timing work supports instrumentation and enforcement measurement, not validation of the new authorization protocol. Novelty still requires a focused literature review.

December graduation is fixed. Plan around 20 hours/week and approximately three physical lab hours/week. Develop and test credentials, policies, and network conditions at home; use lab sessions for robot integration and selected physical validation. Establish a complete bench authorization path before expanding the experiment matrix.

## Decisions needed

1. Exact gripper control interface, objects, approved locations, and job-completion evidence.
2. The local job-approval rule and root grant limits for disk transfers; job approvals have been selected by Luke, and operator-permission delegation is outside the core.
3. Explicit completion allowance and Nano supervision protocol, including interrupted-job reconciliation. Pi verification/Nano retention and admission-only expiry are Luke's preferences.
4. Advisor acceptance of the revised contribution and minimum evidence.

Technical starting points: [ACE-OAuth local token validation](https://www.rfc-editor.org/rfc/rfc9200.html#appendix-F.1), [COSE signed structures](https://www.rfc-editor.org/rfc/rfc9052.html#section-4.2), and [COSE signature algorithms](https://www.rfc-editor.org/rfc/rfc9053.html#section-2). These establish available building blocks, not the novelty or correctness of the proposed system.

See [proposed architecture, test matrix, and concise research notes](thesis_delegation_test_plan_2026-09-29.md). Numerical test levels and repetitions are pilot proposals, not an approved final campaign.
