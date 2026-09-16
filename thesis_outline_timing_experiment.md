# Thesis outline: timing experiment

Updated September 16, 2026. Working outline for Luke's own writing. The timing experiment is the agreed organizing argument; detailed claims and evidence remain subject to review. This outline is mirrored in the Thesis writing folder; keep both copies aligned when revising the agreed structure.

This is an AI-assisted planning document, not thesis prose to submit.

## 1. Direction and constraints

- **First readable draft:** September 23, 2026. User-selected target for getting a draft to Sodhi.
- **Dashboard/demo:** September 30, 2026, including a detailed execution guide.
- **Available active work through September 30:** at most 44 hours, including writing, planning, learning, development, lab work, validation, documentation, and contingency. The approved revision allocates 39 planned hours plus 5 reserve; see the delivery notes below.
- **October–November:** prioritize writing, advisor feedback, and revisions. Luke has allocated approximately 20 hours/week: 16 planned plus 4 reserve, including the initial 10-hour V8 validation study.
- **Proposed defense:** December 10, 2026; unconfirmed. Scheduling remains subject to confirmation. Advisor acceptance of the narrowed contribution and review turnaround remain unresolved. Luke has deferred scope outreach; do not treat our planning agreement as advisor approval.
- **Authorship:** Luke writes the thesis. AI assistance supports outlining, critique, explanation, and editing of Luke's writing.

### Working research question

- How do computational workload duration, EWMA weight, and injected failure duration affect the response of a microcontroller trust monitor connected to a robot safeguard input?

### Candidate contribution

- An experimental characterization of a specific prototype's response timing and failure-duration behavior.
- An explanation connecting workload duration, trust updates, and the observed response, with explicit assumptions and measurement limitations.
- A reproducible demonstration of the implemented signal path.
- **Contribution gap:** explain what this characterization adds to prior work. The EWMA recurrence alone is not a novelty claim; a working demonstration alone does not establish research novelty.

### Argument to develop

1. Computational work and trust updates share the implemented loop.
2. EWMA settings determine how many consecutive bad observations are required to cross the threshold from a specified initial score.
3. Loop duration and command timing therefore matter to the response.
4. Existing experiments provide evidence about that response, with important instrumentation limitations.
5. Conclusions must distinguish a logged trust decision, a changed output signal, and physical robot standstill.

## 2. Chapter outline

### Chapter 1 — Problem, question, and scope

**Purpose:** establish one problem that the experiments actually address.

**Essential points**

- Brief application motivation: delayed withdrawal of robot run permission when a fault condition is reported.
- Cloud dependence as context, only to the extent needed to motivate the prototype.
- Research question and experimental factors: workload, EWMA weight, injected failure duration.
- Measured outcomes and the boundaries of the investigation.
- Candidate contribution and a short guide to the remaining chapters.

**Evidence and gaps**

- Ground the system description in the actual firmware and host scripts.
- State that robot-campaign failure injection uses serial commands; it is not a measured network outage at the Arduino.
- Do not describe the prototype as a complete cryptographic authorization system.
- Confirm the contribution's positioning through related work and advisor review.

**Keep out**

- Extended coalition/privacy scenarios, mesh architectures, and promises of capabilities that were never implemented.
- A chronological account of project pivots.

### Chapter 2 — Necessary background and related work

**Purpose:** give readers only the concepts needed to understand the method and assess the contribution.

**Essential points**

- EWMA update rule, initial score, threshold, and interpretation of alpha.
- Difference between computational workload time and full loop period.
- Difference between failure detection, trust-threshold crossing, output actuation, and robot standstill.
- Brief description of the two implemented workloads: key generation and two scalar multiplications.
- Relevant prior work on monitoring response, computation/control timing, and robot interlocks.

**Evidence and gaps**

- Select primary sources that serve a specific later argument; verify every retained citation.
- Check stop terminology against documentation for the actual robot/controller.
- Identify a concrete comparison with prior work. Do not claim novelty merely because the hardware combination differs.

**Keep out**

- General cryptography tutorials, extensive ZKP taxonomy, ROS 2 tutorials, and queueing theory that the analysis does not use.
- Claims that a particular stop-time budget is required by a standard without a verified source.

### Chapter 3 — System and experimental method

**Purpose:** explain exactly what ran, what varied, and how each reported outcome was obtained.

**Suggested subsections**

1. **Implemented architecture:** host/Pi, Arduino, output interface, UR5; one diagram with real messages and connections.
2. **Monitor behavior:** configuration, workload execution, trust update, threshold crossing, recovery, and reset.
3. **Experimental design:** V6/V7 conditions, repetitions, within-campaign ordering, and the separate bench measurements.
4. **Measurement and inclusion rules:** event definitions, clocks, logging, trial validity, exclusions, missing data, and analysis procedure.
5. **Proposed V8 validation:** corrected message capture, device event timestamps/cycle IDs, fresh motion feedback, and a physical-stop pilot. Label procedures proposed until executed and validated.

**Essential points**

- Define the two workloads once and use consistent short labels thereafter. Explain that neither checks received credentials in these campaigns.
- State the implemented recurrence: `trust_next = alpha * observation + (1 - alpha) * trust_previous`.
- Distinguish `observation = 0` under injected attack from the accumulated trust score; the score does not instantly become zero.
- Specify the initial score and strict firmware threshold comparison.
- Explain when serial commands are processed relative to workload execution.
- Separate score recovery from output re-enablement; `RECOVER` and reconfiguration are different operations.
- Define the start and end events for each latency. Logged threshold crossing is not a direct measurement of electrical actuation or standstill.
- State that ECC and proxy conditions were collected in separate robot campaigns, with different outage sets and repetition counts.

**Evidence and gaps**

- Firmware, logger, campaign scripts, raw CSVs, and saved audit outputs are available.
- The serial reader discards data; describe the effect on observed crossing times and counts.
- The logger substitutes zero velocity when joint feedback becomes stale. Those zeros cannot independently establish physical standstill.
- The audit's physical-stop classifier uses those velocity columns. Its classifications need qualification or independent corroboration.
- Document source versions and historical execution provenance without claiming that repository history alone proves the exact flashed binary.

**Keep out**

- Line-by-line code explanations and exhaustive V1–V5 history. Put necessary implementation details and history in appendices.

### Chapter 4 — Results

**Purpose:** present observations in the order needed to answer the research question.

**Suggested subsections**

1. **Workload and loop timing:** separate primitive profiling from host-observed loop intervals.
2. **Trust response:** V6/V7 logged response times and whether threshold crossing was recorded across the tested conditions.
3. **Bench timing:** supporting observations about command-to-response structure, clearly separated from robot results.
4. **Robot observations and uncertainty:** what motion records support, what they do not, and which classifications remain unresolved.
5. **V8 results, pending:** preserve an explicit gap until new timing/physical measurements exist; never combine them with V6/V7 as though their instrumentation were identical.

**Essential points**

- Prefer a small set of useful tables and figures over one subsection per historical claim.
- Report sample counts, units, event definitions, missing observations, and relevant spread.
- Include legitimate non-eviction trials; absence of a stop is not automatically an invalid experiment.
- Keep recorded threshold crossings separate from inferred physical outcomes.
- Show differences between conditions without presenting the between-campaign comparison as a fully controlled algorithm experiment.
- Distinguish observed maxima from guaranteed bounds.

**Evidence and gaps**

- Saved audit tables contain 120 V6 and 75 V7 records; the separate bench table contains 20 records. The September 13 read-only recheck covered all 195 retained robot CSVs and reproduced saved threshold latencies within 0.001 ms. This confirms subtraction of recorded timestamps, not hardware-event accuracy. No new experiment was run.
- Reconcile any retained numerical result with its raw data and analysis definition before final submission.
- Do not claim all physical-stop classifications are independently verified.
- Existing records do not establish a sub-500 ms stop of a moving robot.

**Keep out**

- Withdrawn numerical claims, unrelated profiling results, and a result framed as confirmation of an arithmetic identity.

### Chapter 5 — Interpretation, model, and limitations

**Purpose:** explain what the results mean without extending them beyond the evidence.

**Suggested subsections**

1. **Trust-update behavior:** derive the number of bad observations needed to cross the threshold from the stated initial score.
2. **Response-time structure:** relate that count to workload/loop timing, command processing, and observation delay.
3. **Agreement and discrepancies:** compare predictions with observations and identify unresolved differences.
4. **Implications and limitations:** responsiveness, tolerance of brief failures, implementation dependence, and measurement limits.

**Essential points**

- Explain the mathematical relation in Luke's own words, with a small worked example.
- Define threshold-crossing cycle count as the first integer satisfying the actual strict inequality; check any closed-form expression at equality boundaries.
- Treat a uniformly distributed arrival phase as an assumption unless established experimentally.
- Explain finite-duration failures in terms of the bad observations actually processed. Do not promote the tested grid into a universal phase-independent threshold law.
- Do not use an assumed logger correction as though it were a new measurement.
- If retaining a timing-budget illustration, state its origin and endpoint; include all relevant stages before calling it a total response budget.
- Keep unmeasured detection, electrical, controller, and mechanical delays explicit.
- Discuss the supervisor dependence: successful workload execution does not authenticate the supervisor or establish that its reports are truthful.

**Evidence and gaps**

- Existing model-comparison scripts are useful starting material, not proof that every assumption or residual explanation is correct.
- Correct the summary's budget arithmetic before reuse.
- Literature positioning, model accuracy, and physical-stop evidence remain the main substantive gaps.

**Keep out**

- A new hypothetical hold-down attack chapter, watchdog implementation, universal ZKP performance conclusions, or claims of safety certification.

### Chapter 6 — Conclusion and bounded future work

**Purpose:** answer the research question with no new claims or results.

**Essential points**

- What the experiments establish about this implementation's timing.
- What the study contributes beyond the EWMA algebra.
- The principal limits on interpretation and generalization.
- Only the few follow-ups that arise from final evidence gaps. Improved event capture and physical-stop validation are now planned thesis work; do not automatically defer them to future work. Actual verification belongs to a later research objective unless explicitly justified and approved.

**Evidence and gaps**

- Every conclusion must point back to a result and its stated limitations.
- Do not make the conclusion depend on completing a future system.

## 3. Cut and consolidation decisions

| Material | Recommended treatment | Reason |
| --- | --- | --- |
| Actual architecture, EWMA, V6/V7, supporting bench timing | Keep as the core | Directly addresses the agreed research question |
| Workload profiling | Combine with the timing evidence | Supports the same argument |
| Cloud-loss motivation | Reduce to brief context | Broader than what the robot experiments demonstrate |
| ZKP explanations | Limit to accurate identification of the historical workload | No proof verification was performed in these campaigns |
| Real ZKP or broader authorization implementation | Defer; not a draft prerequisite | Adds implementation and new-evidence requirements |
| Cloud failover/rejoin sweep | Exclude from the central contribution by default | Separate setup and question; partly compromised evidence |
| Hold-down adversary and watchdog proposal | Remove from main argument | Introduces an unbuilt mechanism and another research direction |
| Queueing/QoS, x86 comparison, ns-3, ML, mesh | Remove or defer | Not necessary to explain the timing experiment |
| V1–V5 development history | Appendix only where needed | Explains provenance without dominating the thesis |
| Withdrawn/unsupported results | Omit from thesis claims; preserve audit history separately | Repeatedly defending abandoned claims adds noise |
| Demo dashboard and execution guide | Supporting artifact; short mention in thesis | Handover deliverable, not automatically another research contribution |

### Rule for each paragraph, figure, and citation

- Does it help the reader understand the question, reproduce the method, assess the evidence, or interpret the answer?
- If not, cut it or move it outside the main argument.
- Define necessary caveats once in Methods and carry them through labels and interpretation. Repeat only where omission would mislead.
- Use explicit gap markers in the working draft instead of filling gaps with confident prose.

## 4. September 23 readable-draft target

### Suggested writing order

1. Methods: what ran and what was measured.
2. Results: what the records show, with uncertainty attached.
3. Interpretation: what follows and what remains assumed.
4. Introduction and conclusion: match them to the actual investigation.
5. Background: add only what those sections require.

### Readable-draft acceptance criteria

- All six sections form one argument in Luke's own words.
- The research question matches the implemented experiment and reported outcomes.
- One accurate architecture diagram and a limited set of essential results tables/figures.
- Technical terms are defined when needed; unnecessary background is removed.
- Every retained number has an identifiable source and measurement definition.
- Unresolved claims, missing citations, and evidence checks are visibly marked.
- No placeholder is disguised as a completed result.
- No dependence on finishing ZKP, a broader system, or a full v8 campaign first.
- Keep contribution/scope/evidence questions recorded for later advisor review. Luke has deferred initiating that scope discussion; no outreach is implied.

This target is a readable draft for feedback, not a claim that final thesis validation or submission requirements have been completed. The approved demo/V8 plan is recorded in live Todoist. September allocation: planning/learning 3h, readable draft 16h, logging/bench 4h, dashboard/script 4h, guide/walkthrough/package 4h, original URI integration/meetings/capture 4h, administration 1h, physical pilot 3h target = 39h, plus 5h reserve. The pilot may use up to 2 more reserve hours. Do not double-count parent/subtask estimates. October validation initially uses 2h design, 4h acquisition, and 4h analysis within weekly capacity. Exact V8 factor levels, repetitions, clock alignment and physical criteria are not yet settled.

## 5. Source map

Treat these as evidence to assess, not automatically correct authorities. Later explicit user decisions take precedence over older plans.

| Source | Use | Caution |
| --- | --- | --- |
| [Current writing evidence corrections](https://github.com/LukePepin/On-Edge/blob/main/audit/writing_evidence_status_2026-09-16.md) | Event definitions and qualifications to older summaries | A review addendum, not new experimental data |
| [Historical ground-truth review](https://github.com/LukePepin/On-Edge/blob/main/ground_truth_v2.md) | Campaign and claim inventory | Contains interpretations requiring correction or qualification |
| [Original project summary](https://github.com/LukePepin/On-Edge/blob/main/docs/project_summary_review.md) | Architecture explanation and background inventory | Not thesis prose to adopt; contains technical and reasoning errors |
| [Imported task snapshot](https://github.com/LukePepin/On-Edge/blob/main/todoist.md) | Historical planning context | Superseded in places by live Todoist and current decisions |
| [Trust-monitor firmware](https://github.com/LukePepin/On-Edge/blob/main/firmware/unified_trust_monitor_template/unified_trust_monitor_template.ino) | Workloads, trust update, output behavior | Function names can imply verification that the code does not perform |
| [Joint logger](https://github.com/LukePepin/On-Edge/blob/main/src/sentry_logic/sentry_logic/joint_logger_node.py) | Event recording and instrumentation limits | Serial data loss and synthetic zero velocities |
| [Physical-stop audit](https://github.com/LukePepin/On-Edge/blob/main/audit/physical_stop_crosstab.py) | Understand the existing classification | Does not independently distinguish stale feedback from standstill |
| [Model-comparison script](https://github.com/LukePepin/On-Edge/blob/main/audit/closed_form_check.py) | Inspect existing timing comparison | Assumed phase distribution and explanatory claims need review |
| [V6 audit table](https://github.com/LukePepin/On-Edge/blob/main/audit/eviction_v6.csv) and [V7 audit table](https://github.com/LukePepin/On-Edge/blob/main/audit/eviction_v7.csv) | Saved trial-level analysis | Reconcile retained results with raw logs and method |
| [Bench timing records](https://github.com/LukePepin/On-Edge/blob/main/data/v7_logs/e2e_composition_results.csv) | Separate bench observations | No robot; do not reuse withdrawn prediction/residual columns |

Source baseline inspected at commit `fb03972343020bffb91fcf6f73b60a33d24767d4`. Live Todoist received approved plan updates on September 13; this writing handoff does not change tasks. Source links resolve on GitHub after publication; local evidence is in On-Edge. Older original handoff files remain under Research/Design/9-12 and are historical, not required to start writing.
