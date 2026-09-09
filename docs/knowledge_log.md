# Knowledge log

One entry per drill session. Weak points become the next session's first item.

## 2026-09-08 — session 1 (rounds 1–2, 10 questions)

Score: round 1 ≈ 2.5/5, round 2 ≈ 3/5.

Solid:
- Attack acts at the next cycle boundary; spread ≈ one loop period.
- Category 2 stop, power retained, monitored standstill; latched until reconfiguration.
- Why the ECC 250 ms / α=0.5 cell stops (2 × 120 = 240 < 250).
- 500 ms is a self-imposed design budget; ISO 13849-1 sets no stop time.
- EWMA convention corrected in round 2: α weights the new observation; α=0.1 → 90, 81, 72.9, 65.6.

Weak (first items next session):
1. **Eviction threshold is 30, not 25.** α=0.1 → 12 cycles (0.9^11 = 31.4 above, 0.9^12 = 28.2 below), not 14.
2. **What the proxy computes vs a Schnorr verify.** Must be able to say: two scalar multiplications k·G on a
   static 64-byte buffer; a Schnorr verify sG = R + cP adds a hash (c), a point addition (R + cP), a comparison,
   and consumes a proof (s, R) from a prover. Proxy has none of those four → lower bound.
3. **Threshold rule direction.** Stop iff outage ≥ n(α)·T. 1000 ms at 232 ms = 4 full cycles; α=0.3 needs 4 → stops
   (928 ≤ 1000). 500 ms gives 2 cycles → no stop.
4. **The supervisor-signal gap as an attack.** Trust falls only on ATTACK. Silence/compromise the supervisor →
   trust stays 100 → arm never stops (denial of safety). A config message resets trust and re-closes the loop.
5. **Where stop-time requirements come from.** Cell risk assessment + ISO 13855 separation distance and the
   machine's measured stopping performance; not from 13849-1. Do not claim "similar test beds aim for 500 ms"
   without a citation.
6. Vocabulary slips to retire: "stub" for the current ZKP path (the stub is the withdrawn 3×keygen), "A0/A1"
   (inputs are SI0/SI1), "reversal key" (no such thing).
