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
