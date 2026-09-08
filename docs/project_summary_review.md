# On-Edge Project Summary and Review

Status: SKELETON (2026-09-08). Parts are written in order and marked DONE as they land.
Audience: the author, preparing to defend the work. Purpose: explain the project from first
principles up to the audited results, so that every claim in the thesis can be explained,
defended, or conceded from understanding rather than memory. Every number traces to
`ground_truth_v2.md`; where this document and that one disagree, that one wins.

## Contents

Part I — Foundations (what a reader needs before the project makes sense)
  1. The problem in one page
  2. Industrial robot safety: stop categories, safeguard inputs, and what "500 ms" means
  3. Authorization, identity providers, and why a cloud lease is a kill switch
  4. Cryptographic primitives used here: elliptic curves, secp256r1, keygen, ECDSA, Schnorr
  5. Zero-knowledge proofs: what they are, what they cost, and what a "cost proxy" is
  6. Microcontroller timing: the Cortex-M4, the DWT cycle counter, and constant-time code
  7. Exponentially weighted moving averages: the algebra of trust decay
  8. ROS 2 in one chapter: nodes, topics, services, QoS, and the UR driver
  9. Queueing basics used by the project: M/M/1, M/D/1, traffic intensity

Part II — The system as built
  10. Topology and every communication path
  11. The trust-monitor firmware, line by line
  12. The supervisor: joint logger, kinematics node, orchestrator
  13. The safety intercept: optocoupler, SI0/SI1, Category 2, and the latch
  14. The bench harness and the sentry node
  15. What was proposed but never built (and why it matters for the defense)

Part III — The experiments
  16. Campaign history V1–V7: what changed each time and why
  17. Measurement definitions and the audit scripts
  18. Verification cost results
  19. Loop period and the structure of eviction
  20. Eviction latency on the robot (V6, V7) and the outage threshold
  21. Physical stop, the stationary-arm finding, and the dropped-line defect
  22. The failover sweep
  23. Results that were withdrawn, and the exact reason for each

Part IV — Interpretation
  24. The latency model as a design tool
  25. What the data say about ZKP on a Cortex-M4, honestly
  26. The safety-budget argument and its limits
  27. Threats to validity, listed the way a committee will list them
  28. Anticipated committee questions with answers

Part V — Where it goes next
  29. Draft 2: the unified time-to-safe-state model
  30. Draft 2: the hold-down adversary and the wall-clock watchdog
  31. Bench work still possible without the UR5
  32. Glossary
  33. File and data index (what every file in the repository is for)
