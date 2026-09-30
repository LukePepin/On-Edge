# Study guide: cryptographic delegation for a robot working through disconnection

**Luke Pepin — working thesis direction, September 29, 2026**

This is an assistant-written learning aid and notebook, not thesis manuscript prose. Luke has selected this direction for discussion; Dr. Sodhi has not yet approved the revised scope. Examples below explain the proposed design and are not experimental results. Numerical deadlines are illustrative unless explicitly identified as a project deadline.

## 1. The problem in one concrete scene

Imagine a robot workcell that normally receives job approvals from headquarters, abbreviated **HQ**. The robot, gripper, local computer, and operator are all working. The connection to HQ fails.

An operator now requests another job. The physical equipment can do it, but who can authorize it? Three possible answers lead to three architectures:

1. Wait for HQ to approve the new request.
2. Use a permission that HQ issued before the outage, if that permission covers the request.
3. Let a local authority approve a new job within limits that HQ previously delegated.

The thesis will investigate the third architecture against the first two. The goal is useful operation during communication disruption while preserving explicit limits on what the cell can approve and execute.

**Working research question:** How do central authorization, pre-issued offline permissions, and constrained local delegation affect the continuity and correct execution of robot jobs under DIL connectivity?

The question does not assume delegation always completes more work. Its value may depend on the requests, prior permissions, outage duration, and acceptable local authority.

**Explain it yourself:** Why can a physically functional robot still be unable to start its next job?

**My notes:**

- 
- 

## 2. The vocabulary: identity, permission, and delegation

**Authentication** establishes the identity or key associated with a request. **Authorization** decides whether that requester may perform the particular action. Knowing who signed a message does not establish that the action is allowed.

A **digital signature** lets a verifier check that a message was signed using the private key corresponding to a trusted public key and was not altered afterward. The private key must remain protected. A stolen issuer key can produce signatures that pass verification.

Signatures do not encrypt the request, establish physical safety, prevent a valid message from being replayed, or explain whether the robot actually picked up an object. Those properties need other mechanisms or evidence.

A **delegation grant** is HQ's signed statement that a specified local issuer may approve a restricted class of jobs. A **job permit** is that issuer's signed approval for one particular transfer. The Pi checks both documents and their relationship.

The simple example below uses one delegation step: HQ delegates to a local issuer, which issues job permits. Luke has since clarified that one delegation step is not a fixed boundary for the thesis. The permitted chain depth and how to justify it remain design decisions; one robot remains the physical boundary.

### A worked example

Suppose HQ issues this illustrative grant:

> Issuer L may approve robot R to transfer disks D1 and D2 among pegs A, B, and C. New jobs may start before 10:30. Each admitted transfer has at most 30 seconds to complete. This particular grant does not permit a further delegation hop.

At 10:12, after HQ becomes unreachable, L signs this job permit:

> Job J17: requester O may use robot R to move D1 from A to B using the approved disk-transfer routine. Expected task state is version 7. Start before 10:20 and complete within the grant's allowed runtime.

The Pi verifies the HQ signature, the issuer's signature, the issuer's identity, and every applicable restriction. Moving D3 would be outside this grant even if L signed the request correctly. Extending the start deadline beyond 10:30 would also be invalid.

The exact message format and signature library remain implementation choices. COSE defines established signed-message structures, including a single-signature structure; it is a candidate building block, not a complete delegation policy for this robot. [RFC 9052, section 4.2](https://www.rfc-editor.org/rfc/rfc9052.html#section-4.2)

**Check your understanding:** Can a request have a valid signature and still be unauthorized? Give two examples.

**My notes:**

- 
- 

## 3. What is decentralized in this system?

HQ still determines the outer limits. The local issuer receives discretion to make individual job-approval decisions within those limits while HQ is unreachable. That local decision authority is the decentralized part.

The cell does not invent new authority when the network fails. It exercises authority delegated beforehand. HQ can choose a narrow grant, a broad grant, a short validity period, or a longer one. Those choices create a useful tradeoff: more offline flexibility also gives the local issuer more opportunity to exercise authority before HQ can intervene.

### The three architectures we will compare

| Architecture | Who approves a newly requested job? | What can happen during an outage? |
|---|---|---|
| Central approval | HQ | Requests needing new HQ approval wait or fail; already admitted work follows the common completion policy. |
| Pre-issued offline permission | HQ approved the relevant permission earlier; the Pi checks it locally | Work continues when the permission already covers the request. |
| Constrained local delegation | A local issuer operating under HQ's grant | The issuer can approve new jobs within that grant without contacting HQ. |

Offline permission checking already exists in established authorization frameworks. ACE-OAuth explicitly describes local token validation, so this thesis should not claim that all OAuth-based systems require a live central check for every operation. [RFC 9200, appendix F.1](https://www.rfc-editor.org/rfc/rfc9200.html#appendix-F.1)

The pre-issued baseline must be credible. A broad reusable permission could already cover all Hanoi moves and perform as well as delegation. A fixed Hanoi solution can also be approved in advance. Our comparison must include the actual permissions and who is trusted to make decisions, not just throughput numbers.

**The research opportunity:** characterize when local job-approval discretion is useful, how its limits are enforced, and what happens at physical execution boundaries.

**My notes — a realistic reason the operator might request a different job:**

- 
- 

## 4. The responsibilities of each component

| Component | Proposed responsibility | Boundary to remember |
|---|---|---|
| HQ | Sign delegation grants and renew or revoke authority when communication permits | New revocation information cannot arrive over a fully disconnected link. |
| Local issuer, preferably on the laptop | Apply the local approval rule and sign individual permits | A valid local signature cannot enlarge HQ's grant. |
| Raspberry Pi | Verify the grant and permit; enforce scope, start deadlines, replay rules, and task-state checks; dispatch the approved routine | This is a trusted enforcement component in the core study. |
| Arduino Nano | Supervise a bounded local execution allowance and drive the existing safeguard interface | It trusts Pi admission/completion information; it is not an independent cryptographic verifier. |
| UR5 and gripper | Perform the specified object transfer | Command completion alone does not prove successful placement. |
| Dashboard and recorder | Show decisions, job progress, connectivity, faults, and evidence | Displays must distinguish requested, reported, and physically observed events. |

The new protocol should replace the EWMA trust-score decision. The Nano remains useful for local execution supervision, but the details of its command protocol, heartbeat, timeout, and recovery remain to be specified and implemented.

Two failures must remain distinct:

- **HQ link loss:** authorized local work should remain possible within the grant.
- **Loss of local Pi–Nano supervision:** the system may need to stop because it can no longer supervise the active execution.

The existing safeguard connection is a prototype interface, not a safety-rated independent authorization system. Its presence does not make the Nano capable of defeating a malicious Pi.

**Explain it yourself:** Why should an HQ outage and a failed local watchdog have different effects?

**My notes:**

- 
- 

## 5. Why one disk transfer is one job

A job needs a clear physical boundary. For this project, one job is one disk picked from a known source and placed at a known destination, followed by the defined retreat to a job-completion pose.

The Towers of Hanoi apparatus supplies identifiable objects, discrete destinations, stack heights, and rules for legal moves. Its purpose is to make authorization and execution observable. Solving the puzzle efficiently is not the research contribution.

A permit should bind the job identifier, robot, requester, disk, source, destination, routine, expected state version, and time limits. The execution code must use the checked values. Checking one request and then executing different parameters would break enforcement even if the signatures were valid.

Keep three decisions separate:

1. **Authorized:** does the permission allow this operation?
2. **Valid for the task:** is this the top disk, is the destination legal, and does the expected state match?
3. **Physically executable:** are the calibrated poses, clearance, gripper behavior, and current scene suitable?

A proposed job lifecycle is:

`requested -> checked -> dispatched -> grasping -> transferring -> releasing -> completion confirmed`

Rejected requests do not enter execution. A failed or interrupted transfer enters a fault/uncertain state. The system must not pretend the disk is still at the source, or already at the destination, without evidence.

For the first pilot, operator confirmation and a recording can provide placement evidence. Automatic grasp sensing is not assumed. The final method must state what was actually observed.

### Why replay matters physically

A retransmitted network request must not cause a second pickup. The Pi needs durable job state and duplicate handling. Merely putting a unique number in a permit is insufficient; the verifier must check and remember it.

A crash after release but before logging completion is especially important. The right response is to reconcile the uncertain state, rather than automatically retry. This design should not claim universal exactly-once physical execution.

**My notes — evidence that a disk transfer succeeded:**

- 
- 

## 6. Expiry prevents the next start

Luke's selected policy is **admission-based expiry**. A job checked and started while authorized can finish within an explicitly bounded completion allowance. Expiry blocks new job starts.

Consider the illustrative grant ending at 10:30 with a 30-second maximum runtime. A transfer started at 10:29:55 may finish at 10:30:10. A new transfer requested at 10:30:01 cannot start under that expired grant.

The parent grant must explicitly permit this completion behavior. It is not a loophole allowing arbitrary work after expiry. The active job cannot absorb additional transfers, and a queued job must be checked again at dispatch. A long queue created before expiry does not preserve permission to start later.

Clock handling is part of implementation: the Pi needs a defensible way to evaluate deadlines, account for clock uncertainty, and avoid restoring expired authority after a restart. A monotonic runtime timer helps supervise a running job but does not, by itself, establish the current validity of an HQ-issued absolute deadline.

Longer grant validity supports longer outages, but can prolong the period in which the cell relies on authority that HQ would now revoke. Cached authorization information also has this freshness-versus-availability tradeoff. [RFC 7662, section 4](https://www.rfc-editor.org/rfc/rfc7662.html#section-4)

**Check your understanding:** Why is expiry-at-start compatible with bounded authority? Why is allowing every queued job to start afterward different?

**My notes:**

- 
- 

## 7. The security study: challenge permissions, observe enforcement

The core study does not need a custom score for detecting compromised nodes. It can directly challenge the authorization mechanism with requests that should fail.

| Test | Intended outcome |
|---|---|
| Valid grant and valid in-scope permit | Admit the specified job when the task state and execution conditions also permit it. |
| Altered permit or signature from an unknown key | Reject before dispatch. |
| Genuine local signature authorizing work outside HQ's grant | Reject the excessive permission. |
| Wrong robot, requester, or expected task state | Reject the mismatch. |
| Replayed completed or active job | Do not cause duplicate physical execution. |
| Expired permit at dispatch | Do not start the job. |
| Admission authority expires during an active job | Allow only the bounded completion already authorized; block the next start. |
| Local supervision fails | Apply and record the specified local fault response. |

There is an important limit to the compromised-issuer experiment. An attacker controlling the issuer key can issue cryptographically valid jobs **within** the delegated scope. The verifier can constrain that attacker to the grant; it cannot determine that every in-scope request reflects a benevolent intention.

For the core study, HQ's root key and the Pi verifier remain trusted. Full Pi compromise, physical rewiring, and safety certification are outside the proposed contribution. The system's ordinary robot-command interface must also be restricted so the test client cannot simply bypass the verifier.

Passing these tests is evidence about the implemented cases, not a proof that all possible attacks fail.

**My notes — the attacker capability I want to demonstrate:**

- 
- 

## 8. DIL and the experiment

Here, **DIL** means disconnected, intermittent, and limited communication. The primary experimental link is the backhaul between HQ and the cell. The local robot-control and Nano links remain available in these tests; local failures are separate conditions.

The proposed matrix includes a connected control, 5/15/30 percent random packet loss, short and longer complete outages, repeated up/down intervals, and a limited-bandwidth/delayed case. These are proposed laboratory conditions, not claims about the network conditions of a specific deployment.

Thirty percent packet loss is not equivalent to thirty percent failed jobs. Retransmission, request deadlines, grant renewal, and caching affect the application outcome. Record the achieved network impairment and application behavior instead of assuming the configured loss rate determines the result.

Use matched request traces, root limits, start-validity windows, completion rules, and robot routines across the three architectures where applicable. Include known-in-advance work and newly arriving requests. Report residual differences, particularly the authority given to the local issuer.

Useful measures include:

- Authorized jobs requested, admitted, and physically completed.
- Admission waiting time and time without useful work.
- Rejections, separated by reason.
- Unauthorized admissions or executions observed in the attack tests.
- Duplicate execution, uncertain task state, and recovery intervention.
- Verification cost as supporting engineering evidence.

Repeated home bench tests can exercise real cryptography with a clearly labelled simulated robot. Selected lab trials establish the actual grasp, transfer, release, expiry, and recovery behavior. Simulated transfers must not be counted as physical results.

**My notes — the result that would change my mind about delegation:**

- 
- 

## 9. Connection to the original proposal

| Retained idea | Concrete continuation |
|---|---|
| Secure operation under DIL connectivity | Controlled HQ-link disruption and observed robot job outcomes. |
| Decentralized authority | One constrained local job issuer. |
| Cryptographic authorization | Real signed grants and permits with explicit verification. |
| Central/local comparison | Central approval, pre-issued permissions, and local delegation. |
| Physical enforcement | One UR5, its gripper, Hanoi transfers, and the retained Nano interface. |

The proposed scope removes ZKP/selective disclosure, multi-node mesh scaling, Byzantine-node detection, custom trust scoring, and a standalone signature-algorithm benchmark. The earlier timing work contributes instrumentation experience and reusable components; it does not validate the new authorization protocol.

The possible contribution is a bounded system design and an empirical comparison linking authorization decisions to real robot jobs under disrupted connectivity. Whether this is a sufficient and distinctive thesis contribution still needs the focused literature review and Sodhi's assessment.

## 10. What is real today, and what comes next?

**Current evidence:** the existing V8 project has robot motion, Nano/interface integration, and recording infrastructure. The older Hanoi file contains jaw commands through the UR tool outputs and a disk-transfer routine. The apparatus is reattached. Fresh poses and a working transfer using the current setup still need validation. The new grant/permit architecture is proposed, not implemented or experimentally validated.

**Wednesday, September 30, 11:00 a.m. deliverable:** a runnable Hanoi transfer alongside Luke's revised thesis proposal. Luke has confirmed that live cryptographic delegation is not required for this demonstration.

Today has one hour of lab access. Tomorrow has eight, with three available before the demonstration. The immediate hardware work is to verify jaw control and record fresh poses for one transfer. The one-page proposal should explain motivation, question, approach, comparison, and continuity in Luke's words.

Next, the short systems document should define the authority boundaries, local approval rule, permit fields, job states, expiry/completion rules, replay/restart behavior, and requirements linked to tests. Build the complete bench authorization path before expanding the DIL campaign.

December graduation remains fixed. The normal planning basis is about 20 hours per week and three lab hours per week; tomorrow's longer access is an opportunity, not a new recurring assumption.

### Five questions to answer before writing the one-page proposal

1. What can the local issuer approve that cannot always be decided in advance?
2. What specific authority does HQ retain, and what discretion does it delegate?
3. Why does the robot's physical job boundary matter to authorization?
4. Under what conditions could cached permissions perform just as well?
5. What result would support the thesis even if delegation does not always improve throughput?

**My own explanation, in three sentences:**

1. 
2. 
3. 

**Questions for Sodhi:**

- 
- 

## Project reading map

- [Working research brief](thesis_delegation_brief_2026-09-29.md): agreed direction and unresolved design choices.
- [Proposed system and test matrix](thesis_delegation_test_plan_2026-09-29.md): architecture and candidate evaluation conditions.
- [Current V8 dashboard summary](../docs/v8/DASHBOARD_SUMMARY.md): existing implementation and its measurement limits; it describes the previous timing study.
- [Original proposal](<C:/Users/lukep/Downloads/luke pepin - Thesis Proposal v3.md>): original motivation and broader proposed scope.

The standards cited above are starting points for building and positioning the system. They do not, by themselves, establish its novelty or correctness.
