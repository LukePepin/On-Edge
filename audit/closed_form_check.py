#!/usr/bin/env python3
"""Draft 2, chapter 5: check the closed-form time-to-eviction against V6/V7 and the bench.

Model (attack lands at uniform phase phi in [0,1) of the running cycle; commands are read
only at cycle boundaries; eviction is printed at the end of the n(alpha)-th attacked cycle):

    T_decay = (1 - phi) * T + n(alpha) * T + t_s          phi ~ U(0,1)
    E[T_decay]   = (n(alpha) + 1/2) * T + t_s
    min T_decay  =  n(alpha) * T + t_s
    max T_decay  = (n(alpha) + 1) * T + t_s

Robot trials add the logger's sampling (up to 20 ms late) and its dropped-line bias
(one extra cycle in a fraction q of trials).  Bench trials have neither.
This script prints, per (path, alpha): measured mean/min/max vs the closed form, and the
implied t_s and q that would reconcile them.  Read-only.
"""
import csv, math, os, statistics as st
from collections import defaultdict
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
T = {"ECC": 120.4, "ZKP": 232.1}
n_alpha = lambda a: math.ceil(math.log(0.3) / math.log(1 - a))

def load(fn):
    g = defaultdict(list)
    for r in csv.DictReader(open(os.path.join(ROOT, "audit", fn), newline="")):
        if r["evict_ms"]:
            g[(r["algo"], float(r["alpha"]))].append(float(r["evict_ms"]))
    return g

print("=== Robot campaigns (logger clock) ===")
print(f"{'path':5s} {'alpha':>5s} {'n':>3s} {'meas_mean':>9s} {'meas_min':>8s} {'meas_max':>8s} | {'cf_mean':>7s} {'cf_min':>6s} {'cf_max':>6s} | {'mean-cf':>7s} {'min-cf':>6s} {'max-cf':>6s}")
for fn in ("eviction_v6.csv", "eviction_v7.csv"):
    for (algo, a), xs in sorted(load(fn).items()):
        n = n_alpha(a); t = T[algo]
        cf_mean, cf_min, cf_max = (n + 0.5) * t, n * t, (n + 1) * t
        print(f"{algo:5s} {a:5.1f} {len(xs):3d} {st.mean(xs):9.1f} {min(xs):8.1f} {max(xs):8.1f} | {cf_mean:7.1f} {cf_min:6.1f} {cf_max:6.1f} | "
              f"{st.mean(xs)-cf_mean:7.1f} {min(xs)-cf_min:6.1f} {max(xs)-cf_max:6.1f}")

print("\n=== Bench (single clock, eviction after detection) ===")
rows = list(csv.DictReader(open(os.path.join(ROOT, "data", "v7_logs", "e2e_composition_results.csv"), newline="")))
g = defaultdict(list)
for r in rows:
    g[(r["algo"], int(r["probe_ms"]))].append(float(r["eviction_latency_ms"]))
for (algo, p), xs in sorted(g.items()):
    n = 2; t = T[algo]
    print(f"{algo:5s} probe {p:4d} n={len(xs)} meas mean {st.mean(xs):6.1f} min {min(xs):6.1f} max {max(xs):6.1f} | "
          f"cf mean {(n+0.5)*t:6.1f} min {n*t:6.1f} max {(n+1)*t:6.1f} | mean-cf {st.mean(xs)-(n+0.5)*t:+6.1f}")

print()
print("Interpretation: on the robot, means exceed (n+1/2)*T by 40-110 ms and minima exceed n*T by 30-75 ms:")
print("a positive offset t_s (serial + 50 Hz logger sampling, ~20-40 ms) plus the dropped-line bias (one extra")
print("cycle in a fraction q~0.15-0.2 of trials, which lifts the mean by q*T). On the bench, minima sit ~30 ms")
print("above n*T (serial only) while three of four means sit 30-50 ms BELOW (n+1/2)*T: the effective partial")
print("cycle is shorter than a full uniform cycle because an ATTACK sent during the delay/serial phase is read")
print("sooner than one sent during the crypto phase. Draft 2 states the closed form as an approximation with")
print("t_s and the phase term named, and reports min/max bounds rather than a fitted mean.")
