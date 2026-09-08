# On-Edge Project Summary and Review

Status: COMPLETE first edition (2026-09-08). Parts I–V assembled from docs/review_parts/.
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

---

# Part I — Foundations

This part contains no results. It contains the concepts a reader needs so that, when the
results arrive in Part III, every number has a meaning attached to it. If you already know a
chapter, skip it; but the defense will probe exactly the chapters people skip.

---

## 1. The problem in one page

An industrial robot arm in a factory or a forward-deployed repair cell does not decide for
itself whether it is allowed to move. Something authorizes it. In the architecture this
project started from, that something is a cloud identity provider: a server that issues a
short-lived credential (a "lease"), and the robot's controller keeps moving only while the
lease is valid and renewable. When the network to that server is cut, the lease expires and
the robot stops. In a contested or remote setting, where the network is disconnected,
intermittent, or limited (the "DIL" acronym), the authorization server has become a remote
off-switch for every machine that depends on it.

The project asked a narrow, answerable version of a large question. The large question is:
can authorization be moved to the edge, next to the robot, so that the machine keeps a
verifiable notion of "am I still trusted" without the cloud? The narrow version is: if a small
microcontroller next to the robot runs a cryptographic verification workload continuously
and keeps a trust score that decays when verification fails, how long does it take from the
moment the network goes bad until the robot is physically in a safe state, and what governs
that time?

That narrowing matters. The project did not build a full authorization protocol. It built
the *timing skeleton* of one: a loop that does expensive cryptographic arithmetic every
cycle, a score that decays on failure, a threshold that opens the robot's safety input, and
enough instrumentation to measure how long each of those steps takes on real hardware
attached to a real robot. The result is a small, well-measured model:

> time to eviction ≈ (number of decay cycles needed) × (loop period) + (a partial cycle)

with the number of cycles set by the decay parameter α, and the loop period set by the
cryptographic workload. Both were measured. The rest of this document explains what those
words mean, how the numbers were obtained, and where the evidence is thinner than the prose
of earlier drafts suggested.

Three facts to carry through everything that follows, because earlier project documents
got them wrong:

1. **No zero-knowledge proof was ever verified on the edge node.** The "ZKP" workload is a
   cost proxy: two elliptic-curve scalar multiplications, the arithmetic a Schnorr
   verification would need, without the rest of the verification.
2. **The stop is a Category 2 safeguard stop through the UR5's SI0/SI1 inputs**, driven by
   one Arduino pin. It is not a Category 0 power-removal stop and there is no "STO" path.
3. **The trust score decays only because the supervisor tells the edge node the network is
   down.** The cryptographic workload never fails on its own. The workload's role in the
   experiment is to set the loop period, not to detect anything.

---

## 2. Industrial robot safety: stop categories, safeguard inputs, and what "500 ms" means

### 2.1 Why a robot needs an external safety input at all

A collaborative or industrial arm like the Universal Robots UR5 has its own safety
controller, separate from the motion controller. The motion controller runs the program and
the trajectory; the safety controller watches inputs and internal limits and can override
motion regardless of what the program says. The safety controller exposes a few external
inputs on the control box: an emergency-stop input pair, a safeguard-stop input pair, and on
some configurations a reduced-mode input. These are dual-channel: two physical wires per
function, both of which must agree, so that a single broken wire or stuck contact is
detected rather than silently defeating the function.

The project uses the **safeguard-stop input pair, SI0 and SI1**. In normal operation a 24 V
signal holds both inputs closed. If the signal is removed, the safety controller executes a
safeguard stop.

### 2.2 Stop categories (IEC 60204-1 language)

- **Category 0**: immediate removal of power to the actuators. The arm coasts or is held by
  brakes. On the UR5 this is what "Safe Torque Off" produces; it is the emergency-stop
  behaviour and requires the E-stop inputs or removal of drive power.
- **Category 1**: controlled deceleration to standstill, then power removed.
- **Category 2**: controlled deceleration to standstill, with power retained and the arm held
  in position under monitoring. Motion can resume when the condition clears.

The UR5's safeguard stop is a **Category 2** stop. When SI0/SI1 open, the arm decelerates
under control, holds position, and the running program pauses. When the inputs close again,
the program can be resumed (on this controller, through the teach pendant or the dashboard
server's "play" command; the safety configuration can also be set to auto-resume).

Earlier project documents described the intercept as "Category 0", "Safe Torque Off" and
"STO". All three are wrong for what was wired and what the firmware drives. This matters in
a defense because a committee member who knows the standard will ask which category, and
the honest answer is Category 2, with the qualification that the firmware never re-closes
the input on its own, so the stop is latched by design until the next reconfiguration.

### 2.3 Dual channel and the C192A4 fault

Because the safety controller compares the two channels, restoring them at different
times can trip a "safeguard stop disagreement" fault (UR code C192A4 was observed during
integration). In the built system one Arduino pin feeds both channels in parallel through
the optocoupler block, so any channel skew comes from the optocoupler and wiring, not from
firmware. The fault is real and was observed; it is not a designed feature and it is not a
Category 0 stop. Earlier drafts called it a "latching cryptographic halt"; the accurate
description is a dual-channel timing fault on restoration.

### 2.4 Where "500 ms" comes from

The number 500 ms appears throughout the project as a safety budget. It is important to be
precise about its status: **ISO 13849-1 does not specify a 500 ms stop time.** That standard
defines performance levels, diagnostic coverage, mean time to dangerous failure, and
architecture categories for safety-related control systems. Stop-time requirements come
from a risk assessment of the specific cell (separation distances, approach speeds, and
the machine's measured stopping performance under ISO 13855). In this project 500 ms is a
**self-imposed design budget**, chosen as a plausible order of magnitude for a
collaborative cell. The thesis must say so. The same applies to the 400 ms "ZKP bootstrap"
figure in older documents: it was a threshold chosen to sit above a workload, not a
requirement.

### 2.5 Stopping is not one event

When the safety input opens, several things happen in sequence: the safety controller
registers the input (milliseconds), commands deceleration, the joints decelerate under the
controller's ramp (tens to a couple of hundred milliseconds depending on speed and payload),
and the arm reaches standstill. The project measures the time from a network event to the
*input opening* (with a logged trust value as the marker) and, separately, whether the arm
executed its commanded trajectory at all. It does not isolate the mechanical deceleration
phase from the data it has. Chapter 21 returns to this.

---

## 3. Authorization, identity providers, and why a cloud lease is a kill switch

### 3.1 Identity providers and leases

In modern industrial IT, machines authenticate to an identity provider (IdP) the same way
users do: OAuth-style flows, tokens with an expiry, refresh on a schedule. The controller or
its supervisor holds a token; a policy engine checks it before allowing operations. Token
lifetimes are short by design so that revocation takes effect quickly.

The consequence is a dependency: the machine must reach the IdP at least once per token
lifetime. If it cannot, the token expires and the policy engine denies. For a warehouse with
a fibre backhaul this is a non-issue. For a cell on a ship, a forward base, or behind a
jammed radio link, it is the failure mode the project was built around.

### 3.2 The "cloud-first kill switch"

Earlier drafts used this phrase. The professional version is: *centralized authorization
converts network availability into a precondition for motion*. That is a design choice, and
in some threat models it is the right one (you may want machines to stop when they lose
contact). The project's premise is that in DIL settings it is the wrong one: the loss of the
backhaul carries no information about whether the machine, its program, or its operator are
trustworthy, and stopping production on every link drop is costly and, for a cell mid-task,
can itself be a hazard.

### 3.3 What an edge alternative has to provide

An edge-first alternative needs three things: a local root of trust that can be verified
without the cloud; a way to decide *continuously* whether that trust still holds; and a
physical action when it stops holding. The project is almost entirely about the second and
third: a continuously updated trust score, and a hardware path from that score to the
robot's safety input. The first, the actual verification of a local credential, is where the
built system is a proxy rather than an implementation, and Chapter 15 lists exactly what was
proposed but not built.

### 3.4 The coalition and privacy angle (context only)

The proposal motivated zero-knowledge proofs by a coalition scenario: allied units sharing
a cell should be able to prove they are authorized without revealing their credentials or
identities to the local supervisor. That is a legitimate use of ZKPs (selective disclosure)
and it is why the ZKP path exists in the firmware. But no selective-disclosure protocol was
implemented, so the thesis can present this as the motivation for measuring the *cost* of
ZKP-class arithmetic on the edge device, and nothing more.

---

## 4. Cryptographic primitives used here

### 4.1 Elliptic curves in three paragraphs

An elliptic curve over a finite field is a set of points (x, y) satisfying an equation of the
form y² = x³ + ax + b, plus a point at infinity. Points can be "added" by a geometric rule,
and adding a point to itself k times is *scalar multiplication*, written kP. The security of
elliptic-curve cryptography rests on the fact that computing kP from k and P is easy, while
recovering k from P and kP (the discrete logarithm) is infeasible for well-chosen curves at
256-bit size.

**secp256r1** (also called P-256 or prime256v1) is the NIST curve used throughout this
project, chosen because the micro-ecc library implements it compactly for microcontrollers.
A private key is a 256-bit integer d; the public key is Q = dG, where G is a fixed
generator point on the curve.

Scalar multiplication is the expensive operation. Everything measured in this project is,
underneath, one or two scalar multiplications.

### 4.2 Key generation

`uECC_make_key` draws a random private scalar d and computes Q = dG: **one fixed-base
scalar multiplication** plus the random draw. On the Nano 33 BLE it costs 111.5 ms. This is
the ECC path's workload. Note that it is key generation, not signature verification; the
project's early audit reports pointed this out and it was never changed, so the ECC path is
best described as "one scalar multiplication per cycle".

### 4.3 ECDSA signature and verification

ECDSA signing produces (r, s) from a hash and a private key; verification recomputes a
point from (r, s), the hash, and the public key and checks its x-coordinate. Verification
costs roughly **two scalar multiplications** (one fixed-base with G, one variable-base with
Q) plus a point addition and some modular inversions. The Pi-side wrapper in the repository
(`uecc_wrapper.c`) times `uECC_verify` on the Cortex-A72 at 9.65 ms; that figure supports
the supervisor service-rate work, not the edge-node results.

### 4.4 Schnorr signatures and why they are the ZKP reference point

A Schnorr signature on message m with private key d, public key P = dG: pick random k,
compute R = kG, compute challenge c = H(R ‖ P ‖ m), and s = k + c·d. Verification checks
sG = R + cP. The verification is **two scalar multiplications** (sG fixed-base, cP
variable-base), **one point addition**, **one hash**, and a comparison.

Schnorr's structure (commit, challenge, response) is the simplest instance of a sigma
protocol, which is the building block of many zero-knowledge proofs of knowledge. That is
why "Schnorr verification cost" is a reasonable floor for "what would a simple ZKP
verification cost on this device". The project's proxy executes the two scalar
multiplications and nothing else, so it is a lower bound on the arithmetic of that floor.

### 4.5 micro-ecc and constant time

micro-ecc (uECC) is a small C library for ECDH and ECDSA on curves including secp256r1,
designed for 8-, 32- and 64-bit microcontrollers. It uses a regular (constant-time-style)
scalar multiplication ladder so that timing does not depend on the secret scalar bits. The
practical consequence for this project is that the workload's execution time is extremely
stable from cycle to cycle: the proxy's 300 profiled runs have a standard deviation of
0.21 ms on a 224.9 ms mean. That stability is a property of the library, not a discovery of
the project, and it is the reason the earlier "central limit theorem stabilization" story
had nothing to stabilize.

---

## 5. Zero-knowledge proofs: what they are, what they cost, what a cost proxy is

### 5.1 Definition, minimally

A zero-knowledge proof lets a prover convince a verifier that a statement is true (for
example, "I know a private key for this public key" or "this credential has attribute X")
without revealing anything beyond the truth of the statement. Three properties: completeness
(an honest prover convinces), soundness (a dishonest prover cannot), zero knowledge (the
verifier learns nothing else).

Sigma protocols (Schnorr's is one) achieve this interactively in three moves; the
Fiat-Shamir transform makes them non-interactive by replacing the verifier's random
challenge with a hash. More elaborate systems (Bulletproofs, zk-SNARKs, zk-STARKs) prove
richer statements at higher verifier cost or with trusted setup.

### 5.2 What verification costs on a microcontroller

For the simple Schnorr-style proof of knowledge of a discrete log, verifier cost is
dominated by two scalar multiplications. For a selective-disclosure credential (proving
some attributes of a signed credential without revealing others), the verifier does more:
several scalar multiplications (one per hidden attribute in typical constructions), several
point additions, and hashing. On a Cortex-M4 at 64 MHz with a software curve library, each
scalar multiplication costs about 110 ms, so even a small selective-disclosure verification
lands in the several-hundred-millisecond to second range. That is the "security tax"
intuition, now stated with a measured unit cost rather than a percentage.

### 5.3 What the project's "ZKP path" actually does

The firmware's ZKP path calls `uECC_compute_public_key` twice, on the two 32-byte halves of
a 64-byte scalar buffer. `uECC_compute_public_key(d, Q)` computes Q = dG: one fixed-base
scalar multiplication. So the path performs **two fixed-base scalar multiplications** per
cycle and discards the results (a volatile accumulator prevents the compiler from removing
them). It performs no hash, no point addition, no comparison, and reads no proof from
anywhere. In the control-loop firmware the 64-byte buffer is generated once on the device
and reused every cycle; in the stand-alone profiler the host supplies fresh random bytes
each run.

The honest name for this is a **ZKP-cost proxy**: a workload whose cost equals the scalar
multiplication component of a minimal Schnorr verification. Two things follow. First, any
claim of the form "a ZKP was verified" is false and must not appear. Second, the proxy is a
*lower* bound on the arithmetic of a real verification, so measured eviction latencies with
the proxy are optimistic for any real ZKP scheme.

### 5.4 What was withdrawn and why

Before 2026-08-11 the ZKP path was three calls to `uECC_make_key` (three scalar
multiplications plus three random draws), costing 334.66 ms, and the commit that set it says
it was calibrated to "fit right under the 400 ms threshold". Every ZKP figure from before
that date (334 ms, the 22.85 % "security tax", the 301–346 ms "stabilization window") is
withdrawn. The proxy replaced the stub on 2026-08-12 and every ZKP-labelled result in the
thesis comes from data collected on or after that date.

---

## 6. Microcontroller timing: the Cortex-M4, the DWT counter, and constant-time code

### 6.1 The device

The Arduino Nano 33 BLE carries a Nordic nRF52840: an ARM Cortex-M4F at 64 MHz, 256 KB of
RAM, 1 MB of flash, with Bluetooth radio (unused here) and a hardware cryptographic
accelerator (CryptoCell-310, deliberately *not* used, so that the measured cost is the
software cost a generic Cortex-M4 would pay). The firmware is bare-metal Arduino C++ with
no operating system; the main loop is the only thread of execution, and serial I/O is
polled between cycles.

### 6.2 Measuring time without an OS

`millis()` and `micros()` on Arduino rely on a periodic timer interrupt and have coarse
resolution. The Cortex-M4 provides a Data Watchpoint and Trace unit with a 32-bit cycle
counter (DWT_CYCCNT) that increments every core clock cycle. The firmware enables it, zeroes
it before the workload, and reads it after. The difference is the number of core cycles the
workload took, including any interrupt time that fell inside the window (none of consequence
here, since the only interrupt source is the USB serial peripheral).

Converting cycles to milliseconds requires knowing the clock: at 64 MHz, 64,000 cycles per
millisecond. The firmware and the host script both hard-code that constant. The project did
not measure the clock directly; instead the bench block, which timestamps trust lines on
the host clock, measured one full loop iteration at 232.1 ms for the proxy and 120.4 ms for
ECC. Adding the 10 ms delay and a few milliseconds of serial print to the DWT-derived
workload costs (224.9 and 111.5 ms) predicts about 240 and 127 ms. Agreement within about
four percent means the 64 MHz assumption cannot be far wrong; it is not an independent
calibration of the oscillator.

### 6.3 The loop, precisely

Each iteration of `loop()`:

1. Drain the serial input, one character at a time, until a newline; act on complete
   commands (`ATTACK`, `RECOVER`, or a JSON configuration).
2. Run the selected workload with the cycle counter around it.
3. Compute the per-cycle trust observation, update the EWMA, compare to the threshold, and
   drive the safety pin.
4. Print one JSON line: cycle index, execution time in ms, trust score.
5. `delay(10)`.

Commands are therefore acted on only at step 1 of the *next* iteration. An `ATTACK` that
arrives during step 2 waits for the rest of that cycle, then takes effect. This single fact
explains the "partial cycle" term in the latency model and the uniform spread of about one
loop period seen in every eviction-latency group.

### 6.4 Why the numbers are so stable

Constant-time scalar multiplication, no OS, no cache effects to speak of, one interrupt
source: the workload cost varies by about 0.1 % across runs. This is why the project can
treat the loop period as a constant and why the eviction-latency model has only two
parameters (cycle count and period) and no noise term beyond the attack phase.

---

## 7. Exponentially weighted moving averages: the algebra of trust decay

### 7.1 The update rule

The firmware keeps one number, the trust score Γ, initialized to 100, and updates it every
cycle with a new observation c:

    Γ ← α·c + (1 − α)·Γ

Here α is the weight on the *new* observation. This is the standard EWMA form. Two
conventions exist in the literature; the other one puts α on the history term. The project's
earlier outline wrote the formula with α on the history term while the code puts it on the
new observation; the code is what ran, so the thesis uses the code's convention. With this
convention, **larger α means faster reaction**, which is why α = 0.5 evicts fastest.

### 7.2 What the observation is

In the built system c takes only two values. When the supervisor has asserted `ATTACK`,
c = 0. Otherwise c = 100, unless the workload's own execution time exceeded a threshold
(400 ms for the proxy, 150 ms for ECC), in which case c is reduced by the excess. Since the
workloads run at about 60 % of their thresholds, that branch never executes in any recorded
trial. So in practice: c = 0 under attack, 100 otherwise.

### 7.3 Decay under attack

With c = 0 the update is Γ ← (1 − α)·Γ, a geometric decay. Starting from 100, after k
attacked cycles Γ = 100·(1 − α)^k. Eviction happens when Γ < 30. Solving 100(1 − α)^k < 30:

    k > ln(0.3) / ln(1 − α)

so the number of attacked cycles needed is n(α) = ⌈ln 0.3 / ln(1 − α)⌉:

| α | (1−α) | sequence from 100 | n(α) |
|---|---|---|---|
| 0.1 | 0.9 | 90, 81, 72.9, 65.6, 59.0, 53.1, 47.8, 43.0, 38.7, 34.9, 31.4, **28.2** | 12 |
| 0.3 | 0.7 | 70, 49, 34.3, **24.0** | 4 |
| 0.5 | 0.5 | 50, **25** | 2 |

These exact sequences are visible in the raw data, which is what made it possible to count
dropped telemetry lines later (Chapter 21): if the logger shows 50 and then 12.5, the 25
was emitted by the firmware and lost in transit.

### 7.4 Recovery after the attack clears

When `RECOVER` arrives, c returns to 100 and Γ ← 0.5·100 + 0.5·Γ (for α = 0.5) climbs
geometrically back toward 100: from 50 it goes 75, 87.5, 93.75, and so on. If the score
never crossed 30, nothing happened to the robot. If it did cross, the safety pin is already
low and the firmware does not raise it again on recovery; only a new configuration message
raises it. Recovery of the score therefore has no physical effect after an eviction.

### 7.5 What an EWMA does and does not give you

The EWMA gives a tunable delay between the onset of failure and the safety action, with a
single parameter and no memory beyond one number. The delay is quantized in cycles, so its
resolution is the loop period. It also gives a natural threshold behaviour on outage
duration: an outage shorter than n(α) cycles never evicts, one longer always does. The
project's V6 and V7 campaigns are essentially a measurement of that threshold and that
delay. What the EWMA does not give is any robustness against a supervisor that stops
reporting: the score only ever falls because the supervisor says so.

---

## 8. ROS 2 in one chapter

### 8.1 What ROS 2 is, for this project

ROS 2 is middleware for robot software: processes ("nodes") exchange typed messages over
named topics (publish/subscribe), call each other's services (request/reply), and run
long-running goals through action servers. Underneath, DDS handles discovery and transport.
The project's supervisor runs ROS 2 Humble on Ubuntu 22.04 on a Raspberry Pi 4.

### 8.2 The three nodes that matter

- **`ur_robot_driver`** (third party): connects to the UR5 controller over Ethernet using
  the RTDE interface, publishes `/joint_states` (positions and velocities at up to 500 Hz on
  a real controller, throttled here) and the wrist IMU, and exposes trajectory controllers.
- **`joint_logger`** (project): subscribes to joint states and IMU, owns the serial link to
  the trust monitor, exposes the `/inject_attack` service, and writes the 50 Hz CSV on its
  own timer using the PC clock so that the timeline continues even when the robot's stream
  pauses.
- **`stream_wrist_kinematics`** (project): sends the two-phase trajectory to the UR5's
  `passthrough_trajectory_controller` as a `FollowJointTrajectory` action goal and calls
  `/inject_attack` half a second after sending the second phase.

### 8.3 Controllers and why "passthrough" was chosen

`ros2_control` on the UR driver offers several controllers. `scaled_joint_trajectory_controller`
interpolates the trajectory on the Pi and streams setpoints; `passthrough_trajectory_controller`
hands the waypoints to the UR controller, which interpolates natively. The project moved to
passthrough after Pi-side CPU jitter caused timing faults and protective stops. A related
lesson from June: specifying zero velocities at sparse waypoints forced quintic
interpolation with unrealistic acceleration; leaving velocities unspecified gives cubic
splines and smooth motion.

### 8.4 QoS in one paragraph

DDS lets each publisher and subscriber declare quality-of-service: reliability (RELIABLE
retransmits; BEST_EFFORT does not) and history (KEEP_ALL queues everything; KEEP_LAST with a
depth keeps only the newest N). For sensor streams BEST_EFFORT/KEEP_LAST(1) is standard: a
stale joint state is worthless, so drop it. The project's supervisor auth-request service
uses BEST_EFFORT/KEEP_LAST(1). Earlier documents claimed a measured "99.6 % shedding" effect
from switching QoS; no such measurement exists in the repository, and the thesis treats the
QoS choice as a design decision, not a result.

---

## 9. Queueing basics used by the project

### 9.1 Arrival rate, service rate, traffic intensity

A server that takes on average 1/μ seconds per job can complete μ jobs per second. If jobs
arrive at λ per second, the traffic intensity is ρ = λ/μ. If ρ ≥ 1 the queue grows without
bound; if ρ < 1 it is stable, with delays that blow up as ρ approaches 1.

### 9.2 M/M/1 versus M/D/1

M/M/1 assumes exponentially distributed service times; M/D/1 assumes deterministic
(constant) service times. Mean queue length in M/G/1 (general service) is given by the
Pollaczek–Khinchine formula, L_q = ρ²(1 + C_v²) / (2(1 − ρ)), where C_v is the coefficient
of variation of service time. For deterministic service C_v = 0 and the queue is half as
long as M/M/1 at the same ρ. The project's supervisor-side verifier (`uECC_verify` on the
Pi) has C_v = 0.017, so M/D/1 is the right model for it. The service time was measured at
9.65 ms (n = 1000), giving μ = 103.6 requests per second; that file was later deleted from
the working tree but is recoverable from git history and its statistics reproduce.

### 9.3 What the project claims here, and what it does not

What survives: the Pi-side service time and its near-zero variance, and the fact that the
supervisor's authentication service uses BEST_EFFORT/KEEP_LAST(1). What does not survive:
any measured livelock threshold, any before/after QoS comparison, the "3.10 packets per
second" service rate for a 64-byte payload (that came from the withdrawn stabilization
story), and the NS-3 extrapolations built on it. The queueing material belongs in the thesis
as design rationale and as future work, not as a result chapter, which is why the Draft 1
chapter map removed it from the results.

---

*End of Part I.*


---

# Part II — The system as built

Everything in this part is present in the repository at the commit audited on 2026-09-07
(HEAD fd2eba4, then cleaned up on 2026-09-08). Line numbers refer to the files as they stand
after the cleanup; the audit notes in `audit/` carry the pre-cleanup references.

---

## 10. Topology and every communication path

### 10.1 The five boxes

1. **Mock cloud identity provider.** A small Python server. In the robot campaigns it is a
   TCP server on a laptop that streams `AUTH_OK`; in the bench block it is an HTTP health
   endpoint on the Pi itself. It exists to be severed. Nothing about it is measured.
2. **Supervisor: Raspberry Pi 4.** Runs ROS 2, the UR driver, the joint logger, the
   kinematics node, and the campaign orchestrator. Talks to the robot over Ethernet, to the
   edge node over USB serial, and to the mock cloud over Wi-Fi or loopback.
3. **Edge node: Arduino Nano 33 BLE.** Runs the trust-monitor firmware. Talks only over USB
   serial to the supervisor, and drives one output pin.
4. **Optocoupler block.** Converts the pin's 3.3 V logic to the 24 V PNP signal the UR5
   expects, on both safeguard channels in parallel.
5. **UR5 with its CB controller.** Executes trajectories from the supervisor, reports joint
   states, and stops when its safeguard inputs open.

The Draft 1 figure (`figures/system_flow.mmd` in the thesis repository) draws these with
every arrow labelled. The important structural fact is that there are **two independent
paths from the supervisor to the robot**: the ROS 2 path (trajectory goals, dashboard
commands, joint-state feedback) and the trust path (serial to the edge node, then the pin,
then the safety input). The experiment measures the trust path's latency using timestamps
recorded on the ROS 2 path.

### 10.2 The serial protocol

Both directions are newline-terminated text at 115,200 baud.

Supervisor → edge node:
- `{"algo": "ECC"|"ZKP"|"CLOUD", "alpha": <float>}` — configure. Resets Γ to 100, resets the
  cycle counter, clears the attack flag, raises the safety pin, replies `{"status": "READY"}`.
  Sent at boot (the firmware blocks until it gets one) and at the start of every trial.
- `ATTACK` — set the attack flag. Sent at 20 Hz for the duration of the nominal outage.
- `RECOVER` — clear the attack flag without touching Γ. Added 2026-08-11.

Edge node → supervisor, once per cycle:
- `{"cycle": <int>, "exec_time_ms": <float>, "trust_score": <float>}`

Nothing else crosses the link. In particular, no joint data, no hashes, no credentials and
no proofs go to the edge node; the "vault and broker" data flow in older architecture
documents was never implemented.

### 10.3 The ROS 2 path

- `ur_robot_driver` ↔ UR5 controller: RTDE over Ethernet, plus the reverse interface for
  trajectory passthrough. The URCap "external control" program must be running on the
  pendant for the driver to command motion; a safeguard stop pauses it.
- Kinematics node → driver: one `FollowJointTrajectory` action goal per phase to
  `/passthrough_trajectory_controller`.
- Driver → joint logger: `/joint_states` and `/io_and_status_controller/ur_imu`.
- Kinematics node → joint logger: the `/inject_attack` service (a `std_srvs/Trigger`).
- Orchestrator → UR5 dashboard server (TCP port 29999): `unlock protective stop` and `play`
  between trials.

### 10.4 Timing sources

Three clocks appear in the data. The **edge node's DWT counter** measures workload cost.
The **supervisor's PC clock** timestamps every logger row and every bench event. The
**UR controller's clock** is never used directly; joint states are stamped on arrival by the
logger's 50 Hz timer. All eviction latencies in the robot campaigns are differences of
supervisor timestamps; all loop periods are differences of supervisor timestamps in the
bench block. No cross-clock subtraction is ever performed, which is one reason the numbers
are clean.

---

## 11. The trust-monitor firmware, line by line

File: `firmware/unified_trust_monitor_template/unified_trust_monitor_template.ino`, 268 lines.

### 11.1 Globals (lines 11–46)

`current_algo`, `ewma_alpha` (default 0.3, always overwritten by configuration),
`EVICTION_THRESHOLD = 30.0`, `trust_score = 100.0`, `cycle_count`, `attack_mode_active`.
DWT register macros. `#define uECC_CURVE uECC_secp256r1` before including micro-ecc. A
`rand()`-based RNG handed to micro-ecc (weak entropy, noted in the early audit reports, and
irrelevant to timing). Two booleans selecting the workload. `SAFETY_PIN = 12`.

### 11.2 setup() (lines 48–105)

Serial at 115,200; pin 12 output, driven HIGH immediately ("start in active state to
prevent reset jitter"); DWT enabled; wait for the USB serial connection; then **block**
until a JSON line with both `algo` and `alpha` arrives. On success: set the workload flags,
reply READY, drive pin 12 HIGH again. The firmware therefore never runs a workload until the
supervisor has configured it, and the safety loop is closed from power-up.

### 11.3 execute_ecc_verification() (lines 111–153)

Zero the cycle counter, call `uECC_make_key`, read the counter, convert to ms. Then:

```
if (attack_mode_active) current_trust = 0.0;
else if (exec_time_ms > 150.0) current_trust = max(0, 100 - (exec_time_ms - 150));
else current_trust = 100.0;
trust_score = alpha*current_trust + (1-alpha)*trust_score;
if (trust_score < 30.0) digitalWrite(SAFETY_PIN, LOW);
print JSON; cycle_count++; delay(10);
```

Note what is absent: no `digitalWrite(SAFETY_PIN, HIGH)` anywhere in this function. Once
the pin goes LOW it stays LOW until a configuration message.

### 11.4 execute_zkp_verification() (lines 155–210)

Identical structure. The workload (lines 162–176):

```
static uint8_t attributes[64]; static bool payload_init = false;
if (!payload_init) { RNG(attributes, 64); attributes[0] |= 1; attributes[32] |= 1; payload_init = true; }
volatile int acc = 0;
acc += uECC_compute_public_key(&attributes[0],  public_key); acc += public_key[0];
acc += uECC_compute_public_key(&attributes[32], public_key); acc += public_key[0];
```

Two scalar multiplications on a buffer generated once. The `|= 1` forces the low bit so the
scalars are odd (nonzero). The volatile accumulator stops the optimizer from deleting the
calls. The penalty threshold here is 400 ms. The comment above the block reads "Real ZKP
proxy", and the thesis keeps that honesty.

### 11.5 loop() (lines 215–268)

Character-at-a-time serial drain into `input_buffer` (capped at 200 characters). On
newline: `ATTACK` sets the flag; `RECOVER` clears it; a JSON object with `algo` and `alpha`
performs the full reset described in 10.2 and raises the pin. Then one workload call
depending on the flags. A `CLOUD` configuration sets neither flag, so the loop does nothing
but drain serial; that mode was used in the abandoned three-algorithm matrix and in the
Aug-10 swapover demo.

### 11.6 Properties that follow

- Command latency: up to one loop period, uniformly distributed, because commands are read
  only at the top of the loop.
- Latching: no path re-raises the pin except reconfiguration.
- The exec-time penalty never fires in practice (workloads at ~60 % of thresholds).
- Under `ATTACK`, `exec_time_ms` continues to be measured and printed but has no effect on
  trust; the workload's only role during an attack is to consume one loop period.
- Single pin: the "dual-channel synchronized GPIO" described in older documents does not
  exist in this file. The dual-channel behaviour is entirely in the wiring.

### 11.7 History that matters

- 2026-08-05: unified template created; ZKP stub set to 3× keygen "to fit under 400 ms".
- 2026-08-06: attack made non-blocking (trust forced to 0 instead of extra keygen loops).
- 2026-08-11 18:43: `RECOVER` added. This is the commit that made outage duration a real
  factor. V6 ran that evening.
- 2026-08-12 11:46: ZKP stub replaced by the two-multiplication proxy; comments changed from
  "Category 0" to "Category 2". V7 ran two minutes later. Luke confirms no uncommitted edits
  were flashed (2026-09-07).

---

## 12. The supervisor: joint logger, kinematics node, orchestrator

### 12.1 joint_logger_node.py (320 lines)

Parameters: `algo`, `outage` (ms), `iteration`, `alpha`, `timestamp` (Unix seconds, passed
in by the shell script so the CSV and the packet capture share a name).

Startup: open `/dev/ttyACM0` (or `ttyACM1`), send the configuration JSON repeatedly for up
to 6 s until READY comes back, else abort the trial. Then start a serial-reader thread and a
CSV-writer thread, subscribe to joint states and IMU, create the `/inject_attack` service,
and start a 50 Hz timer.

The 50 Hz timer (`log_timer_callback`) writes one row: PC time (seconds and nanoseconds),
the latest trust score received, six joint positions, six joint velocities (forced to zero
if no joint-state message has arrived in the last 100 ms, on the assumption that a paused
URCap means standstill), raw and EMA-filtered IMU acceleration, and the attack flag.

The attack sequence (`_execute_attack_sequence`): for the nominal outage duration, write
`ATTACK\n` every 50 ms; then write `RECOVER\n` and clear the flag. For the `CLOUD` algorithm
it instead inserts and removes an iptables rule on port 8080; that branch was not used in
V5–V7.

The serial reader (`serial_read_loop`, lines 148–161) is the source of the dropped-line
defect: it calls `reset_input_buffer()`, sleeps 10 ms, and does one non-blocking
`readline()`. A line that straddles the flush or the read boundary is discarded (a partial
line fails the `{...}` check). Chapter 21 quantifies the effect. The design intent was to
always read the freshest line; the side effect was losing 10–20 % of lines.

### 12.2 stream_wrist_kinematics.py (267 lines)

Phase 1: send a single-waypoint goal that moves the arm to the Pick pose over 5 s. Wait for
the result, then poll joint states until the arm is at standstill (joint position change
below 2 mrad between messages).

Phase 2: send a five-waypoint goal: Pick at 1 s, Transfer at 3 s, Place at 5 s, Transfer at
7 s, Pick at 10 s. Waypoints are normalized to the shortest angular path from the current
pose to avoid full-turn unwinds. Velocities are left unspecified so the UR controller uses
cubic interpolation. Immediately after sending, a thread sleeps 0.5 s and then calls
`/inject_attack`. The same thread sleeps a further 60 s and then hard-exits the process so
the shell script is never blocked by a paused robot.

The consequence for the results: since the first waypoint is the pose the arm is already
in, at 1 s, commanded motion effectively begins between 0.5 and 1.0 s after the attack.
Fast evictions land before the arm moves.

### 12.3 run_test.sh (139 lines)

Argument parsing (`--algo`, `--outage`, `--iter`, `--alpha`); checks `ulimit -l` is
unlimited (for `mlockall`); clears leftover iptables rules; kills zombie loggers; starts
`tshark` on the wireless interface writing to `/tmp`; starts the joint logger under
`taskset 0x7` and `chrt -f 99`; sleeps 6 s for the handshake, prints a 4 s warning for the
operator to press Play; switches the UR controller to passthrough; runs the kinematics node
under the same real-time settings and waits for it; sleeps 3 s; kills everything; moves the
pcap into `data/`. The CSV name is built as
`trial_<ALGO>_outage<OUTAGE>_ewma<alpha*10>_iter<ITER>_<timestamp>.csv`.

### 12.4 run_campaign.py (192 lines)

Builds the factorial list, shuffles with `random.seed(42)`, optionally takes one half
(`--half 1|2`), and loops: run `run_test.sh`, validate the CSV (at least 50 rows and the
attack flag seen), append to `data/sub_eviction_summary.csv` if valid, else re-queue the
trial with an incremented attempt counter and reshuffle the remainder. After every trial,
`recover_robot()`: 2 s pause, dashboard `unlock protective stop`, 2 s, dashboard `play`, 3 s.

The validation rule changed on 2026-08-11. Before that a trial was rejected unless it
*stopped*; with a working outage factor that would have re-queued every legitimate
non-stop trial forever. The rule now checks only that the trial ran.

### 12.5 What the supervisor does not do

It does not hash telemetry, does not send anything to the edge node except configuration
and attack/recover keywords, does not verify anything cryptographic in the robot campaigns,
and does not participate in the safety path except by telling the edge node when the
network is "down". The supervisor's `supervisor_node.py` (an auth-request service with the
Pi-side `uECC_verify` timing wrapper) belongs to the July service-rate work and is not part
of any V5–V7 trial.

---

## 13. The safety intercept

### 13.1 The circuit

Arduino D12 (3.3 V logic) → optocoupler block input → 24 V PNP output → UR5 SI0 and SI1 in
parallel (Luke, 2026-09-07). The block is active-high: logic high closes the safeguard loop.
Loss of power or connection on the Arduino side therefore opens the loop, which is the
fail-safe direction.

### 13.2 What the UR5 does when the loop opens

Safeguard stop: controlled deceleration, hold position, program paused, pendant shows the
safeguard-stop state. Category 2. Drive power remains. When the loop closes again the
program can be resumed with Play (or auto-resume if configured). Between trials the
orchestrator issues `unlock protective stop` and `play` via the dashboard; `unlock
protective stop` is harmless if no protective stop is present and covers the case where a
trajectory fault occurred.

### 13.3 What the firmware does when the loop should close again

Nothing, until the next configuration message. The score may recover to 100 after
`RECOVER`, but the pin stays low. This is by construction, and the thesis should describe it
as a latched Category 2 stop with reset by reconfiguration, not as an auto-resuming stop and
not as a Category 0 stop.

### 13.4 The C192A4 disagreement fault

Observed during integration. With one pin feeding both channels, any skew between channels
on restoration is a property of the optocoupler pair and wiring. The fault forces a
pendant-level reset. It is worth a paragraph in the thesis as an observed integration
hazard; it is not a designed security feature.

### 13.5 What is not in the loop

No emergency-stop input, no reduced-mode input, no power relay. Nothing the firmware does can
remove drive power. If a committee member asks "what if the arm must be de-energized", the
answer is that this design does not do that and a Category 0 path would need the EI0/EI1
inputs or a relay on the drive supply, both of which are future work.

---

## 14. The bench harness and the sentry node

### 14.1 run_end_to_end_campaign.py (196 lines)

Runs on the Pi with only the trust monitor attached. Starts a local HTTP server on
127.0.0.1:8081 whose `/health` returns 200 while `cloud_is_up` is true and hangs for 2 s
otherwise. For each trial (probe interval 100 or 500 ms; workload ECC or proxy; α = 0.5;
five iterations): configure the edge node; for 3 s, probe at the interval; then set
`cloud_is_up = false` and record `t_jam`; probe immediately and on each failure (the first
one, in practice) record `t_detection` and send `ATTACK`; read the serial stream by
accumulating all bytes and splitting on newlines (no drops); record `t_first_decay` at the
first trust value below 100 and `t_eviction` at the first value ≤ 30; then send `RECOVER`.

Because all four timestamps are `time.time()` on the same host, the differences are direct.
The script also computes a "predicted_total" from hard-coded cycle times of 125 and 247 ms;
that column is untraced and is not used.

### 14.2 sentry_node.ino (93 lines)

A state machine on a second Arduino with no cryptography. States: CLOUD, ZKP_BOOTSTRAP,
ECC_STEADY. Inputs from the host: `CONFIG:K,DWELL`, `CLOUD_UP`, `CLOUD_DOWN`,
`BOOTSTRAP_COMPLETE`, `REJOIN_CONFIRMED`, `REJOIN_FAILED`. Outputs: transition messages and
`INITIATE_REJOIN`. The rejoin request is emitted only when K consecutive `CLOUD_UP` events
have been received and at least DWELL_MS have elapsed since the first of them; any
`CLOUD_DOWN` resets both. The state becomes CLOUD only on `REJOIN_CONFIRMED`. This replaced
(2026-08-11) an earlier version that rejoined on a fixed 15 s timer regardless of
connectivity.

### 14.3 run_cloud_failover_sweep.py (287 lines)

Host side of the sentry test. Serves a mock cloud on 127.0.0.1:8080 with three failure
patterns (hang; alternate 500 ms up/down; respond slowly), probes it at the configured
interval requiring HTTP 200 and a JSON `status: ok`, forwards `CLOUD_UP`/`CLOUD_DOWN` to the
sentry, simulates the crypto node's bootstrap by sending `BOOTSTRAP_COMPLETE` 1.5 s after
the sentry enters ZKP_BOOTSTRAP, and on `INITIATE_REJOIN` re-probes the cloud before
answering `REJOIN_CONFIRMED` or `REJOIN_FAILED`. Records detection latency, recovery
latency, "unmonitored motion" (probe count × interval while in CLOUD with the cloud down),
false rejoins, and excess oscillations.

Limits: everything is on one host with a loopback cloud; one run per configuration; the
archived results file predates a serial-parsing fix and its probe = 1000 ms rows are
unusable. The sweep never involved the robot or the trust monitor.

---

## 15. What was proposed but never built

A defense goes badly when the candidate is surprised by a gap the committee already found.
This list is the set of things earlier project documents describe as existing that do not
exist in the repository.

| Described in earlier documents | Status in the built system |
|---|---|
| ZKP selective-disclosure verification on the edge node | Not built. Two scalar multiplications on a static buffer. |
| 64-byte "independent constraints" payload with CLT stabilization | Not built. One loop, deterministic cost, sd 0.2 ms. The profiler file cited for it never existed. |
| Hashed telemetry streamed to the edge node ("vault and broker") | Not built. Nothing but keywords and configuration crosses the serial link. |
| Kinematic trajectory hashes unlocked by verification | Not built. |
| Nine Arduino worker nodes in a star | One trust monitor (plus one sentry on the bench). |
| Dual-channel synchronized GPIO with < 20 ms skew | One pin; channels paralleled in wiring. |
| Category 0 / STO stop | Category 2 safeguard stop. |
| Hold-down suspension of EWMA decay during legitimate crypto work | Not built. Trust is forced to 0 whenever ATTACK is asserted. |
| Token-bucket admission control | Not built. |
| 368 ms URScript mode-switch penalty measurement | No data or script in the repository. |
| 99.6 % boot-storm shedding from QoS change | No measurement in the repository. |
| IMU + Extended Kalman Filter deceleration proof | Not built. IMU is logged raw and EMA-filtered; never analysed. |
| Ledger/SQLite work-order reconciliation on rejoin | Not built. |
| NS-3 extrapolation to n* | Simulations exist in history, built on the withdrawn 3.10 packets/s figure. Not usable. |

Each of these can be presented as future work or as a design intent that was descoped when
the hardware sprint ran out of time. None of them can be presented as done.

---

*End of Part II.*


---

# Part III — The experiments

This part is the evidence. Each chapter names the files the numbers come from and the
script that recomputes them. If a number here is not in `ground_truth_v2.md`, this part is
wrong and that file is right.

---

## 16. Campaign history V1–V7: what changed each time and why

The project ran seven campaigns in eight days (2026-08-05 to 08-12). Only the last three are
usable for the thesis, and it is important to be able to say precisely why the first four
are not.

| Campaign | Date | Factor varied | Firmware state | Verdict |
|---|---|---|---|---|
| V1 | Aug 5 evening | random packet loss 25/50/75 % via iptables; ECC vs stub; α .1/.3/.5; n=3 | stub ZKP; attack latched | Probabilistic loss never reached the firmware as a factor; superseded the same night. |
| V2 | Aug 5–6 night | "deterministic outage" 500–5000 ms; resolution-IV 12-config design; n=12 | same | First use of ATTACK keyword flooding. No RECOVER, so every trial latched. 19 trials failed to fire and were not re-run. |
| V3 | Aug 6 afternoon | full 2×4×3 (α .5/.7/.9) | same, blocking attack loops | 20 failed trials not re-run. |
| V4 | Aug 6 evening | same matrix, randomized queue, re-run on failure | non-blocking attack (trust forced to 0) | Complete 120-cell matrix, but attack latched: every trial evicts regardless of outage. The "H1' null result" came from here. |
| V5 | Aug 7 | α changed to .1/.3/.5, outage 500–5000, n=5 | same | Complete, clean, latched. Kept as the latched-attack baseline. |
| V6 | Aug 11 evening | ECC only; outage 250–2000; n=10 | **RECOVER added 18:43** | First campaign in which outage duration is a real factor. |
| V7 | Aug 12 | proxy only; outage 250–5000; n=5 | **proxy replaces stub 11:46** | First campaign with the measured ZKP-cost workload. |

Three things to be able to say in a defense:

- Why α changed from {.5,.7,.9} to {.1,.3,.5}: the high values all evict in one or two
  cycles and give no resolution; the low set spans 2 to 12 cycles.
- Why the outage set changed between V6 and V7: the threshold n(α)·T_cycle is about twice
  as long for the proxy, so the levels were shifted up to bracket it (250/500/1000 below,
  3000/5000 above, 1000 near the α = 0.3 boundary).
- Why V6 and V7 were never run together: time. The UR5 was available for a few more hours.
  The consequence, that ECC versus proxy is a between-campaign comparison, has to be stated.

The "latched attack" defect deserves its own sentence. Before Aug 11 the firmware had
exactly one attack command and no way to clear it except a full reconfiguration. The
supervisor's logger did stop sending ATTACK after the nominal duration, but the flag on the
device stayed set, so the score decayed to eviction in every single trial. The logger's own
`attack_active` column shows the same thing from the other side: in V5 it stays at 1 for
about 63 s, the length of the trial, regardless of the nominal 500–5000 ms. So the earlier
finding "outage duration has no effect" was a statement about a factor that was never
delivered. It was withdrawn and replaced by the V6/V7 threshold result.

---

## 17. Measurement definitions and the audit scripts

Every quantity in Parts III and IV is one of the following. The scripts live in `audit/`.

| Quantity | Definition | Script |
|---|---|---|
| Verification cost | DWT cycles ÷ 64,000 per workload call | `zkp_profile_stats.py` |
| Loop period T_cycle | host time between trust 50 and trust 25 at α = 0.5 (bench) | inline in `phase2_zkp.md` |
| Trial validity | ≥ 50 logger rows and `attack_active`=1 observed | `inventory_trials.py` |
| Eviction latency (logged) | first row with trust ≤ 30 after attack − first row with attack flag | `eviction_latency.py` |
| First-decay latency | first row with trust < 100 after attack − attack flag | same |
| Step sequence | distinct successive trust values during decay | same |
| Physical stop | joint speeds < 0.02 rad/s from before t_attack + 8.5 s through + 9.5 s | `physical_stop_crosstab.py` |
| Capture ratio | expected decay values 100(1−α)^k actually present in the log | `telemetry_capture.py` |
| Crossing missed | first logged value ≤ 30 is not the first expected value ≤ 30 | same |

Two definitions need justification.

**Why physical stop is defined by motion.** The trajectory commands continuous motion from
about half a second after the attack until about nine and a half seconds after it. An arm
that sits still for that entire window did not execute its program, and the only mechanism
in the cell that prevents program execution is the safeguard input. The definition is
therefore a direct observation of the safety action, independent of the trust telemetry.
It cannot be fooled by a dropped serial line. It can be fooled only by a trial in which the
program was not running at all, which the orchestrator's Play command and the presence of
phase-1 motion rule out (phase-1 motion is visible in every valid file).

**Why 0.02 rad/s.** The controller's idle jitter on a stationary UR5 is below 0.01 rad/s in
these logs; 0.02 gives margin without admitting slow real motion (the slowest commanded
segment exceeds 0.1 rad/s).

---

## 18. Verification cost results

File: `data/real_zkp_profiling.csv`, 300 rows. Columns: cycle, start_cycles, end_cycles,
total_cycles, exec_time_ms, res1, res2, keybyte.

| Statistic | Value |
|---|---|
| n | 300 |
| mean | 224.864 ms |
| standard deviation | 0.209 ms |
| minimum | 224.083 ms |
| median | 224.867 ms |
| 95th percentile | 225.183 ms |
| maximum | 225.391 ms |
| coefficient of variation | 0.093 % |
| Shapiro–Wilk | W = 0.995, p = 0.44 |
| first 50 vs last 50 mean | 224.87 vs 224.81 ms |

All 300 rows have `res1 = res2 = 1` (both scalars valid) and `exec_time_ms` equals
`total_cycles / 64000` exactly, confirming the conversion is a host constant. The start
counter reads 4 in every row: the counter is zeroed and then read, and the read itself
costs four cycles.

ECC keygen: from the Aug 10 swapover log's 1640 ECC cycles, mean 111.54 ms, sd 0.09,
range 111.24–111.87. Ratio proxy/ECC = 2.016, which is what two scalar multiplications
against one should give (keygen also draws randomness; the difference is inside the noise).

What this establishes, exactly: the cost of two fixed-base secp256r1 scalar multiplications
in micro-ecc on this device, with no accelerator, at the assumed 64 MHz. What it does not
establish: the cost of any complete verification, the cost of variable-base multiplication
(the same routine in micro-ecc, so probably similar, but not measured), or the behaviour
under interrupt load (the audit reports from July asked for a loaded measurement; none was
done).

Provenance: the file was written on the Windows PC at 18:39 on Aug 11 and committed four
minutes later. Luke recalls also running the profiler on the Pi; no file from that run
survives, and a repeat on the Pi is scheduled.

---

## 19. Loop period and the structure of eviction

File: `data/v7_logs/e2e_composition_results.csv`, 20 rows, one host clock.

### 19.1 The period

At α = 0.5 the trust sequence under attack is 100 → 50 → 25, so the interval from the
first decayed line (50) to the eviction line (25) is one complete loop iteration: workload,
serial print, 10 ms delay, serial read.

| Workload | mean | sd | min | max | n |
|---|---|---|---|---|---|
| ECC | 120.4 ms | 4.8 | 113.2 | 123.7 | 10 |
| proxy | 232.1 ms | 5.4 | 225.7 | 236.4 | 10 |

The sd of about 5 ms is host-side: the script polls the serial port every 10 ms, so each
timestamp carries up to 10 ms of quantization. The device-side period is more stable than
this.

### 19.2 Detection to first decay

| Workload | mean | range |
|---|---|---|
| ECC | 177 ms | 125–228 |
| proxy | 309 ms | 258–443 |

This interval is one full period plus a partial one: the ATTACK arrives at a random point
in the running cycle, waits for that cycle to finish (the partial term, uniform on [0, T]),
and then the next full cycle runs with the attack in effect and emits the first decayed
value. The ranges are consistent with T + U(0, T) plus serial latency.

### 19.3 The eviction structure

Putting the two together, from detection to eviction is a partial cycle plus n(α) full
cycles, so

    T_evict ≈ n(α)·T_cycle + U(0, T_cycle) + t_serial

with mean (n(α) + ½)·T_cycle. At α = 0.5: predicted mean 2.5 × 120.4 = 301 ms for ECC and
2.5 × 232.1 = 580 ms for the proxy; measured 262/333 ms (ECC, probe 100/500) and 533/549
ms (proxy). The measured values sit somewhat below the (n + ½) prediction, which suggests
the effective partial term is a little shorter than a full uniform cycle (the serial read
in the firmware happens right after the delay, so an ATTACK sent during the delay is
picked up sooner). This is a second-order effect and the model is presented as an
approximation.

### 19.4 What the bench block does not show

Its detection column equals one probe timeout because the script probes at the instant it
kills the cloud. Under natural probe phase the detection window would be uniform between
one and two probe intervals. The identity "detection + eviction = total" holds because the
columns are defined that way. And the script's "predicted_total" column is built on an
untraced 247 ms and must be ignored.

---

## 20. Eviction latency on the robot and the outage threshold

Files: `data/v6_logs/trial_*.csv` (120 valid), V7 trial files (75 valid). Per-trial outputs
in `audit/eviction_v6.csv` and `audit/eviction_v7.csv`.

### 20.1 Tables

The Draft 1 tables (Chapter 4 of the thesis) are the reference. Condensed:

**ECC (V6), n = 10 per cell.** Stops (physical): α = 0.1 only at 2000 ms; α = 0.3 at 500
ms and above; α = 0.5 at 250 ms and above. Latencies where eviction occurred: 1572 ms
(α = 0.1), 609–660 ms (α = 0.3), 324–391 ms (α = 0.5), with within-cell ranges of about one
loop period.

**Proxy (V7), n = 5 per cell.** Stops: α = 0.1 at 3000 and 5000; α = 0.3 at 1000 and above;
α = 0.5 at 500 and above. Latencies: 2995–3030 ms (α = 0.1), 1077–1122 ms (α = 0.3),
552–659 ms (α = 0.5).

### 20.2 Against the model

Predicted means (n + ½)·T:

| α | ECC predicted | ECC measured (pooled) | proxy predicted | proxy measured (pooled) |
|---|---|---|---|---|
| 0.1 | 12.5 × 120.4 = 1505 | 1572 | 12.5 × 232.1 = 2901 | 3013 |
| 0.3 | 4.5 × 120.4 = 542 | 629 | 4.5 × 232.1 = 1044 | 1109 |
| 0.5 | 2.5 × 120.4 = 301 | 363 | 2.5 × 232.1 = 580 | 624 |

Measured exceeds predicted by 40–90 ms in every row. Two contributions: the logger samples
at 50 Hz (up to 20 ms late), and the logger drops lines so that in 10–20 % of trials the
recorded crossing is a full cycle late (Chapter 21). A crude correction, adding 0.15 × T to
the prediction, brings every row within about 30 ms. The model has no fitted parameter; the
agreement is in ordering, spacing, and magnitude.

### 20.3 The threshold

The cleanest result in the project. With outage as a real factor, each cell is all-stop or
all-no-stop, and the boundary sits where n(α)·T_cycle predicts:

- ECC, α = 0.5: 2 × 120 = 240 ms. 250 ms stops (10/10), and there is no shorter level.
- ECC, α = 0.3: 4 × 120 = 480 ms. 250 no, 500 yes.
- ECC, α = 0.1: 12 × 120 = 1444 ms. 1000 no, 2000 yes.
- Proxy, α = 0.5: 2 × 232 = 464 ms. 250 no, 500 yes.
- Proxy, α = 0.3: 4 × 232 = 928 ms. 500 no, 1000 yes.
- Proxy, α = 0.1: 12 × 232 = 2785 ms. 1000 no, 3000 yes.

Twenty-seven cells, zero exceptions, once stop is judged by motion. Above the threshold the
latency is independent of outage duration, as it must be: the outage only needs to last
long enough to deliver n(α) attacked cycles.

One subtlety about the ECC 250 ms / α = 0.5 cell. The threshold is 240 ms and the logger
records the attack flag as lasting about 272 ms, so the margin is one-eighth of a cycle.
The device sees ATTACK at cycle boundaries, so whether two attacked cycles occur depends on
where in the cycle the attack starts. All ten trials stopped. Either the margin was enough
in every trial or the 20 Hz ATTACK repeats plus RECOVER timing extend the effective
attack slightly; the data cannot distinguish these, and the thesis should describe this
cell as "at threshold, stopped in all ten" without claiming more.

---

## 21. Physical stop, the stationary-arm finding, and the dropped-line defect

### 21.1 Logged versus physical

Across V5, V6 and V7 (315 valid trials):

- Trials logged as stopped (trust ≤ 30 in the CSV) whose arm nevertheless completed its
  trajectory: **0**.
- Trials whose arm never executed the trajectory but which show no trust ≤ 30 in the CSV:
  **8** (V6: six in the 250 ms / α = 0.5 cell, one in 500 ms / α = 0.3; V7: one in
  1000 ms / α = 0.3).

The eight are all boundary cells, where the crossing happens on the last attacked cycle
and a single missing serial line hides it. So the logged stop count under-reports, never
over-reports. Earlier internal reports treated the 4/10 and 4/5 boundary cells as evidence
of "cycle-boundary jitter deciding marginal cases"; they were instrumentation.

### 21.2 The dropped-line defect, quantified

Because the firmware's under-attack sequence is exactly 100(1−α)^k, the audit can check
which expected values appear. Restricting to the first n(α)+2 decay steps (the tail rounds
to zero and would inflate the count):

| Campaign | mean capture | worst trial | crossing line missed / logged stops |
|---|---|---|---|
| V7 | 0.83–0.86 | 0.50 | 5 / 44 |
| V6 | 0.78–0.81 | 0.50 | 16 / 73 |
| V5 | 0.79–0.92 | 0.50 | 26 / 120 |
| V4 | 0.80–0.91 | 0.50 | (same mechanism) |

Mechanism: the logger's reader flushes the input, sleeps 10 ms, and reads one line
non-blocking; anything that straddles the boundaries is lost. The visible signatures are
skipped steps (50 then 12.5), first-decay values that are impossible (75 at α = 0.5, which
is the first *recovery* step after a dropped 50), and a one-cycle spread in every latency
cell. The bench harness, which accumulates all bytes, has none of these.

### 21.3 The stationary-arm finding

The trajectory's first waypoint is the arm's current pose at t = 1 s, and the attack is
called at t = 0.5 s. Motion starts between 0.5 and 1.0 s after the attack. Evictions faster
than that open the safeguard input before the arm has moved. From the velocity columns:

| Condition | stops | arm moving at eviction |
|---|---|---|
| ECC α = 0.5 (V5, V6) | 54 | 0 |
| ECC α = 0.3 (V5, V6) | 49 | only the V6 2000 ms cell (10), at 0.06 rad/s |
| ECC α = 0.1 | 30 | all, 0.3–0.4 rad/s |
| proxy α = 0.5 (V7) | 20 | 2 of 20, slow |
| proxy α = 0.3 (V7) | 14 | 0 |
| proxy α = 0.1 (V7) | 10 | all, ~0.57 rad/s |
| stub α = 0.5 / 0.3 (V5) | 40 | all |

Therefore: **every stop that landed under 500 ms happened with a stationary arm.** What
those trials show is that the trajectory was never executed, which is a valid observation
of the safety action, but it is not a demonstration of arresting a moving arm inside the
budget. Stops of a moving arm exist only at α = 0.1 and in the withdrawn-stub cells, all
above 1.5 s. The thesis says this in one sentence in the results and again in the
limitations. A future campaign that wants the missing evidence fires the attack two to four
seconds into phase 2.

### 21.4 What is not measured about the stop

The mechanical deceleration phase after the input opens, the safety controller's reaction
time, and the exact moment the input opened (the logged trust crossing is a proxy, up to
one cycle late). The IMU columns exist but were never analysed; an Extended Kalman Filter
mentioned in old outlines was never written.

---

## 22. The failover sweep

File: `data/cloud_failover_sweep_results.csv`, 108 rows, one per configuration.

Usable rows: the 81 at probe intervals 100, 250 and 500 ms. The 27 rows at 1000 ms were
produced before a serial-parsing fix and record detection or recovery as zero in almost all
cases.

Observations (single runs, loopback mock cloud, no robot, no crypto node):

- Detection latency is about 3.1–3.4 probe intervals for clean-drop and degraded patterns
  and up to 6.3 intervals under flapping, and does not depend on K (the state machine
  detects on the first CLOUD_DOWN; K gates only the rejoin).
- Recovery latency is approximately dwell + 1–2 s.
- No excess oscillation in any usable row; one false rejoin in the corrupt block.
- "Unmonitored motion" equals probe interval × number of failed probes before the
  transition; it is an accounting quantity, not motion.

Grade: demo. The sweep can be re-run without the robot (one Arduino plus the script) and
should be, with n ≥ 3 per configuration, before anything from it goes into a results
chapter.

---

## 23. Results that were withdrawn, and the exact reason for each

| Withdrawn statement | Reason | Where it came from |
|---|---|---|
| ZKP costs 334.66 ms | Stub of 3× keygen, calibrated to sit under 400 ms (commit message of Aug 5) | Aug 10 swapover log |
| 22.85 % security tax | Computed from the stub | proposal-era profiling |
| 301–346 ms "64-byte stabilization" and the central-limit-theorem argument | No 64-constraint code exists; the profiler file cited never existed; measured sd is 0.2 ms | never in repo |
| "ZKP is incompatible with industrial safety" as a measured finding | Based on the stub; with the proxy it is a model statement | V4/V5 prose |
| ECC halts in 236–439 ms at α = 0.5/0.7/0.9 | Those α were V4; V5 measured 291–505 ms at 0.5 | `empirical_conclusions.md` (deleted) |
| Outage duration has no effect (H1' null) | Attack latched; factor never delivered | V4 |
| Category 0 / STO / "latching cryptographic halt" | SI0/SI1 is Category 2; C192A4 is a timing fault | multiple |
| Cohen's d = 2.4 proves n = 4 suffices | Observed-power fallacy | `final_lab_plan.md` (deleted) |
| 500 ms is an ISO 13849-1 limit | The standard sets no stop time | multiple |
| 247 ms proxy loop period | Untraced; measured 232 ms | `conclusion2.md`, e2e script constant |
| "Composition confirmed to 0.0 ms" | Arithmetic identity of the columns | `conclusion2.md` |
| 4/5 partial boundary cell; "unexplained 75 first step" | Dropped-line defect | `conclusion2.md` |
| 335 physical trials | Counts 20 Arduino-only bench runs | `conclusion2.md`, `project_truth.md` |
| K ≥ 3 eliminated all false rejoins | Single-run sweep with a corrupt block; one false rejoin total | `project_truth.md` |
| 368 ms URScript mode-switch penalty | No data or script | prose only |
| 99.6 % boot-storm shedding | No measurement | prose only |
| Hold-down suspension as a built mechanism and its "unbounded" defect | Never implemented | `gaps.md` §5 |
| μ = 3.10 packets/s, ρ = 16.14, NS-3 n* | Built on the stub | Phase 3.5/5 docs |
| ≈110 ms mechanical deceleration, EKF | Never analysed | `master.md` (deleted) |

Each was removed from the repository on 2026-09-08 or is retained only in git history and
in `audit/ground_truth_v1_2026-08-11.md`.

---

*End of Part III.*


---

# Part IV — Interpretation

Part III said what was measured. This part says what it means, what it does not mean, and
how to argue it in a room where at least one person will have read the standard, one will
have written a cryptographic library, and one will ask why the sample sizes are small.

---

## 24. The latency model as a design tool

### 24.1 The model, stated once

For a trust monitor with EWMA weight α, eviction threshold θ (here 0.3 of full trust), and
loop period T, with the failure signal arriving at a uniformly random phase of the cycle:

    n(α) = ⌈ ln θ / ln(1 − α) ⌉
    T_evict = n(α)·T + φ·T + t_s,   φ ~ U(0, 1),   t_s ≈ serial latency (ms)

Mean ≈ (n(α) + ½)·T. Minimum ≈ n(α)·T. Maximum ≈ (n(α) + 1)·T. The distribution of T_evict
within a condition is approximately uniform over one period, which is exactly the spread
seen in every cell of V6 and V7.

Adding the detection stage in front (the supervisor noticing the cloud is gone) adds a
term that depends on probe interval P and probe timeout: between P and 2P under natural
phase, one timeout when probing at the instant of failure. Total exposure from network
failure to safety action is then detection + T_evict. The thesis states this as a
composition, not as a measured identity.

### 24.2 Inverting it

Given a budget B on the mean time to safe state and a chosen α, the loop period must
satisfy T ≤ B / (n(α) + ½). Given a period T and a budget B, the admissible α are those
with n(α) ≤ B/T − ½. For B = 500 ms:

| α | n(α) | T for mean ≤ 500 ms | T for worst case ≤ 500 ms |
|---|---|---|---|
| 0.5 | 2 | ≤ 200 ms | ≤ 167 ms |
| 0.3 | 4 | ≤ 111 ms | ≤ 100 ms |
| 0.1 | 12 | ≤ 40 ms | ≤ 38 ms |

The ECC path (120 ms) satisfies the α = 0.5 mean bound and misses the worst-case bound by a
few percent, which is what V6 shows (max 505 ms). The proxy (232 ms) satisfies nothing at
500 ms. That is the "security tax" statement in its defensible form: not a percentage, but
a position on this table.

### 24.3 What the design tool tells an engineer

- α is a free knob with a cost: higher α reacts faster but also reacts to transient
  failures (an α = 0.5 monitor stops the robot on any two consecutive bad cycles).
- The loop period is the expensive knob: it is set by the cryptographic workload and the
  device. Halving the period halves every latency.
- The threshold θ is a third knob the project never varied (fixed at 0.3). Raising it
  toward 1 reduces n(α) toward 1 for any α; the thesis can note this as untested.
- Nothing in the model depends on which algorithm produces the period. That is the
  reframing that survived the audit: the experiment measured how cycle cost drives safety
  latency, not whether ZKP is "compatible" with anything.

---

## 25. What the data say about ZKP on a Cortex-M4, honestly

Measured: two secp256r1 scalar multiplications cost 225 ms on this device without
acceleration, with negligible variance. Inferred, with stated assumptions: a minimal
Schnorr verification would cost at least that plus a hash (SHA-256 of ~100 bytes: well
under a millisecond) plus one point addition (a few hundred microseconds), so roughly
225–230 ms. A selective-disclosure verification with several hidden attributes would cost
several multiples of that.

Not measured: any real verification; variable-base multiplication specifically; behaviour
under interrupt load; the nRF52840's CryptoCell accelerator (which would change the numbers
by an order of magnitude and was deliberately excluded to represent generic hardware).

What can be concluded: on a generic 64 MHz Cortex-M4 with a software curve library, a trust
loop whose every cycle performs even the minimal ZKP-class arithmetic has a period of
about a quarter of a second, and with an EWMA of any reasonable α that places the mean stop
time well beyond half a second. If the cell's safety budget is in that range, the design
must either accelerate the arithmetic (hardware curve unit, faster core), run the
verification less often than every safety cycle (decouple the verification cadence from the
trust-update cadence), or accept a longer time to safe state. Each of those is a design
option the thesis can name; none of them was tested.

What must not be concluded: that ZKPs are "incompatible with industrial safety", that a
specific percentage tax exists, or that anything about zero knowledge was demonstrated.

---

## 26. The safety-budget argument and its limits

The argument as the thesis should make it:

1. 500 ms is a design budget the project chose, representative of collaborative cells but
   not derived from a standard. (State this every time the number appears.)
2. Time to safe state decomposes into detection, trust decay, and mechanical stop.
3. Trust decay was measured on the robot at two loop periods and follows the model.
4. With ECC-class cost and α = 0.5 the decay stage alone fits a 500 ms mean; with
   ZKP-class cost it does not.
5. The mechanical stage was not isolated, and every sub-500 ms stop in the data occurred
   with the arm stationary, so the project cannot claim a moving arm was arrested inside
   the budget.

Point 5 is the one to state before anyone asks. It does not undermine points 3 and 4, which
are about the decay stage; it limits what the physical demonstration shows. The physical
demonstration shows that the trust decision reaches the safety controller and prevents
program execution, 245 times, with zero false stops. That is a real result about the
intercept. It is not a stopping-distance result.

---

## 27. Threats to validity, listed the way a committee will list them

**Construct validity**
- The ZKP path is a cost proxy, not a verification. (Stated; the thesis uses the term
  throughout.)
- The failure signal is the supervisor's ATTACK keyword, not a failed verification. The
  trust monitor never detects anything itself. (Stated in the limits section.)
- "Outage" is a serial keyword flood, not a network condition experienced by the edge node.

**Internal validity**
- Logger drops 10–20 % of telemetry lines; latencies are late by one cycle in that
  fraction of trials; boundary stop counts are under-reported unless motion is used.
  (Quantified; corrected classification used.)
- ECC and proxy campaigns ran on different days with different outage sets and n; any
  contrast is between campaigns. (Stated.)
- Attack precedes motion by 0.5–1.0 s; fast stops are stationary-arm stops. (Stated.)
- Firmware for V7 was committed two minutes before the first trial. Luke confirms the
  flashed source matched the commit; the repository cannot prove it.

**External validity**
- One device, one library, one curve, one robot, one cell. The loop-period numbers are
  device-specific; the model is not.
- The mock cloud is local; detection numbers are harness artifacts.
- n = 5 per cell in V7; n = 10 in V6. Adequate for an all-or-nothing threshold result;
  thin for distributional claims. Report ranges, not confidence intervals, and do not
  compute power from the observed effect.

**Statistical conclusion validity**
- No ANOVA is presented in Draft 1, deliberately. The earlier ANOVA and Cohen's d were on
  latched-attack data and are withdrawn. The V6/V7 result is a deterministic threshold
  with zero exceptions in 27 cells; a hypothesis test would add nothing and would invite
  the observed-power question.

---

## 28. Anticipated committee questions, with answers

**"Did you verify a zero-knowledge proof?"** No. The edge node executes the two scalar
multiplications a Schnorr verification requires, on a static buffer, and I measured their
cost. I call it a ZKP-cost proxy for that reason. The result is a lower bound on what a
minimal verification would cost, and the thesis is explicit that the verification itself
is future work.

**"What stop category is this, and does it remove power?"** Category 2 safeguard stop
through SI0/SI1, driven by one logic pin through an optocoupler pair. Drive power stays on.
The firmware latches the open state until reconfigured. A Category 0 path would need the
emergency-stop inputs or a drive-power relay; neither was built.

**"Where does 500 ms come from?"** It is my design budget, chosen as representative of a
collaborative cell. ISO 13849-1 does not specify a stop time; stop-time requirements come
from the cell's risk assessment and ISO 13855 separation-distance calculations. Everything
in the thesis that compares to 500 ms is a comparison to that budget.

**"Your fastest stops: was the arm moving?"** No. Motion is commanded from half a second
after the attack, and the ECC α = 0.5 evictions land before that. Those trials show the
trajectory was never executed. Moving-arm stops occur only in the slower conditions. This
is stated in the results and limitations, and a mid-trajectory attack is the first thing
I'd run with renewed robot access.

**"How do you know the logger's stop count is wrong and not the robot?"** Because the
firmware's decay sequence is exactly 100(1−α)^k and I can see which values are missing from
the log, and because the joint velocities show the arm never moved in those trials. Zero
trials in 315 show the opposite disagreement.

**"Why no ANOVA?"** Because the result is a deterministic threshold with no exceptions once
the instrument defect is corrected, and the latency above threshold is a quantized
function of two known constants. The earlier ANOVA was on data in which the outage factor
was not delivered, and it was withdrawn.

**"Why are ECC and ZKP in different campaigns?"** Time: the ZKP-cost proxy replaced a stub
on the last morning of robot access. I report the contrast as between-campaign and lean
on the bench block, where both workloads were timed the same way on the same day.

**"What does the trust monitor actually detect?"** Nothing on its own. It reacts to the
supervisor's signal. Its contribution is the timing and the hardware path from a trust
decision to a safety input. Making the edge node independently capable of detecting a
failed verification is the next design step, and the current dependence is a
denial-of-safety exposure: a silenced supervisor leaves trust at 100.

**"Is 64 MHz assumed or measured?"** Assumed for the cycle-to-millisecond conversion, and
corroborated to within four percent by wall-clock loop periods measured on the bench.

**"What happened to the CLT / 64-byte stabilization result?"** It was withdrawn. The
code it described never existed; the workload is constant-time with 0.1 % variation; and
the statistical argument was inverted (a sum's variance grows). The audit that found this
is documented in the repository.

**"What is the contribution, in one sentence?"** A measured, inverted latency model for an
EWMA trust monitor driving a hardware safety input on an industrial arm, validated at two
cryptographic loop periods with a working outage factor, together with an audited
experimental pipeline that found and corrected its own instrumentation defects.

---

*End of Part IV.*


---

# Part V — Where it goes next

---

## 29. Draft 2: the unified time-to-safe-state model

### 29.1 What "unified" should mean

Draft 1 presents the decay stage on its own. Draft 2 should present one expression for the
whole path from the network event to the arm at rest, with every term either measured,
bounded, or explicitly left symbolic:

    T_safe = T_detect + T_decay + T_stop

- **T_detect**: from the moment the cloud becomes unreachable to the moment the
  supervisor asserts ATTACK. Depends on probe interval P, probe timeout τ, and phase:
  under natural phase T_detect ∈ [τ, P + τ]. Measured only in the degenerate case
  (probe at the instant of failure), where it equals τ.
- **T_decay**: from ATTACK to the safety pin going low. Measured. n(α)·T + φ·T + t_s.
- **T_stop**: from the pin going low to the arm at rest. Not isolated in the data.
  Bounded above by the UR5's documented stopping performance at the commanded speed, and
  the thesis can cite the manufacturer's stopping-distance tables as the bound while
  stating that it was not measured here.

### 29.2 Closed form

With φ uniform on [0,1] and T_detect uniform on [τ, P + τ]:

    E[T_safe] = (τ + P/2) + (n(α) + ½)·T + t_s + E[T_stop]
    max T_safe = (P + τ) + (n(α) + 1)·T + t_s + max T_stop

The thesis should present both, because a safety argument is usually made on the maximum.
The V6/V7 data validate the middle term; the bench validates its structure; the first and
last terms are design inputs.

### 29.3 What to do with the logger bias

Draft 2 can either present logged latencies with the +0.15·T correction estimated from the
capture ratio, or present them uncorrected with the one-cycle-late caveat. Uncorrected with
caveat is the more defensible choice; the correction is a model of the instrument, not a
measurement.

---

## 30. Draft 2: the hold-down adversary and the wall-clock watchdog

### 30.1 Two adversaries, one built and one proposed

The project's earlier documents describe a "hold-down" mechanism that suspends trust
decay while the edge node is busy with legitimate cryptographic work, and an adversary who
keeps it busy forever. That mechanism was never built. Draft 2 should analyse it as a
*proposed* design and its failure mode, and should analyse separately the failure mode of
the *built* design:

- **Built system.** Trust falls only when the supervisor says ATTACK. An adversary who
  silences the supervisor, or a supervisor that crashes, freezes trust at 100. The edge
  node never detects this because it verifies nothing that depends on the supervisor.
- **Proposed hold-down.** If decay were suspended during verification work, an adversary
  who floods verification requests keeps decay suspended. Same outcome by a different
  route.

Both are denial-of-safety conditions: the attacker does not defeat the cryptography, only
the timing.

### 30.2 The watchdog

The natural mitigation for both is a wall-clock watchdog on the edge node: if no
well-formed heartbeat (or no completed verification) arrives within W milliseconds, treat
it as a failed observation and let trust decay. Predicted stop latency then becomes
W + T_decay; choosing W trades false stops under legitimate load against exposure under
attack. This can be analysed on paper with the measured T and simulated with any loop
model; it needs no robot. A bench confirmation (heartbeat withheld, pin observed) needs one
Arduino.

### 30.3 What the simulation should use

Cycle times 120.4 and 232.1 ms, not 125 and 247. α ∈ {0.1, 0.3, 0.5}. Threshold 30. Attack
phase uniform. Report predicted T_decay distributions and compare to the V6/V7 cells as a
check that the simulator reproduces the measured data before it is used for anything new.

---

## 31. Bench work still possible without the UR5

In priority order:

1. **Proxy profile on the Pi.** Flash `zkp_real_profiler.ino`; run `run_real_zkp_test.py`
   with the Pi port. Confirms the committed profile from a second host. Ten minutes.
2. **Failover sweep re-run.** Flash `sentry_node.ino`; run `run_cloud_failover_sweep.py`
   (current script, writes the `_v3` file); n ≥ 3 per configuration. Replaces the
   partly corrupt file. About two hours of unattended run time.
3. **Loop period under serial load.** Bench block with the joint logger's 20 Hz ATTACK
   flood active, to see whether serial interrupts move the 232 ms period. Addresses the
   July audit's "measure under load" request.
4. **Watchdog prototype.** Add the heartbeat timeout to a copy of the firmware; measure
   time from withheld heartbeat to pin low on the bench. Supports Chapter 30.
5. **Variable-base multiplication cost.** One more profiler variant calling the point
   multiplication with a non-generator base, to close the fixed-base caveat.
6. **Lossless logger.** Fix the serial reader (accumulate bytes, split on newline) in a
   copy of the logger, verify against the bench, and keep it ready for any future robot
   session. Do not touch the file that produced the archived data.

Anything requiring the arm (mid-trajectory attack, deceleration isolation, Category 0 path)
waits for renewed access and is future work in the thesis.

---

## 32. Glossary

- **α (alpha)**: EWMA weight on the newest observation. Higher reacts faster.
- **ATTACK / RECOVER**: serial keywords from supervisor to edge node that set and clear
  the attack condition.
- **Category 0 / 1 / 2 stop**: power removed immediately / controlled stop then power
  removed / controlled stop with power retained. The project's stop is Category 2.
- **C192A4**: UR safety fault code for safeguard-input channel disagreement.
- **DIL**: disconnected, intermittent, limited (network conditions).
- **DWT_CYCCNT**: Cortex-M cycle counter used to time workloads.
- **EWMA**: exponentially weighted moving average.
- **Eviction**: trust score falling below 30, which opens the safeguard input.
- **Loop period, T_cycle**: wall-clock time per firmware iteration: 120.4 ms (ECC),
  232.1 ms (proxy).
- **micro-ecc / uECC**: the C elliptic-curve library used on the edge node.
- **n(α)**: attacked cycles needed to evict: 12, 4, 2 for α = 0.1, 0.3, 0.5.
- **Physical stop**: the arm did not execute its commanded trajectory (motion criterion).
- **Proxy, ZKP-cost proxy**: two secp256r1 scalar multiplications standing in for the
  arithmetic of a Schnorr verification.
- **RTDE**: UR's real-time data exchange interface used by the ROS driver.
- **secp256r1 / P-256**: the elliptic curve used throughout.
- **Sentry node**: the second Arduino running the cloud-viability state machine.
- **SI0 / SI1**: UR5 safeguard-stop input pair.
- **Supervisor**: the Raspberry Pi 4 running ROS 2 and the orchestration.
- **Trust monitor**: the edge Arduino running the workload and the EWMA.
- **V5 / V6 / V7**: the three robot campaigns used in the thesis.

---

## 33. File and data index

Repository `On-Edge` after the 2026-09-08 cleanup.

**Top level**
- `ground_truth_v2.md` — authoritative claims ledger.
- `todoist.md` — task list.
- `README.md` — layout and reproduction commands.

**firmware/**
- `unified_trust_monitor_template/` — trust monitor (canonical).
- `zkp_real_profiler/` — proxy cost profiler.
- `sentry_node/` — cloud-viability state machine.

**scripts/**
- `run_test.sh` — one robot trial. `run_campaign.py` — randomized campaign.
- `run_real_zkp_test.py` — profiler host. `run_end_to_end_campaign.py` — bench block.
- `run_cloud_failover_sweep.py` — sentry sweep.
- `combine_v6_sub_eviction.py`, `combine_v7_logs.py` — CSV concatenation
  (the V7 one still globs the old location).
- `setup_ur5_ros2.sh` — Pi setup.

**src/sentry_logic/** — ROS 2 package: `joint_logger_node.py`,
`stream_wrist_kinematics.py`, `supervisor_node.py`, `c_src/` (Pi-side verify wrapper).

**data/**
- `real_zkp_profiling.csv` — 300 proxy runs.
- `cloud_failover_sweep_results.csv` — 108 sweep rows (27 corrupt).
- `sub_eviction_summary.csv` — V7 per-trial logged summary.
- `v5_spoofing_archive/` — V5 (latched attack), 138 files.
- `v6_logs/` — V6, 127 trial files + summary + combined.
- `v7_logs/` — V7, 82 trial files + `e2e_composition_results.csv` + combined.
- `archive_pre_v5/` — V1–V4, Aug-10 swapover log, July baseline PNG.

**audit/**
- Scripts: `inventory_data.py`, `inventory_trials.py`, `eviction_latency.py`,
  `telemetry_capture.py`, `physical_stop_crosstab.py`, `decel_after_eviction.py`,
  `zkp_profile_stats.py`, `make_thesis_figures.py`.
- Outputs: `data_inventory.csv`, `trial_inventory.csv`, `eviction_v{4,5,6,7}.csv`.
- Notes: `phase1_inventory.md`, `phase2_zkp.md`, `phase3_4_reverify.md`.
- History: `ground_truth_v1_2026-08-11.md`, `decontamination_report_2026-08-14.md`.

**docs/**
- `project_summary_review.md` — this document.
- `enhanced_earc_literature_review.md` — literature review material.
- `gaps.md` — open gaps (§5 hold-down to be rewritten as proposed, not built).
- `original_thesis_proposal.md` — historical baseline.

**Thesis repository** (`URI-ISE/Thesis/draft 9-9/`): `thesis.tex`, `chapter1–6.tex`,
`abstract.tex`, `figures/` (four data figures plus `system_flow.mmd`/`.pdf`),
`urithesis.cls`, `references.bib`.

---

*End of Part V.*

