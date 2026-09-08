#!/usr/bin/env python3
"""Phase 3: cross-tabulate the LOGGED stop (trust<=30 in CSV) against the PHYSICAL stop.

Trajectory context (stream_wrist_kinematics.py lines 192-210): phase-2 goal = Pick@1s,
Transfer@3s, Place@5s, Transfer@7s, Pick@10s; the attack service is called 0.5 s after the
goal is sent.  So, relative to t_attack, motion is commanded from about +0.5 s to +9.5 s.
A trial in which the arm is at standstill for the whole of [+2 s, +9 s] cannot have executed
the trajectory: the safeguard input must have opened (physical stop), whatever the CSV says
about trust.  A trial that moves and then reaches standstill before +8.5 s and stays there
also stopped physically.  A trial that is still moving at +9 s did not stop.

physical_stop  = standstill (max|v| < 0.02 rad/s) sustained from some t_s <= t_attack+8.5 s
                 through t_attack+9.5 s
logged_stop    = first trust<=30 after attack exists in the CSV
Prints per (algo,outage,alpha): n, logged stops, physical stops, disagreements, and the
physical-stop latency (t_s - t_attack) for trials that were moving at eviction.  Read-only.
"""
import csv, glob, os, re, sys, statistics as st
from collections import defaultdict
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME_RE = re.compile(r"trial_(?P<algo>[A-Z]+)_(?:outage|loss)(?P<level>\d+)_ewma(?P<ewma>\d+)_iter(?P<iter>\d+)_(?P<epoch>\d{10})\.csv$")
V_STILL = 0.02

def analyse(p):
    rows = []
    for x in csv.reader(open(p, newline="", encoding="utf-8", errors="replace")):
        if not x or x[0] == "timestamp_sec": continue
        try: rows.append((int(x[0]) + int(x[1]) / 1e9, float(x[2]), int(x[-1]), max(abs(float(v)) for v in x[9:15])))
        except ValueError: pass
    if len(rows) < 50 or not any(r[2] for r in rows): return None
    ta = next(t for t, _, a, _ in rows if a == 1)
    te = next((t for t, tr, _, _ in rows if t >= ta and tr <= 30.0), None)
    win = [(t, v) for t, _, _, v in rows if ta <= t <= ta + 9.5]
    if not win or win[-1][0] < ta + 9.0: return None  # trial too short to judge
    # standstill onset: last time velocity exceeded V_STILL, +1 sample
    moving_times = [t for t, v in win if v >= V_STILL]
    if not moving_times:
        t_s = ta  # never moved
    else:
        t_s = moving_times[-1]
    physical_stop = t_s <= ta + 8.5
    ever_moved = bool(moving_times)
    return dict(logged=te is not None, physical=physical_stop, ever_moved=ever_moved,
                phys_latency_ms=(t_s - ta) * 1000 if physical_stop and ever_moved else None,
                logged_latency_ms=(te - ta) * 1000 if te else None)

def main():
    pat, label = sys.argv[1], sys.argv[2]
    files = glob.glob(os.path.join(ROOT, pat, "trial_*.csv")) if os.path.isdir(os.path.join(ROOT, pat)) else glob.glob(os.path.join(ROOT, pat))
    g = defaultdict(list)
    for p in sorted(files):
        m = NAME_RE.search(os.path.basename(p))
        if not m or m["iter"] == "99": continue
        a = analyse(p)
        if a: g[(m["algo"], int(m["level"]), int(m["ewma"]) / 10)].append(a)
    print(f"=== {label} ===")
    print(f"{'algo':5s} {'out':>5s} {'alpha':>5s} {'n':>3s} {'logged':>6s} {'phys':>5s} {'log&!phys':>9s} {'phys&!log':>9s} {'never_moved':>11s} | phys-stop latency for moving trials: n mean min max")
    tot = defaultdict(int)
    for k in sorted(g):
        v = g[k]; L = sum(r["logged"] for r in v); P = sum(r["physical"] for r in v)
        a = sum(r["logged"] and not r["physical"] for r in v); b = sum(r["physical"] and not r["logged"] for r in v)
        nm = sum(not r["ever_moved"] for r in v)
        lat = [r["phys_latency_ms"] for r in v if r["phys_latency_ms"] is not None]
        tot["n"] += len(v); tot["L"] += L; tot["P"] += P; tot["a"] += a; tot["b"] += b
        print(f"{k[0]:5s} {k[1]:5d} {k[2]:5.1f} {len(v):3d} {L:6d} {P:5d} {a:9d} {b:9d} {nm:11d} | "
              + (f"{len(lat)} {st.mean(lat):6.0f} {min(lat):6.0f} {max(lat):6.0f}" if lat else "-"))
    print(f"TOTAL n={tot['n']} logged={tot['L']} physical={tot['P']} logged-but-not-physical={tot['a']} physical-but-not-logged={tot['b']}")

if __name__ == "__main__": main()
