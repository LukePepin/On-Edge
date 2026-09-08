#!/usr/bin/env python3
"""Phase 2: statistics for data/real_zkp_profiling.csv.

Recomputes n, mean, sd (population and sample), min, max, p95, median of
exec_time_ms, checks that exec_time_ms == total_cycles/64000, checks res1/res2,
and runs Shapiro-Wilk.  Also prints what the mean would be under alternative
clock assumptions, because the CSV stores raw cycles and the ms conversion is a
host-side constant (scripts/run_real_zkp_test.py line 14).  Read-only.
"""
import csv, math, os, statistics as st
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
P = os.path.join(ROOT, "data", "real_zkp_profiling.csv")

rows = list(csv.DictReader(open(P, newline="")))
cyc = [int(r["total_cycles"]) for r in rows]
ms = [float(r["exec_time_ms"]) for r in rows]
bad_conv = sum(1 for r in rows if abs(int(r["total_cycles"]) / 64000.0 - float(r["exec_time_ms"])) > 1e-6)
bad_res = sum(1 for r in rows if r["res1"] != "1" or r["res2"] != "1")
starts = {r["start_cycles"] for r in rows}

n = len(ms)
mean = st.mean(ms); sd_s = st.stdev(ms); sd_p = st.pstdev(ms)
srt = sorted(ms)
p95 = srt[math.ceil(0.95 * n) - 1]
print(f"file: data/real_zkp_profiling.csv  n={n}")
print(f"start_cycles values: {starts}  (DWT reset to 0 then read; constant offset)")
print(f"rows where exec_time_ms != total_cycles/64000: {bad_conv}")
print(f"rows with res1/res2 != 1: {bad_res}")
print(f"cycles: mean={st.mean(cyc):.0f} min={min(cyc)} max={max(cyc)}")
print(f"exec_time_ms @64 MHz: mean={mean:.3f} sd(sample)={sd_s:.3f} sd(pop)={sd_p:.3f} "
      f"min={min(ms):.3f} median={st.median(ms):.3f} p95={p95:.3f} max={max(ms):.3f}")
print(f"CV = {sd_s/mean*100:.3f}%")
for f_mhz in (64.0,):
    print(f"  (if core clock were {f_mhz} MHz: mean = {st.mean(cyc)/(f_mhz*1000):.2f} ms)")
try:
    from scipy import stats
    W, p = stats.shapiro(ms)
    print(f"Shapiro-Wilk: W={W:.4f} p={p:.3e} -> {'normal not rejected' if p > 0.05 else 'NOT normal'}")
except ImportError:
    print("scipy not available; Shapiro-Wilk skipped")
# per-run ordering: any drift?
first50 = st.mean(ms[:50]); last50 = st.mean(ms[-50:])
print(f"drift check: mean first 50 = {first50:.3f}, last 50 = {last50:.3f}")
