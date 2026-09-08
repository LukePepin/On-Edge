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
