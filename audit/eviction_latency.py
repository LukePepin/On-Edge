#!/usr/bin/env python3
"""Phases 2/3: recompute eviction latency and firmware loop period from trial CSVs.

Usage: python audit/eviction_latency.py <dir-or-glob> [label]

For every trial_*.csv matching, using the run_campaign validity rule (>=50 rows,
attack fired):
  t_attack   = first logger timestamp where attack_active == 1
  t_evict    = first timestamp (>= t_attack) where trust_score <= 30.0
  t_decay1   = first timestamp (>= t_attack) where trust_score < 100.0
  eviction latency = t_evict - t_attack  (ms)   [same definition as ground_truth §3]
  first-decay latency = t_decay1 - t_attack (ms)
  step sequence = distinct successive trust values from first decay to eviction/end
  loop period  = mean interval between successive distinct trust-value changes
                 while trust is decaying (>=2 changes), per trial
Aggregates by (algo, outage, alpha).  Writes audit/eviction_<label>.csv.
Timestamps come from the logger's 50 Hz PC clock (20 ms quantisation).
Read-only with respect to data/.
"""
import csv, glob, math, os, re, sys, statistics as st
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME_RE = re.compile(r"trial_(?P<algo>[A-Z]+)_(?:outage|loss)(?P<level>\d+)_ewma(?P<ewma>\d+)_iter(?P<iter>\d+)_(?P<epoch>\d{10})\.csv$")


def analyse(path):
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        r = csv.reader(f); hdr = next(r)
        ti, ai = hdr.index("trust_score"), hdr.index("attack_active")
        si, ni = hdr.index("timestamp_sec"), hdr.index("timestamp_nanosec")
        rows = []
        for row in r:
            if not row: continue
            try:
                rows.append((int(row[si]) + int(row[ni]) / 1e9, float(row[ti]), int(row[ai])))
            except ValueError:
                continue
    if len(rows) < 50: return None
    t_attack = next((t for t, _, a in rows if a == 1), None)
    if t_attack is None: return None
    post = [(t, tr) for t, tr, _ in rows if t >= t_attack]
    t_decay1 = next((t for t, tr in post if tr < 100.0), None)
    t_evict = next((t for t, tr in post if tr <= 30.0), None)
    min_trust = min(tr for _, tr in post)
    # distinct step sequence + intervals
    steps, times = [], []
    last = None
    for t, tr in post:
        if last is None or tr != last:
            steps.append(tr); times.append(t); last = tr
    # keep only the decaying prefix (monotone non-increasing after first change)
    dec_steps, dec_times = [steps[0]], [times[0]]
    for s, t in zip(steps[1:], times[1:]):
        if s < dec_steps[-1]:
            dec_steps.append(s); dec_times.append(t)
        else:
            break
    intervals = [b - a for a, b in zip(dec_times[1:-1], dec_times[2:])]  # exclude first (partial) interval
    period = st.mean(intervals) * 1000 if intervals else None
    # attack duration as seen by logger flag
    t_attack_end = max(t for t, _, a in rows if a == 1)
    return dict(t_attack=t_attack, evict_ms=(t_evict - t_attack) * 1000 if t_evict else None,
                decay1_ms=(t_decay1 - t_attack) * 1000 if t_decay1 else None,
                min_trust=min_trust, steps=dec_steps[1:], period_ms=period,
                n_steps=len(dec_steps) - 1, attack_flag_ms=(t_attack_end - t_attack) * 1000)


def main():
    pat = sys.argv[1]; label = sys.argv[2] if len(sys.argv) > 2 else "out"
    files = glob.glob(os.path.join(ROOT, pat, "trial_*.csv")) if os.path.isdir(os.path.join(ROOT, pat)) else glob.glob(os.path.join(ROOT, pat))
    recs = []
    for p in sorted(files):
        m = NAME_RE.search(os.path.basename(p))
        if not m or m["iter"] == "99": continue
        a = analyse(p)
        if a is None: continue
        g = m.groupdict()
        recs.append(dict(file=os.path.basename(p), algo=g["algo"], outage=int(g["level"]), alpha=int(g["ewma"]) / 10,
                         iter=int(g["iter"]), **a))
    out = os.path.join(ROOT, "audit", f"eviction_{label}.csv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0].keys())); w.writeheader()
        for r in recs: w.writerow({**r, "steps": " ".join(f"{s:g}" for s in r["steps"])})

    def fmt(xs):
        xs = [x for x in xs if x is not None]
        if not xs: return f"{'-':>8s} {'-':>6s} {'-':>8s} {'-':>8s}"
        return f"{st.mean(xs):8.1f} {(st.stdev(xs) if len(xs) > 1 else 0):6.1f} {min(xs):8.1f} {max(xs):8.1f}"

    print(f"=== {label}: {len(recs)} valid trials from {pat} ===")
    print("Per (algo, alpha) pooled over outage:")
    print(f"{'algo':5s} {'alpha':>5s} {'n':>3s} {'stops':>5s} {'pred_n':>6s} | evict_ms mean sd min max | decay1_ms mean sd min max | period_ms mean sd min max")
    grp = defaultdict(list)
    for r in recs: grp[(r["algo"], r["alpha"])].append(r)
    for k in sorted(grp):
        rs = grp[k]; pred = math.ceil(math.log(0.3) / math.log(1 - k[1]))
        stops = [r for r in rs if r["evict_ms"] is not None]
        print(f"{k[0]:5s} {k[1]:5.1f} {len(rs):3d} {len(stops):5d} {pred:6d} | {fmt([r['evict_ms'] for r in rs])} | "
              f"{fmt([r['decay1_ms'] for r in rs])} | {fmt([r['period_ms'] for r in rs])}")
    print("\nPer (algo, outage, alpha) cell:")
    print(f"{'algo':5s} {'out':>5s} {'alpha':>5s} {'n':>3s} {'stops':>5s} | evict_ms mean sd min max | min_trust mean | steps observed (distinct) | attack_flag_ms mean")
    grp = defaultdict(list)
    for r in recs: grp[(r["algo"], r["outage"], r["alpha"])].append(r)
    for k in sorted(grp):
        rs = grp[k]; stops = [r for r in rs if r["evict_ms"] is not None]
        seqs = sorted({" ".join(f"{s:g}" for s in r["steps"]) for r in rs})
        print(f"{k[0]:5s} {k[1]:5d} {k[2]:5.1f} {len(rs):3d} {len(stops):5d} | {fmt([r['evict_ms'] for r in rs])} | "
              f"{st.mean(r['min_trust'] for r in rs):9.2f} | {len(seqs)} seq: {' || '.join(seqs)[:110]} | {st.mean(r['attack_flag_ms'] for r in rs):7.0f}")
    print(f"\nwrote {os.path.relpath(out, ROOT)}")


if __name__ == "__main__":
    main()
