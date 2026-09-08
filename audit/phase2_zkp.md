# Phase 2 — ZKP status (audit working notes)

Scripts: `audit/zkp_profile_stats.py`, `audit/eviction_latency.py`, `audit/telemetry_capture.py`.
Outputs: `audit/eviction_v7.csv`, `audit/eviction_v6.csv`, `audit/eviction_v5.csv`, `audit/eviction_v4.csv`.

## 2.1 What was executed

Two distinct pieces of firmware carry the "real ZKP" workload. Neither verifies a proof.

**(a) Standalone profiler** — `firmware/zkp_real_profiler/zkp_real_profiler.ino` (added 01a0971, 2026-08-11):

```cpp
// lines 9-13
// 64-byte payload maps to 2 independent 32-byte scalars.
// A full Schnorr verification requires two scalar multiplications (sG and cP).
// We proxy this by running uECC_compute_public_key twice.
// This measures scalar-multiplication cost as a lower bound on Schnorr verification,
// not a full verify (no hashing, no point addition).
...
// lines 54-67
ARM_DWT_CYCCNT = 0;
uint32_t start = ARM_DWT_CYCCNT;
int res1 = uECC_compute_public_key(&attributes[0], public_key);
int res2 = uECC_compute_public_key(&attributes[32], public_key);
uint32_t end = ARM_DWT_CYCCNT;
```

Host supplies 64 fresh `os.urandom` bytes per run (`run_real_zkp_test.py` line 44); the device
computes two fixed-base scalar multiplications k·G with k = each 32-byte half. Runs where either
half is not a valid private scalar (`res==0`) are dropped host-side (lines 61-64). Timing is the
DWT cycle counter, converted at `CYCLES_PER_MS = 64000.0` (line 14) on the host; the CSV stores raw
cycles, so the ms column is a host constant, not a device measurement.

**(b) Control-loop firmware** — `unified_trust_monitor_template.ino` ZKP block, lines 162-176 (since
6db79e0, 2026-08-12 11:46 EDT):

```cpp
// Real ZKP proxy: two secp256r1 scalar multiplications over a static nonzero payload.
static uint8_t attributes[64];
... RNG(attributes, 64) once ...
acc += uECC_compute_public_key(&attributes[0],  public_key);
acc += uECC_compute_public_key(&attributes[32], public_key);
```

Same primitive, same count, but on a **static** payload generated once at first call. The cost is
therefore identical to (a) but nothing varies per cycle; no data from the Pi is ever verified. The
block still emits `exec_time_ms`, but `joint_logger_node.py` does not log it (CSV columns, lines
128-135), so no per-cycle timing exists for the robot campaigns.

Note on what the proxy omits relative to a Schnorr verify (`sG == R + cP`): the hash `c = H(R‖P‖m)`,
one point addition, the point comparison, and any deserialisation. Both multiplications in the proxy
are fixed-base (G); the real `cP` is variable-base. In micro-ecc both go through the same
`EccPoint_mult` routine, so the cost difference is small, but this is an assumption, not a measurement.

## 2.2 Profile result (`data/real_zkp_profiling.csv`)

| n | mean | sd | min | median | p95 | max | CV | Shapiro-Wilk |
|---|---|---|---|---|---|---|---|---|
| 300 | 224.864 ms | 0.209 ms | 224.083 | 224.867 | 225.183 | 225.391 | 0.093 % | W=0.995, p=0.44 (normality not rejected) |

Raw cycles: mean 14,391,308 (min 14,341,336, max 14,424,999). `exec_time_ms == total_cycles/64000` in
all 300 rows; `res1==res2==1` in all rows; no drift (first-50 mean 224.87, last-50 224.81).

Provenance: script `PORT='COM32'` (Windows); file mtime 2026-08-11 18:39:10 EDT on this machine,
script mtime 18:37:45, commit 18:43:41. The committed profile was produced from the Windows PC.
Luke reports profiling was also run on the Pi; **no Pi profile file exists in the repo.**

Clock assumption cross-check: the end-to-end block measured one full ZKP-mode loop iteration
(trust 50→25 interval, host wall-clock) at 232.1 ms mean (sd 5.4, 225.7–236.4, n=10) and one
ECC-mode iteration at 120.4 ms (sd 4.8, n=10). Firmware adds `delay(10)` plus a ~60-byte serial
print per iteration. 224.9 + 10 + ~5 (serial at 115200) ≈ 240 vs 232 observed; 111.5 + 10 + 5 ≈
126.5 vs 120.4 observed. Both within ~4 %, so the 64 MHz DWT conversion is corroborated by
wall-clock to a few percent; it is not off by a large factor.

## 2.3 Was the measured cost carried into the eviction campaign?

Yes, but as a **new campaign**, not a re-run of the 120-trial V5 matrix:

| Campaign | Trials | Algo | Outage set | α | Firmware ZKP block |
|---|---|---|---|---|---|
| V5 (2026-08-07) | 120 | ECC + ZKP | 500/1000/2000/5000 | .1/.3/.5 | 3×`uECC_make_key` stub, attack latched |
| V6 (2026-08-11) | 120 | ECC only | 250/500/1000/2000 (n=10) | .1/.3/.5 | n/a (RECOVER present) |
| V7 core (2026-08-12) | 75 | ZKP-proxy only | 250/500/1000/3000/5000 (n=5) | .1/.3/.5 | 2×`compute_public_key` |
| V7 e2e (2026-08-12) | 20 | ECC + ZKP-proxy | probe 100/500, jam 10 s | .5 | same; **no robot** |

So the ECC/ZKP-proxy comparison at the real cost is *between* campaigns (different days, outage
sets, and n), never within one randomized queue. Any algorithm contrast at the real cost must be
labelled as such.

## 2.4 Recomputed V7 eviction latency (logger clock, first `trust<=30` − first `attack_active==1`)

Pooled over outage levels where eviction occurred:

| α | n trials | stops | pred cycles | evict mean | sd | min | max | first-decay mean (range) |
|---|---|---|---|---|---|---|---|---|
| 0.1 | 25 | 10 | 12 | 3012.6 | 138.1 | 2846.4 | 3263.4 | 421 (266–615) |
| 0.3 | 25 | 14 | 4 | 1108.5 | 72.7 | 978.3 | 1250.1 | 430 (279–659) |
| 0.5 | 25 | 20 | 2 | 623.5 | 80.4 | 515.4 | 787.0 | 403 (275–702) |

Per-cell stop counts (n=5 each): outage 250 → 0/0/0; 500 → 0/0/**5**; 1000 → 0/**4**/5;
3000 → 5/5/5; 5000 → 5/5/5 (α = .1/.3/.5). This matches the quantized prediction
n(α)·T_cycle with T_cycle≈232 ms: α=.5 needs ≥464 ms, α=.3 needs ≥928 ms, α=.1 needs ≥2784 ms.

`audit/conclusion2.md` states means 659 / 1122 / 3030 ms. Recomputed pooled means are 623.5 /
1108.5 / 3012.6 ms; the 1122 and 3030 figures reproduce if only the fully-stopping cells above the
boundary are pooled (α=.3: 3000+5000 → 1121.2; α=.1: 5000 only → 3030.1). **659 for α=0.5 does not
reproduce** from any subset (500→653.9, 1000→551.6, 3000→629.6, 5000→658.8; the 5000 cell alone
gives 658.8). Treat conclusion2's 659 as "the 5000 ms cell", not the α=0.5 mean.

The **247 ms cycle time** in conclusion2 and hard-coded in `run_end_to_end_campaign.py` line 177 is
**UNTRACED**: no file in the repo measures it. Measured loop period is 232 ms (e2e, lossless
serial) and ~300±60 ms from logger step intervals (contaminated by dropped lines, see 2.6).
The e2e script's own "predicted_total" therefore over-predicts every trial (residuals −165 to −617 ms).

## 2.5 End-to-end composition block (`data/v7_logs/e2e_composition_results.csv`, n=20)

Arduino + a localhost dummy cloud on the Pi; **no UR5, no joint logger**. Single host clock.
`detection + eviction == total` holds to 0.01 ms in all 20 rows — but this is an arithmetic identity
of how the three columns are computed from the same four timestamps (script lines 173-175), not an
empirical finding.

| probe | algo | detection mean (sd) | eviction after detection mean (sd, min–max) | total mean (min–max) |
|---|---|---|---|---|
| 100 | ECC | 108.3 (0.8) | 262.3 (21.5, 248–300) | 370.6 (356–409) |
| 100 | ZKP-proxy | 108.2 (0.4) | 532.7 (76.0, 494–668) | 640.9 (602–777) |
| 500 | ECC | 508.5 (0.7) | 332.5 (24.7, 289–351) | 841.0 (798–859) |
| 500 | ZKP-proxy | 507.6 (0.6) | 549.4 (31.3, 494–566) | 1057.0 (1001–1074) |

Detection ≈ one probe timeout because the script probes immediately at jam onset (line 130), so the
detection window is a lower bound, not a distribution. Structure of eviction after detection:
detection→first decay = 309 ms (ZKP, 258–443) and 177 ms (ECC, 125–228) = partial cycle + one full
cycle; first decay→eviction = exactly one cycle (232.1 / 120.4 ms). Hence T_evict ≈ n(α)·T_cycle +
U(0, T_cycle) + serial, i.e. mean ≈ (n+½)·T_cycle.

## 2.6 New instrumentation defect: the joint logger drops firmware lines

`joint_logger_node.serial_read_loop()` (lines 148-161) does `reset_input_buffer()`, sleeps 10 ms,
then a non-blocking `readline()`; any line not wholly inside that window is discarded (partial
lines fail the `{…}` check). Under attack the expected trust sequence is exactly 100·(1−α)^k, so
dropped lines are detectable:

| Campaign | capture of first n(α)+2 decay steps (mean, min) | eviction crossing line missed |
|---|---|---|
| V7 (ZKP-proxy) | 0.83–0.86, min 0.50 | 5 of 44 stops |
| V6 (ECC) | 0.78–0.81, min 0.50 | 16 of 73 stops |
| V5 | 0.79–0.92, min 0.50 | 26 of 120 stops |
| V4 | 0.80–0.91, min 0.50 | (same mechanism) |

Consequences: (i) logger-derived eviction latencies are biased late by one cycle in ~10–20 % of
trials (visible as the ~1-cycle spread in every cell, e.g. V7 α=.5 range 515–787 ms); (ii) the
"unexplained 75 vs 50 first decay step" in conclusion2 is this defect — in
`trial_ZKP_outage250_ewma5_iter5_1786554448.csv` the 50 line was dropped and the first logged value
is the recovery step 0.5·100 + 0.5·50 = 75; (iii) `min_trust` for non-stopping trials is
unreliable by one step. The e2e block does not have this defect (it accumulates all bytes).

## 2.7 What can be claimed

Defensible:
- "Two secp256r1 fixed-base scalar multiplications (micro-ecc `uECC_compute_public_key`) cost
  224.86 ± 0.21 ms (n=300, DWT cycle count at an assumed 64 MHz, wall-clock-corroborated) on a
  Nano 33 BLE Cortex-M4, no hardware acceleration." File: `data/real_zkp_profiling.csv`.
- "This is a lower bound on the arithmetic of a Schnorr verification; hashing, point addition and
  the comparison were not executed."
- "A workload of that cost ran inside the trust-monitor loop on the robot during 75 physical
  trials (V7) and the eviction latency followed n(α)·T_cycle quantization." Files: `data/trial_ZKP_outage*.csv`, `audit/eviction_v7.csv`.
- "Measured loop period with that workload: 232 ms (e2e, n=10)."

Not defensible:
- "A ZKP was verified" / "Schnorr verification ran in the control loop" — nothing is verified; the
  payload in the control loop is static and generated on-device.
- "ZKP verification costs 247 ms per cycle" — untraced constant.
- Any per-cycle timing distribution for the robot campaigns — not logged.
- "Total exposure = detection + eviction was confirmed empirically" — identity by construction.
- Anything from `distributed_swapover_log_20260810_150831.csv` labelled ZKP (334.66 ms = stub; the
  `algorithm` column there is inferred from `exec_time_ms > 200`, script line 153).

## 2.8 Open questions for Luke (Phase 2)

1. Was the Pi-side profiling run saved anywhere (file, screenshot, terminal log)? Only the Windows
   run is in the repo.
2. Where did 247 ms come from? If it was read off a serial monitor before the campaign, say so; it
   cannot be used as a measured value in the thesis, and the e2e "predicted" column should be
   recomputed with 232 ms (or, better, dropped).
3. Do you want the thesis to call the workload "scalar-multiplication proxy" or "ZKP-cost proxy"?
   I will use the former unless told otherwise.
