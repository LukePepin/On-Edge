#!/usr/bin/env python3
"""Phase 3/4: does the robot physically stop after the logged eviction, and how fast?

For each valid stopping trial: t_evict = first row with trust<=30 after attack.
  v_at_evict   = max |joint velocity| at t_evict
  t_standstill = first row >= t_evict where max|v| < 0.01 rad/s and stays below for 10 rows
  decel_ms     = t_standstill - t_evict
  stream_halted= True if joint_logger's zero-velocity fallback likely fired (all six velocities
                 exactly 0.0 for >= 5 consecutive rows at standstill), which would mean the
                 RTDE stream stopped rather than a measured deceleration.
Also reports whether the arm was moving at the moment of eviction (v_at_evict > 0.05).
Usage: python audit/decel_after_eviction.py <dir-or-glob> <label>.  Read-only.
"""
import csv, glob, os, re, sys, statistics as st
from collections import defaultdict
ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME_RE = re.compile(r"trial_(?P<algo>[A-Z]+)_(?:outage|loss)(?P<level>\d+)_ewma(?P<ewma>\d+)_iter(?P<iter>\d+)_(?P<epoch>\d{10})\.csv$")

def analyse(p):
    with open(p, newline="", encoding="utf-8", errors="replace") as f:
        r = csv.reader(f); hdr = next(r)
        ti, ai = hdr.index("trust_score"), hdr.index("attack_active")
        vi = [hdr.index(c) for c in ("shoulder_pan_vel","shoulder_lift_vel","elbow_vel","wrist_1_vel","wrist_2_vel","wrist_3_vel")]
        rows = []
        for x in r:
            if not x: continue
            try: rows.append((int(x[0]) + int(x[1]) / 1e9, float(x[ti]), int(x[ai]), [float(x[i]) for i in vi]))
            except ValueError: continue
    if len(rows) < 50 or not any(a for _, _, a, _ in rows): return None
    ia = next(i for i, (_, _, a, _) in enumerate(rows) if a == 1)
    ie = next((i for i in range(ia, len(rows)) if rows[i][1] <= 30.0), None)
    if ie is None: return None
    vmax = lambda i: max(abs(v) for v in rows[i][3])
    v_evict = vmax(ie)
    ist = None
    for i in range(ie, len(rows) - 10):
        if all(vmax(j) < 0.01 for j in range(i, i + 10)):
            ist = i; break
    halted = ist is not None and all(all(v == 0.0 for v in rows[j][3]) for j in range(ist, ist + 5))
    return dict(v_evict=v_evict, decel_ms=(rows[ist][0] - rows[ie][0]) * 1000 if ist else None, stream_halted=halted,
                moving=v_evict > 0.05)

def main():
    pat, label = sys.argv[1], sys.argv[2]
    files = glob.glob(os.path.join(ROOT, pat, "trial_*.csv")) if os.path.isdir(os.path.join(ROOT, pat)) else glob.glob(os.path.join(ROOT, pat))
    grp = defaultdict(list)
    for p in sorted(files):
        m = NAME_RE.search(os.path.basename(p))
        if not m or m["iter"] == "99": continue
        a = analyse(p)
        if a: grp[(m["algo"], int(m["ewma"]) / 10)].append(a)
    print(f"=== {label} ===")
    print(f"{'algo':5s} {'alpha':>5s} {'stops':>5s} {'moving@evict':>12s} {'stream_halted':>13s} | decel_ms (moving only) mean sd min max")
    for k in sorted(grp):
        rs = grp[k]; mv = [r for r in rs if r["moving"] and r["decel_ms"] is not None]
        d = [r["decel_ms"] for r in mv]
        print(f"{k[0]:5s} {k[1]:5.1f} {len(rs):5d} {len(mv):12d} {sum(r['stream_halted'] for r in rs):13d} | "
              + (f"{st.mean(d):6.0f} {st.stdev(d) if len(d)>1 else 0:5.0f} {min(d):5.0f} {max(d):5.0f}" if d else "n/a"))

if __name__ == "__main__": main()
