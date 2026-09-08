#!/usr/bin/env python3
"""Phase 1: per-campaign trial matrix, duplicates, and basic validity flags.

Parses every trial_*.csv under data/ (all subdirectories), extracts
(algo, outage_or_loss, ewma, iter, epoch) from the filename, and reports for each
directory: the factor levels present, cell counts, duplicate cells (same
algo/outage/ewma/iter with >1 file), and per-file validity using the same rule
run_campaign.validate_trial() uses (>=50 rows, attack_active==1 seen, trust<=30
after attack).  Also records the min trust after attack and the first/last
epoch.  Output: audit/trial_inventory.csv and a stdout summary.  Read-only.
"""
import csv
import os
import re
import sys
from collections import Counter, defaultdict
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "audit", "trial_inventory.csv")

NAME_RE = re.compile(r"trial_(?P<algo>[A-Z]+)_(?P<kind>outage|loss)(?P<level>\d+)_ewma(?P<ewma>\d+)_iter(?P<iter>\d+)_(?P<epoch>\d{10})\.csv$")


def iso(ts):
    return datetime.fromtimestamp(ts, tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")


def validate(path):
    """Mirror of scripts/run_campaign.py::validate_trial (lines 45-85)."""
    rows = 0
    attack_fired = False
    stop = False
    min_trust = 100.0
    first_attack_row = None
    try:
        with open(path, newline="", encoding="utf-8", errors="replace") as f:
            r = csv.reader(f)
            hdr = next(r)
            ti = hdr.index("trust_score")
            ai = hdr.index("attack_active") if "attack_active" in hdr else None
            for row in r:
                if not row:
                    continue
                rows += 1
                if ai is None:
                    continue
                try:
                    a = int(row[ai]); t = float(row[ti])
                except ValueError:
                    continue
                if a == 1 and not attack_fired:
                    attack_fired = True
                    first_attack_row = rows
                if attack_fired:
                    min_trust = min(min_trust, t)
                    if t <= 30.0:
                        stop = True
    except Exception as e:
        return rows, False, False, 100.0, None, f"ERR:{e}"
    valid = rows >= 50 and attack_fired
    return rows, attack_fired, stop, min_trust, first_attack_row, "ok" if valid else "INVALID(run_campaign rule)"


def main():
    recs = []
    for dirpath, _, files in os.walk(DATA):
        for fn in files:
            m = NAME_RE.match(fn)
            if not m:
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            d = os.path.dirname(rel)
            rows, fired, stop, mt, far, status = validate(p)
            g = m.groupdict()
            recs.append({
                "dir": d, "file": fn, "algo": g["algo"], "kind": g["kind"],
                "level": int(g["level"]), "ewma": int(g["ewma"]), "iter": int(g["iter"]),
                "epoch": int(g["epoch"]), "epoch_iso": iso(int(g["epoch"])),
                "rows": rows, "attack_fired": int(fired), "stop_occurred": int(stop),
                "min_trust_after_attack": round(mt, 2), "first_attack_row": far or "",
                "status": status,
            })
    recs.sort(key=lambda r: (r["dir"], r["epoch"]))
    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(recs[0].keys()))
        w.writeheader(); w.writerows(recs)

    by_dir = defaultdict(list)
    for r in recs:
        by_dir[r["dir"]].append(r)
    for d in sorted(by_dir):
        rs = by_dir[d]
        print("=" * 100)
        print(f"{d}: {len(rs)} trial CSVs, {iso(min(r['epoch'] for r in rs))} .. {iso(max(r['epoch'] for r in rs))}")
        print(f"  algos={sorted({r['algo'] for r in rs})} kind={sorted({r['kind'] for r in rs})} "
              f"levels={sorted({r['level'] for r in rs})} ewma={sorted({r['ewma'] for r in rs})} "
              f"iters={sorted({r['iter'] for r in rs})}")
        cells = Counter((r["algo"], r["level"], r["ewma"], r["iter"]) for r in rs)
        dups = {k: v for k, v in cells.items() if v > 1}
        print(f"  distinct (algo,level,ewma,iter) cells: {len(cells)}; duplicate cells: {len(dups)}")
        for k, v in sorted(dups.items()):
            print(f"     dup {k} x{v}")
        inval = [r for r in rs if r["status"] != "ok"]
        print(f"  INVALID by run_campaign rule: {len(inval)}")
        for r in inval:
            print(f"     {r['file']} rows={r['rows']} fired={r['attack_fired']} {r['status']}")
        # stop-rate table per (algo, level, ewma)
        tbl = defaultdict(lambda: [0, 0, []])
        for r in rs:
            if r["status"] != "ok":
                continue
            k = (r["algo"], r["level"], r["ewma"])
            tbl[k][0] += 1; tbl[k][1] += r["stop_occurred"]; tbl[k][2].append(r["min_trust_after_attack"])
        print(f"  {'algo':5s} {'level':>6s} {'ewma':>4s} {'n':>3s} {'stops':>5s} {'min_trust_mean':>14s}")
        for k in sorted(tbl):
            n, s, mts = tbl[k]
            print(f"  {k[0]:5s} {k[1]:6d} {k[2]:4d} {n:3d} {s:5d} {sum(mts)/len(mts):14.2f}")
    print(f"\nWrote {len(recs)} records to {os.path.relpath(OUT, ROOT)}")


if __name__ == "__main__":
    sys.exit(main())
