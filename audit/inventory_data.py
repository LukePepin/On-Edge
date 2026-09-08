#!/usr/bin/env python3
"""Phase 1 data inventory for the On-Edge audit.

For every CSV under data/ (recursively) report: path, row count (excluding header),
column list, embedded epoch timestamp from filename, and the min/max of any
timestamp-like column found in the file.  Output: audit/data_inventory.csv plus a
per-directory roll-up printed to stdout.

Read-only: never modifies anything under data/.
"""
import csv
import os
import re
import sys
from collections import defaultdict
from datetime import datetime, timezone

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
DATA = os.path.join(ROOT, "data")
OUT = os.path.join(ROOT, "audit", "data_inventory.csv")

EPOCH_RE = re.compile(r"(1[78]\d{8})")  # 10-digit epoch in filename


def iso(ts):
    try:
        return datetime.fromtimestamp(float(ts), tz=timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    except Exception:
        return ""


def inspect(path):
    rows = 0
    header = []
    tmin = tmax = None
    ts_col = None
    with open(path, "r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return rows, header, None, None
        # choose a timestamp column
        for cand in ("timestamp_sec", "timestamp", "t_jam"):
            if cand in header:
                ts_col = header.index(cand)
                break
        for row in reader:
            if not row:
                continue
            rows += 1
            if ts_col is not None and ts_col < len(row):
                try:
                    v = float(row[ts_col])
                    if v > 1e9:  # epoch seconds
                        tmin = v if tmin is None else min(tmin, v)
                        tmax = v if tmax is None else max(tmax, v)
                except ValueError:
                    pass
    return rows, header, tmin, tmax


def main():
    records = []
    for dirpath, _, files in os.walk(DATA):
        for fn in sorted(files):
            if not fn.lower().endswith(".csv"):
                continue
            p = os.path.join(dirpath, fn)
            rel = os.path.relpath(p, ROOT).replace("\\", "/")
            rows, header, tmin, tmax = inspect(p)
            m = EPOCH_RE.search(fn)
            fn_epoch = int(m.group(1)) if m else None
            records.append({
                "path": rel,
                "dir": os.path.dirname(rel),
                "rows": rows,
                "ncols": len(header),
                "columns": "|".join(header),
                "filename_epoch": fn_epoch or "",
                "filename_epoch_iso": iso(fn_epoch) if fn_epoch else "",
                "data_tmin_iso": iso(tmin) if tmin else "",
                "data_tmax_iso": iso(tmax) if tmax else "",
                "size_bytes": os.path.getsize(p),
            })

    with open(OUT, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=list(records[0].keys()))
        w.writeheader()
        w.writerows(records)

    # roll-up per directory
    by_dir = defaultdict(list)
    for r in records:
        by_dir[r["dir"]].append(r)
    print(f"{'directory':45s} {'csv':>5s} {'rows':>9s}  epoch range (filename)            header signature(s)")
    for d in sorted(by_dir):
        rs = by_dir[d]
        eps = [r["filename_epoch"] for r in rs if r["filename_epoch"]]
        rng = f"{iso(min(eps))} .. {iso(max(eps))}" if eps else "(no epoch in names)"
        sigs = sorted({r["columns"][:60] for r in rs})
        print(f"{d:45s} {len(rs):5d} {sum(r['rows'] for r in rs):9d}  {rng:34s} {len(sigs)} distinct")
        for s in sigs:
            print(f"{'':45s} {'':5s} {'':9s}  {'':34s}   - {s}")
    print(f"\nWrote {len(records)} records to {os.path.relpath(OUT, ROOT)}")

    # pcap count per dir
    pc = defaultdict(int)
    for dirpath, _, files in os.walk(DATA):
        for fn in files:
            if fn.lower().endswith(".pcap"):
                pc[os.path.relpath(dirpath, ROOT).replace("\\", "/")] += 1
    print("\nPCAP counts:")
    for d in sorted(pc):
        print(f"  {d:45s} {pc[d]}")


if __name__ == "__main__":
    sys.exit(main())
