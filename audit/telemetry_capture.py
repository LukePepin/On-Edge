#!/usr/bin/env python3
"""Phase 2/3: how much firmware telemetry does joint_logger_node.py actually capture?

joint_logger_node.serial_read_loop() (lines 148-161) calls reset_input_buffer(),
sleeps 10 ms, then does a non-blocking readline(); any line not wholly inside
that window is discarded.  Under attack the firmware emits one trust value per
cycle, trust(k) = 100*(1-alpha)^k, so the set of *expected* values is known
exactly.  For each valid trial this script lists the distinct logged trust
values during the decay and reports which expected steps were captured.

Metrics per campaign:
  capture_ratio  = captured decay steps / expected decay steps
                   (expected = number of consecutive attack cycles until the
                   logged minimum, i.e. k_min = log(min/100)/log(1-alpha))
  crossing_missed = the first logged value <= 30 is NOT the first expected
                   value <= 30 (i.e. the eviction crossing line was dropped and
                   the eviction timestamp is >= 1 cycle late)
Read-only.
"""
import csv, glob, math, os, re, sys, statistics as st
from collections import defaultdict

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
NAME_RE = re.compile(r"trial_(?P<algo>[A-Z]+)_(?:outage|loss)(?P<level>\d+)_ewma(?P<ewma>\d+)_iter(?P<iter>\d+)_(?P<epoch>\d{10})\.csv$")


def run(pat, label):
    files = glob.glob(os.path.join(ROOT, pat, "trial_*.csv")) if os.path.isdir(os.path.join(ROOT, pat)) else glob.glob(os.path.join(ROOT, pat))
    out = defaultdict(list)
    for p in sorted(files):
        m = NAME_RE.search(os.path.basename(p))
        if not m or m["iter"] == "99": continue
        alpha = int(m["ewma"]) / 10
        with open(p, newline="", encoding="utf-8", errors="replace") as f:
            r = csv.reader(f); hdr = next(r); ti, ai = hdr.index("trust_score"), hdr.index("attack_active")
            rows = [(float(x[ti]), int(x[ai])) for x in r if x]
        if len(rows) < 50 or not any(a for _, a in rows): continue
        i0 = next(i for i, (_, a) in enumerate(rows) if a == 1)
        seq, last = [], None
        for tr, _ in rows[i0:]:
            if tr != last:
                seq.append(tr); last = tr
        dec = [seq[0]]
        for s in seq[1:]:
            if s < dec[-1]: dec.append(s)
            else: break
        dec = [round(x, 2) for x in dec[1:]]  # logged decay values (exclude starting value)
        if not dec: continue
        expected = []
        v = 100.0; k = 0
        while round(v, 2) > min(dec) - 1e-9 and k < 200:
            v *= (1 - alpha); k += 1; expected.append(round(v, 2))
        captured = [e for e in expected if e in dec]
        first_exp_cross = next((e for e in expected if e <= 30.0), None)
        first_log_cross = next((d for d in dec if d <= 30.0), None)
        crossing_missed = first_log_cross is not None and first_exp_cross is not None and first_log_cross != first_exp_cross
        out[(m["algo"], alpha)].append((len(captured) / len(expected), crossing_missed, first_log_cross is not None, len(expected)))
    print(f"=== {label} ===")
    print(f"{'algo':5s} {'alpha':>5s} {'n':>3s} {'capture_ratio mean':>18s} {'min':>5s} {'stops':>5s} {'crossing_missed':>15s}")
    for k in sorted(out):
        v = out[k]; stops = [x for x in v if x[2]]
        print(f"{k[0]:5s} {k[1]:5.1f} {len(v):3d} {st.mean(x[0] for x in v):18.2f} {min(x[0] for x in v):5.2f} {len(stops):5d} {sum(x[1] for x in stops):15d}")


if __name__ == "__main__":
    run(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else sys.argv[1])
