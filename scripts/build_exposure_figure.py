#!/usr/bin/env python3
"""Build the unified exposure figure (thesis PDF + slide PNG).

One artifact, used twice:
  - docs/figures/exposure_gantt.pdf        (thesis, vector)
  - docs/figures/exposure_gantt_slide.png  (presentation, 16:9)
  - data/exposure_summary.csv              (every number feeding the figure)

Buckets per condition row (time from jam onset, ms):
  [detection, measured ~1P][detection, modeled worst case to 2P][eviction latency]
with min-max whiskers on eviction, a marker at the measured mean total, and the
500 ms self-imposed design budget line.

Sources (all measurements retrace ground_truth.md / project_truth.md):
  - Eviction latency (ECC):  data/v5_spoofing_archive/trial_ECC_*.csv
      first ts(trust_score <= 30) - first ts(attack_active == 1), per trial.
      Must reproduce ground_truth.md §3 (means 1578.8 / 620.2 / 374.3 ms).
  - Eviction latency (real ZKP): data/v7_logs/combined_v7_campaign.csv,
      outage 5000 ms cells only (guaranteed eviction). Must reproduce
      project_truth.md claim 3.6 (~659 / 1122 / 3030 ms).
  - Detection window: data/v7_logs/e2e_composition_results.csv, probe=100 ms,
      per path. Additivity (claim 3.8) is re-verified before use.

The script aborts rather than draw a figure that fails any of these checks.
"""

import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
from matplotlib.lines import Line2D

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
FIGDIR = ROOT / "docs" / "figures"

TRUST_EVICT = 30.0
PROBE_MS = 100.0
WORST_DETECT_MS = 2 * PROBE_MS  # modeled 2P upper bound (claim 3.8)
BUDGET_MS = 500.0               # self-imposed design budget (NOT ISO 13849-1)

# ground_truth.md §3 (ECC rows): alpha -> (mean, min, max), n=20 each
GT_ECC = {0.1: (1578.8, 1500.4, 1735.8),
          0.3: (620.2, 531.6, 764.5),
          0.5: (374.3, 291.0, 504.9)}
# project_truth.md claim 3.6 (real ZKP, outage 5000 ms): alpha -> approx mean
GT_ZKP_APPROX = {0.5: 659.0, 0.3: 1122.0, 0.1: 3030.0}
ZKP_TOL_MS = 40.0

EWMA_ALPHA = {"1": 0.1, "3": 0.3, "5": 0.5}

# Palette (validated with the dataviz six-checks validator, light surface)
C_DETECT = "#2a78d6"
C_EVICT = "#eb6834"
C_INK = "#0b0b0b"
C_INK2 = "#52514e"
C_GRID = "#d9d8d4"
SURFACE = "#ffffff"


def trial_latency_ms(df):
    """Eviction latency per ground_truth.md §3: first trust<=30 after first attack."""
    t = df["timestamp_sec"].to_numpy(float) + df["timestamp_nanosec"].to_numpy(float) * 1e-9
    attack = np.flatnonzero(df["attack_active"].to_numpy() == 1)
    if attack.size == 0:
        return None
    a0 = attack[0]
    evict = np.flatnonzero(df["trust_score"].to_numpy(float)[a0:] <= TRUST_EVICT)
    if evict.size == 0:
        return None
    return (t[a0 + evict[0]] - t[a0]) * 1000.0


def extract_v5_ecc():
    """Per-trial ECC eviction latencies from the V5 archive, deduped per cell.

    Re-queued trials leave multiple files per (outage, alpha, iter) cell. The
    dedup rule is not documented, so try each candidate rule and keep the one
    that reproduces ground_truth.md §3 exactly; abort if none does.
    """
    pat = re.compile(r"trial_ECC_outage(\d+)_ewma([135])_iter(\d+)_(\d+)\.csv$")
    cells = {}
    for f in sorted((DATA / "v5_spoofing_archive").glob("trial_ECC_*.csv")):
        m = pat.search(f.name)
        if not m:
            continue
        outage, ewma, itr, ts = m.groups()
        df = pd.read_csv(f, usecols=["timestamp_sec", "timestamp_nanosec",
                                     "trust_score", "attack_active"])
        lat = trial_latency_ms(df)
        cells.setdefault((int(outage), EWMA_ALPHA[ewma], int(itr)), []).append((int(ts), lat))

    def resolve(rule):
        out = {}
        for cell, cands in cells.items():
            valid = [(ts, lat) for ts, lat in cands if lat is not None]
            if not valid:
                return None
            valid.sort()
            out[cell] = valid[-1][1] if rule == "latest" else valid[0][1]
        return out

    for rule in ("latest", "earliest"):
        resolved = resolve(rule)
        if resolved is None:
            continue
        stats = {}
        ok = True
        for alpha, (gm, gmin, gmax) in GT_ECC.items():
            lats = np.array([v for (o, a, i), v in resolved.items() if a == alpha])
            s = dict(n=lats.size, mean=lats.mean(), min=lats.min(), max=lats.max())
            stats[alpha] = s
            if not (s["n"] == 20 and abs(s["mean"] - gm) <= 0.5
                    and abs(s["min"] - gmin) <= 0.5 and abs(s["max"] - gmax) <= 0.5):
                ok = False
        if ok:
            print(f"[PASS] V5 ECC reproduces ground_truth §3 (dedup rule: {rule} file per cell)")
            return stats
        print(f"[info] dedup rule '{rule}' does not reproduce ground_truth §3:")
        for alpha, s in sorted(stats.items()):
            print(f"       alpha={alpha}: n={s['n']} mean={s['mean']:.1f} "
                  f"min={s['min']:.1f} max={s['max']:.1f}  (target {GT_ECC[alpha]})")
    sys.exit("[FAIL] V5 ECC latencies do not reproduce ground_truth.md §3 under any "
             "dedup rule — investigate before publishing this figure.")


def extract_v7_zkp():
    """Real-ZKP eviction latencies from V7, guaranteed-eviction cells (outage 5000)."""
    df = pd.read_csv(DATA / "v7_logs" / "combined_v7_campaign.csv",
                     usecols=["timestamp_sec", "timestamp_nanosec", "trust_score",
                              "attack_active", "algo", "outage_ms", "alpha", "iteration"])
    n_cells = df.groupby(["algo", "outage_ms", "alpha", "iteration"]).ngroups
    print(f"[info] V7 campaign: {n_cells} trial cells "
          f"({'matches' if n_cells == 75 else 'EXPECTED 75 — got'} the 75 in project_truth)")
    stats = {}
    for alpha, gm in GT_ZKP_APPROX.items():
        lats = []
        sub = df[(df["algo"] == "ZKP") & (df["outage_ms"] == 5000) & (df["alpha"] == alpha)]
        for _, trial in sub.groupby("iteration"):
            lat = trial_latency_ms(trial.reset_index(drop=True))
            if lat is not None:
                lats.append(lat)
        lats = np.array(lats)
        s = dict(n=lats.size, mean=lats.mean(), min=lats.min(), max=lats.max())
        stats[alpha] = s
        if s["n"] != 5 or abs(s["mean"] - gm) > ZKP_TOL_MS:
            sys.exit(f"[FAIL] V7 ZKP alpha={alpha}: n={s['n']} mean={s['mean']:.1f} ms "
                     f"vs claim 3.6 ~{gm:.0f} ms (tol {ZKP_TOL_MS} ms) — investigate.")
    print("[PASS] V7 ZKP (outage 5000) reproduces project_truth claim 3.6 "
          + ", ".join(f"alpha={a}: {s['mean']:.0f} ms" for a, s in sorted(stats.items())))
    return stats


def extract_detection():
    """Measured detection window per path from the e2e block, probe=100 ms."""
    df = pd.read_csv(DATA / "v7_logs" / "e2e_composition_results.csv")
    resid = (df["detection_window_ms"] + df["eviction_latency_ms"]
             - df["total_exposure_ms"]).abs().max()
    if resid > 0.01:
        sys.exit(f"[FAIL] e2e additivity violated (max residual {resid:.3f} ms) — claim 3.8.")
    print(f"[PASS] e2e additivity verified (max residual {resid:.3f} ms, {len(df)} trials)")
    out = {}
    for algo, sub in df[df["probe_ms"] == 100].groupby("algo"):
        out[algo] = dict(n=len(sub),
                         det_mean=sub["detection_window_ms"].mean(),
                         onset_mean=(sub["t_first_decay"] - sub["t_detection"]).mean() * 1000.0,
                         total_mean=sub["total_exposure_ms"].mean())
    return out


def n_cycles(alpha):
    return int(np.ceil(np.log(0.3) / np.log(1.0 - alpha)))


def build_rows(ecc, zkp, det):
    rows = []
    for path, label, cyc, stats, dkey in (
            ("ECC", "ECC — 111.5 ms crypto (~123 ms cycle)", 123, ecc, "ECC"),
            ("ZKP", "Real ZKP — 224.9 ms crypto (~247 ms cycle)", 247, zkp, "ZKP")):
        for alpha in (0.5, 0.3, 0.1):
            s = stats[alpha]
            d = det[dkey]
            rows.append(dict(
                path=path, group_label=label, cycle_ms=cyc, alpha=alpha,
                pred_cycles=n_cycles(alpha),
                det_mean=d["det_mean"], det_n=d["n"], onset_mean=d["onset_mean"],
                evict_mean=s["mean"], evict_min=s["min"], evict_max=s["max"],
                evict_n=s["n"],
                measured_total=d["det_mean"] + s["mean"],
                worstcase_total=WORST_DETECT_MS + s["mean"],
            ))
    return rows


def draw(rows, out_path, slide=False):
    fs = dict(tick=15 if slide else 8.5, label=16 if slide else 9,
              bar=15 if slide else 8, group=17 if slide else 9,
              legend=13.5 if slide else 7.5, title=24)
    barh = 0.62
    group_gap = 1.15

    ys, ylabels = [], []
    y = 0.0
    for i, r in enumerate(rows):
        if i == 3:
            y -= group_gap  # gap between ECC and ZKP groups
        ys.append(y)
        ylabels.append(f"α = {r['alpha']:.1f}\n({r['pred_cycles']} cycles)")
        y -= 1.0

    figsize = (13.333, 7.5) if slide else (7.1, 3.9)
    fig, ax = plt.subplots(figsize=figsize, dpi=150 if slide else 200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)

    edge = dict(edgecolor=SURFACE, linewidth=1.4)
    for r, yy in zip(rows, ys):
        d = r["det_mean"]
        ax.barh(yy, d, height=barh, color=C_DETECT, **edge)
        ax.barh(yy, WORST_DETECT_MS - d, left=d, height=barh, facecolor=SURFACE,
                edgecolor=C_DETECT, linewidth=0.9, hatch="////")
        ax.barh(yy, r["evict_mean"], left=WORST_DETECT_MS, height=barh,
                color=C_EVICT, **edge)
        # min-max whisker (eviction spread, drawn at the worst-case position)
        w0, w1 = WORST_DETECT_MS + r["evict_min"], WORST_DETECT_MS + r["evict_max"]
        ax.plot([w0, w1], [yy, yy], color=C_INK, lw=1.3, solid_capstyle="butt", zorder=4)
        for wx in (w0, w1):
            ax.plot([wx, wx], [yy - 0.16, yy + 0.16], color=C_INK, lw=1.3, zorder=4)
        # measured mean total marker
        ax.plot(r["measured_total"], yy, marker="D", ms=9 if slide else 5,
                mfc=C_INK, mec=SURFACE, mew=1.1, zorder=5)
        # end label: modeled worst-case mean total
        ax.text(w1 + (34 if slide else 26), yy, f"{r['worstcase_total']:,.0f} ms",
                va="center", ha="left", fontsize=fs["bar"], color=C_INK,
                fontweight="bold")

    # group labels above each block of three bars
    for idx in (0, 3):
        ax.text(0, ys[idx] + 0.78, rows[idx]["group_label"],
                fontsize=fs["group"], fontweight="bold", color=C_INK,
                ha="left", va="center", zorder=6,
                bbox=dict(facecolor=SURFACE, edgecolor="none", pad=1.5))

    ax.axvline(BUDGET_MS, color=C_INK2, lw=1.2, ls=(0, (4, 3)), zorder=3)
    ax.text(BUDGET_MS + 30, ys[-1] - 0.55, "500 ms budget (self-imposed)",
            fontsize=fs["label"], color=C_INK2, ha="left", va="center")

    ax.set_yticks(ys)
    ax.set_yticklabels(ylabels, fontsize=fs["tick"], color=C_INK)
    ax.set_xlabel("Time since jam onset (ms)", fontsize=fs["label"], color=C_INK)
    ax.set_xlim(0, 3950)
    ax.set_ylim(ys[-1] - 0.75, ys[0] + 1.75)
    ax.xaxis.grid(True, color=C_GRID, lw=0.6)
    ax.set_axisbelow(True)
    ax.tick_params(axis="x", labelsize=fs["tick"], colors=C_INK)
    for s in ("top", "right", "left"):
        ax.spines[s].set_visible(False)
    ax.spines["bottom"].set_color(C_GRID)

    handles = [
        Patch(color=C_DETECT, label=f"Detection — measured (≈1 probe, P = {PROBE_MS:.0f} ms)"),
        Patch(facecolor=SURFACE, edgecolor=C_DETECT, hatch="////",
              label="Detection — modeled worst case (2P bound)"),
        Patch(color=C_EVICT, label="Eviction latency — measured mean"),
        Line2D([], [], color=C_INK, lw=1.3, label="Min–max across trials (eviction)"),
        Line2D([], [], marker="D", ls="none", mfc=C_INK, mec=SURFACE,
               ms=8 if slide else 5, label="Measured mean total (detection + eviction)"),
        Line2D([], [], color=C_INK2, lw=1.2, ls=(0, (4, 3)),
               label="500 ms design budget (self-imposed)"),
    ]
    ax.legend(handles=handles, loc="upper right", fontsize=fs["legend"],
              frameon=False, ncol=1, bbox_to_anchor=(1.0, 0.99),
              handlelength=1.6, labelspacing=0.55 if slide else 0.4)

    if slide:
        fig.suptitle("Attack exposure: detection + eviction vs the 500 ms budget",
                     fontsize=fs["title"], fontweight="bold", color=C_INK,
                     x=0.055, ha="left", y=0.965)
        ax.set_title("Measured means · ECC: V5 (n = 20/α) · real ZKP: V7 "
                     "guaranteed-eviction cells (n = 5/α) · detection: 20 e2e trials",
                     fontsize=13.5, color=C_INK2, loc="left", pad=14)
        fig.subplots_adjust(left=0.10, right=0.975, top=0.845, bottom=0.10)
    else:
        fig.subplots_adjust(left=0.115, right=0.98, top=0.93, bottom=0.13)

    fig.savefig(out_path, facecolor=SURFACE)
    plt.close(fig)
    print(f"[out ] {out_path.relative_to(ROOT)}")


def write_summary(rows, out_csv):
    df = pd.DataFrame(rows)
    df["detection_2p_ms"] = WORST_DETECT_MS
    df["budget_ms"] = BUDGET_MS
    df["eviction_source"] = np.where(df["path"] == "ECC",
                                     "data/v5_spoofing_archive (ground_truth §3)",
                                     "data/v7_logs/combined_v7_campaign.csv outage=5000 (claim 3.6)")
    df["detection_source"] = "data/v7_logs/e2e_composition_results.csv probe=100 (claim 3.8)"
    cols = ["path", "cycle_ms", "alpha", "pred_cycles", "det_mean", "det_n",
            "detection_2p_ms", "onset_mean", "evict_mean", "evict_min", "evict_max",
            "evict_n", "measured_total", "worstcase_total", "budget_ms",
            "eviction_source", "detection_source"]
    df[cols].round(2).to_csv(out_csv, index=False)
    print(f"[out ] {out_csv.relative_to(ROOT)}")


def main():
    print("=== Unified exposure figure ===")
    ecc = extract_v5_ecc()
    zkp = extract_v7_zkp()
    det = extract_detection()
    rows = build_rows(ecc, zkp, det)

    print("\nFigure rows:")
    for r in rows:
        print(f"  {r['path']:>3} α={r['alpha']:.1f}: detect {r['det_mean']:6.1f} ms "
              f"(2P bound {WORST_DETECT_MS:.0f}) + evict {r['evict_mean']:7.1f} ms "
              f"[{r['evict_min']:.1f}–{r['evict_max']:.1f}] → measured {r['measured_total']:7.1f} / "
              f"worst-case {r['worstcase_total']:7.1f} ms")

    FIGDIR.mkdir(parents=True, exist_ok=True)
    draw(rows, FIGDIR / "exposure_gantt.pdf", slide=False)
    draw(rows, FIGDIR / "exposure_gantt_slide.png", slide=True)
    write_summary(rows, DATA / "exposure_summary.csv")


if __name__ == "__main__":
    main()
