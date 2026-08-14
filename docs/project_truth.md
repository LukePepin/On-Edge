# Project Truth

**Companion to `ground_truth.md`. Same authority tier.**

`ground_truth.md` is the numbers ledger: every retained figure, traced to a file,
with withdrawn claims marked. **This document is the prose spine** — what the
project *is*, what it claims, what it does not claim, and which files in the repo
still contradict that. Where the two overlap, they must agree; if they ever
diverge, fix this document to match `ground_truth.md`, never the reverse.

Written 2026-08-12. Reflects state through the V7 real-ZKP campaign and the
end-to-end composition block (335 physical trials total).

---

## 1. What the project actually is

One sentence: **an edge-local trust monitor that keeps an industrial robot
running through network loss, and stops it in hardware when local verification
degrades.**

The honest framing, in the order a reader needs it:

1. Industrial robots draw authorization from a cloud identity provider. Sever the
   network and the lease expires and the robot halts. That involuntary halt is a
   kill switch.
2. This project moves the authorization decision onto edge hardware beside the
   robot so it keeps operating through the outage.
3. Because there is no longer an external authority that can revoke permission,
   the edge node must be able to stop the robot **itself**. It runs an EWMA trust
   score that decays when verification degrades; below 30 it drops a 24 V line
   through an optocoupler into a UR5's safeguard inputs and the arm halts. The
   final step is hardware — no software in the loop.
4. The measured contribution is a **latency model** that predicts, from two
   numbers (verification cycle time and the EWMA weight α), how fast that stop
   happens — validated across 335 physical trials.

That is the whole project. Everything below either supports this or is explicitly
out of scope.

---

## 2. Platform (as built)

- Raspberry Pi 4 — supervisor / orchestrator. Runs the campaign scripts, probes
  the cloud, logs telemetry. **Not** a cryptographic "Vault." It does not hash
  50 Hz kinematics into a vault; that description is fiction from old docs.
- Two Arduino Nano 33 BLE (Cortex-M4) nodes:
  - **Crypto node** — runs the verification workload each cycle, updates the EWMA
    trust score, drives the safety pin. Wired to the UR5 through the optocoupler.
  - **Sentry node** — cloud-viability state machine (CLOUD → ZKP → ECC → rejoin).
- micro-ecc on the Cortex-M4 for the actual elliptic-curve operations.
- Dual-channel 24 V PNP optocoupler into the UR5 SI0/SI1 safeguard inputs.
- UR5 manipulator.
- Communication is USB serial (Pi ↔ Arduinos). Not micro-ROS, not a wireless
  MANET — both were tried and abandoned (see §6).

---

## 3. What the project claims (all retained claims, one place)

Each of these traces to a file and survives audit. This is the complete list of
things the write-up is allowed to assert as results.

1. **The latency model.** Under attack the firmware computes
   `trust(t+1) = (1 − α) · trust(t)`. Eviction (trust ≤ 30 from 100) takes
   `n = ceil(log 0.3 / log(1 − α))` cycles: 12 / 4 / 2 for α = 0.1 / 0.3 / 0.5.
   Stop latency = `n × cycle_period + detection_offset`. Validated across six
   conditions and, with V6/V7, across 335 trials.
2. **α is the weight on the new observation.** Low α = slow decay. The documented
   `Γ(t+1) = α·Γ(t) + (1−α)·N₀` formula is inverted relative to the code. Code is
   correct.
3. **Measured cycle times.** ECC ~111.5 ms crypto (~123 ms loop period); the old
   "ZKP" stub ~334.7 ms; **real ZKP proxy 224.86 ms** (sd 0.21, p95 225.18, 300
   runs, two secp256r1 scalar multiplications). Real ZKP loop period ~247 ms
   including overhead.
4. **The stub was not ZKP.** The "ZKP" path in early trials was three ECC keypair
   generations timed to land under 400 ms. Real ZKP has now been profiled and is
   *cheaper* than the stub claimed (~225 vs ~335 ms), not more expensive.
5. **V6 sub-eviction result (120 trials).** Stop occurs iff the outage spans the
   required cycle count. Stop-rate table (per 10) — 250/500/1000/2000 ms × α:
   0.1 → 0/0/0/10; 0.3 → 0/9/10/10; 0.5 → 4/10/10/10. Boundary cells (4/10,
   9/10) are cycle-boundary jitter deciding marginal cases. Cycle period
   confirmed at ~125 ms by an independent route (inverting min_trust).
6. **V7 real-ZKP result (75 trials).** Confirmatory, pre-registered before
   running; cycle constant amended once to the measured value before trial 1.
   All acceptance criteria met. Guaranteed-eviction latencies at 5000 ms
   (means): α=0.5 ~659 ms, α=0.3 ~1122 ms, α=0.1 ~3030 ms — all within the
   predicted ±1-cycle ranges.
7. **Real ZKP still misses the budget.** At ~247 ms/cycle the fastest possible
   eviction is ~600–700 ms (α=0.5), outside a 500 ms design budget at every α
   tested. Cheaper than the stub claimed, still too slow — the security-tax
   result, properly earned.
8. **End-to-end composition (20 trials).** Total exposure = detection window +
   eviction latency, verified additive to 0.0 ms on a single clock. Measured
   detection ≈ one probe interval (the harness probes immediately at jam onset),
   so the modeled worst case of 2P is a conservative upper bound.
9. **Design-tool inversion.** Given a stop budget and cycle time, the model
   returns admissible α; given budget and α, the maximum affordable cycle time.
   At α=0.5 and 500 ms, cycle time must be under ~170 ms.
10. **Cloud failover sweep (108 cells).** Unmonitored motion after cloud loss is
    non-zero in every configuration (~2 probe intervals; floor ~200 ms at 100 ms
    probing). Detection latency scales with probe interval. K≥3 consecutive
    healthy probes eliminated all false rejoins; K=1 allowed 2. Caveat the
    probe=1000 ms rows (detection often not recorded).
11. **368 ms URScript mode-switch penalty** motivates the hardware bypass.
12. **QoS livelock mitigation:** RELIABLE/KEEP_ALL → BEST_EFFORT/KEEP_LAST(1).
13. **Physical opto-isolated 24 V intercept** halts a live UR5 on trust collapse,
    active-high and therefore fail-safe on power loss.
14. **Randomized trial queue (seed 42)** against thermal and RF confounding.
15. **Cycle time drives eviction latency** — the ~3× slower path evicts ~2.8×
    later. A real result about computational cost and safety response,
    independent of which algorithm produces the cost.

---

## 4. What the project does NOT claim (withdrawn — do not restore)

Any file asserting these is contaminated and must be fixed.

- **22.85% Security Tax** as an ECC-vs-ZKP figure. Withdrawn: the ZKP number it
  compared against was a stub. The real security-tax statement is claim 3.7 above.
- **"ZKP is incompatible with industrial safety"** as an empirical finding. It is
  a *model prediction* from real profiling, not a measured trial outcome yet.
- **The 64-byte CLT / Central Limit Theorem stabilization phenomenon.** The
  firmware runs one loop three times (or two scalar mults), not 64 independent
  constraints. Measured sd is 0.17–0.21 ms — a constant-time workload with no
  variance to compress. Withdrawn entirely, including the 301–346 ms window and
  the Berry-Esseen reference. Also: variance of a sum of n i.i.d. terms *grows*
  (n·σ²); only the coefficient of variation shrinks.
- **Category 0 halt / Latching Cryptographic Halt as a designed feature.** SI0/SI1
  are Safeguard Stop inputs → **Category 2** (auto-resumes on signal restore).
  Category 0 needs EI0/EI1 or cutting power to the safety relays. The C192A4
  dual-channel disagreement fault is real and does latch, but it is a timing
  fault on restoration, not a designed Category 0 stop. *(Amended 2026-08-14 to
  match `ground_truth.md` §5.3: once latched, the C192A4 safety-fault state does
  perform a **Category 0 halt** until manual reset — the fault path ends in
  Cat 0, but this remains an observed fault, never a designed feature.)*
- **Observed-power justification.** Cohen's d = 2.398 computed from the collected
  data, then used to argue n=4 sufficed for 80% power. Circular. Report the
  effect size; do not use it to justify sample size retroactively.
- **ISO 13849-1 specifies 500 ms.** It does not. It governs performance levels,
  MTTFd, diagnostic coverage, architecture categories — no stop-time ceiling.
  500 ms (and the 400 ms bootstrap figure) is a **self-imposed design budget**
  and must be labeled as such every time it appears.
- **H1' null result ("outage duration has no significant effect").** An artifact:
  the firmware had no path to clear `attack_mode_active`, so trust decayed to
  eviction regardless of nominal outage — the factor was never observable.
  Withdrawn and *replaced* by the V6 result (claim 3.5), where the RECOVER fix
  makes outage duration the governing factor.
- **Phase Overlap Hypothesis / "hardware enforces safety before detection
  concludes."** Fabricated. The composition is exactly additive (verified 0.0 ms,
  claim 3.8); the crypto node has no network channel to observe, so it cannot
  decay before the Pi signals it. Delete on sight.
- **N = 121, 1940, or 54 as the campaign size.** 120 = V5 campaign trials.
  1940 = crypto cycles in the swapover log (300 ZKP + 1640 ECC). 121 and 54
  correspond to nothing. Totals now: 120 (V5) + 120 (V6) + 75 (V7) + 20 (e2e)
  = **335 trials**.
- **p\* crossover threshold, MTTR-vs-cloud superiority, NS-3 saturation (n\*),
  M/M/1 → M/D/1 queue numbers as measured results.** These are proposal-era or
  simulation-era framings with no trial data behind them in the retained set.
  QoS mitigation (claim 3.12) survives as an engineering fix; the queueing
  *theory numbers* (ρ = 16.14, μ = 3.10 pkt/s, 610 ms delay) do not.
- **The "Vault" — Pi hashing 50 Hz telemetry for selective disclosure.** Not what
  the system does. The Pi orchestrates and logs; the Arduinos verify.
- **MANET / wireless mesh.** Abandoned (Pivot 1). The system is a USB-serial star.

---

## 5. Scope of the honest thesis (for the write-up)

A master's thesis, not a breakthrough, and it does not need to be one:

- **Core contribution:** the latency model and its inversion into a design tool,
  validated on physical hardware across 335 trials at two cycle times.
- **Method contribution:** a pre-registered, instrumentation-audited experimental
  pipeline — including finding its own instrumented-to-target code, withdrawing
  the affected claims, fixing the firmware, and re-running clean. The audit is a
  strength to present as methodology, not a confession.
- **Engineering contribution:** an opto-isolated hardware safety intercept on a
  live UR5, fail-safe on power loss.
- **Named open gaps (honest, not fatal):** hold-down denial-of-safety
  (unbounded decay suspension under CPU saturation); the failover blind window;
  real ZKP not yet run in physical trials, only profiled and predicted.

---

## 6. Abandoned directions (real history, keep for the pivots chapter)

These happened and belong in an "engineering evolution" narrative — but as
*history*, not as current architecture:

- micro-ROS on the Arduino → SRAM exhaustion → USB-serial star ("Vault & Broker"
  topology, minus the vault mysticism).
- Niryo Ned2 → UR5 (needed real industrial inertia and 24 V servo architecture).
- Software `stopl()` over TCP → 368 ms penalty → hardware optocoupler bypass.
- Binary auth → continuous EWMA.
- Default ROS 2 QoS → BEST_EFFORT/KEEP_LAST(1).

Note: several old docs present these as *finished features of the final system*
(e.g. system_architecture.md still diagrams a ZKP/ECC dual-mesh with a hold-down
state as if shipped). In the pivots chapter they are steps; nowhere are they
current-system claims.

---

## 7. File status (what needs cleaning)

Mirrors `ground_truth.md` §8, expanded with the specific contaminants per file.

**Update 2026-08-14:** this cleaning pass has been applied — see
`decontamination_report.md`. Contaminated files were corrected in place, stale
files archived or removed, and `audit/` renamed `docs/`. The table records the
**pre-cleanup** state and is retained as the audit record.

| File | Status | Specific contaminants to fix |
|---|---|---|
| `conclusion.md` | Contaminated | CLT/Berry-Esseen (§1); M/M/1 ρ=16.14 numbers (§2); Cat 0 latching (§3); N=1940 as campaign ANOVA, "22.85%", ZKP mean 334 as real (§4) |
| `master_research_summary.md` | Contaminated | CLT stabilization; M/D/1 numbers; Cat 0; security tax; hold-down as shipped feature |
| `empirical_conclusions.md` | Contaminated | α levels 0.5/0.7/0.9 (never run); ECC "236–439 ms" (measured 291–505); ZKP as real; H1' null; CLT; observed-power n=4 |
| `outline_v2.md` | Contaminated | §3.4 inverted Γ formula; §4.2 22.85%; §4.3 CLT window; §5 M/M/1/NS-3 numbers; §6.4 Cat 0; superseded until outline_v3 exists |
| `system_architecture.md` | Contaminated | Cat 0 in sequence diagram; ZKP ~334 as real; hold-down shown as shipped; "Vault" hashing; **duplicate file — two identical copies exist, dedupe** |
| `gaps.md` | Mostly correct | §5 (hold-down) is correct and load-bearing. §4 still cites the 224.86 ms figure against a 400 ms bootstrap "43.7% headroom" and an FPGA fix — reframe to the design-budget language; the 224.86 figure itself is now correct |
| `experimental_pivots.md` | Contaminated | Pivot 2 (CLT segmentation, 301–346 ms) withdraw; Pivot 8 (Cat 0 framing) → Cat 2 + timing-fault |
| `original_thesis_proposal.md` | Historical baseline | Do not edit. Keep as contrast; it is explicitly the proposal, not results |
| `running.md` | Superseded | Documents the `--loss`/`--nodes` campaign that was never the final design; contains a logged AI exchange recommending a 54-run fractional-factorial and "Category 0 Halt" — archive, do not treat as runbook |
| `final_lab_plan.md` | Stale | Opens with the observed-power fallacy ("d=2.39 proves n=4"); "7-Hour Mega-Test" and Wednesday defense are historical — archive |
| `audit_checklist.md` | Stale | Pre-video checklist referencing `zkp_trust_monitor/` <400 ms calibration and Cat 0 — archive |
| `README.md` | Stale | Abstract describes MANET / p\* / ZKP mesh; setup references micro-ROS colcon workspace and `on-edge-pi.local` — rewrite abstract to §1, or clearly mark as legacy |
| `ground_truth.md` | Authoritative | Do not edit from other docs |
| `project_truth.md` (this) | Authoritative | Companion to ground_truth; edit only to match it |

---

## 8. The one rule for anyone (human or model) touching these files

Every sentence asserting a result must trace to a file in the retained set.
A claim that cannot be traced is withdrawn, not "probably fine." When a document
disagrees with `ground_truth.md` or this file, the documents are wrong. Do not
edit these two from the others; edit the others from these.
