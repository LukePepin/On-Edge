#!/usr/bin/env python3
"""Generate Draft-1 figures for the thesis from the audited data.

Outputs (PDF) into the thesis figures directory given as argv[1]:
  fig_proxy_cost.pdf        histogram of the 300 ZKP-cost-proxy timings
  fig_eviction_vs_alpha.pdf per-trial eviction latency vs alpha, V6 (ECC) and V7 (proxy),
                            with the model (n(alpha)+0.5)*T_cycle
  fig_stop_map.pdf          physical stop fraction per (outage, alpha) cell with the
                            n(alpha)*T_cycle threshold
  fig_e2e_structure.pdf     bench block: detection / first-decay / eviction segments per trial
Sources: data/real_zkp_profiling.csv, audit/eviction_v6.csv, audit/eviction_v7.csv, the trial
CSVs (for the physical-stop column), data/v7_logs/e2e_composition_results.csv.
Read-only with respect to data/.
"""
import csv, glob, math, os, re, sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
OUT = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "audit", "figures")
os.makedirs(OUT, exist_ok=True)
T_ECC, T_PROXY = 120.4, 232.1
plt.rcParams.update({"font.size": 10, "figure.dpi": 150, "savefig.bbox": "tight"})
n_alpha = lambda a: math.ceil(math.log(0.3) / math.log(1 - a))

# ---------- fig 1: proxy cost histogram ----------
pf = pd.read_csv(os.path.join(ROOT, "data", "real_zkp_profiling.csv"))
fig, ax = plt.subplots(figsize=(5.5, 3.2))
ax.hist(pf.exec_time_ms, bins=30, color="0.55", edgecolor="black")
ax.axvline(pf.exec_time_ms.mean(), color="black", ls="--", lw=1)
ax.set_xlabel("Execution time of two secp256r1 scalar multiplications (ms)")
ax.set_ylabel("Runs")
ax.set_title(f"ZKP-cost proxy, n={len(pf)}: mean {pf.exec_time_ms.mean():.2f} ms, sd {pf.exec_time_ms.std():.2f} ms")
fig.savefig(os.path.join(OUT, "fig_proxy_cost.pdf")); plt.close(fig)

# ---------- physical stop per trial (same rule as audit/physical_stop_crosstab.py) ----------
NAME_RE = re.compile(r"trial_(?P<algo>[A-Z]+)_(?:outage|loss)(?P<level>\d+)_ewma(?P<ewma>\d+)_iter(?P<iter>\d+)_(?P<epoch>\d{10})\.csv$")
def physical_stop(p):
    rows = []
    for x in csv.reader(open(p, newline="", encoding="utf-8", errors="replace")):
        if not x or x[0] == "timestamp_sec": continue
        try: rows.append((int(x[0]) + int(x[1]) / 1e9, int(x[-1]), max(abs(float(v)) for v in x[9:15])))
        except ValueError: pass
    if len(rows) < 50 or not any(a for _, a, _ in rows): return None
    ta = next(t for t, a, _ in rows if a == 1)
    win = [(t, v) for t, _, v in rows if ta <= t <= ta + 9.5]
    if not win or win[-1][0] < ta + 9.0: return None
    mv = [t for t, v in win if v >= 0.02]
    return (mv[-1] if mv else ta) <= ta + 8.5

def cells(pattern):
    files = glob.glob(os.path.join(ROOT, pattern, "trial_*.csv")) if os.path.isdir(os.path.join(ROOT, pattern)) else glob.glob(os.path.join(ROOT, pattern))
    d = {}
    for p in files:
        m = NAME_RE.search(os.path.basename(p))
        if not m or m["iter"] == "99": continue
        ps = physical_stop(p)
        if ps is None: continue
        k = (int(m["level"]), int(m["ewma"]) / 10)
        d.setdefault(k, []).append(ps)
    return {k: (sum(v), len(v)) for k, v in d.items()}
v6c = cells("data/v6_logs"); v7c = cells("data/v7_logs/trial_ZKP_outage*.csv")

# ---------- fig 2: eviction latency vs alpha ----------
e6 = pd.read_csv(os.path.join(ROOT, "audit", "eviction_v6.csv")).dropna(subset=["evict_ms"])
e7 = pd.read_csv(os.path.join(ROOT, "audit", "eviction_v7.csv")).dropna(subset=["evict_ms"])
fig, ax = plt.subplots(figsize=(6, 3.6))
rng = np.random.default_rng(0)
for df, T, lab, mk, off in ((e6, T_ECC, "ECC (V6, n=73)", "o", -0.012), (e7, T_PROXY, "ZKP-cost proxy (V7, n=44)", "s", 0.012)):
    ax.scatter(df.alpha + off + rng.uniform(-0.006, 0.006, len(df)), df.evict_ms, s=14, marker=mk, alpha=0.7, label=lab)
    xs = np.array([0.1, 0.3, 0.5])
    ax.plot(xs + off, [(n_alpha(a) + 0.5) * T for a in xs], "k_", ms=18, mew=1.5)
ax.plot([], [], "k_", ms=12, mew=1.5, label=r"model $(n(\alpha)+\frac{1}{2})\,T_{cycle}$")
ax.axhline(500, color="0.4", ls=":", lw=1); ax.text(0.52, 520, "500 ms budget", fontsize=8, color="0.3")
ax.set_xticks([0.1, 0.3, 0.5]); ax.set_xlabel(r"EWMA weight on new sample, $\alpha$")
ax.set_ylabel("Eviction latency (ms, logger clock)"); ax.set_yscale("log")
ax.set_yticks([250, 500, 1000, 2000, 4000]); ax.get_yaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter())
ax.legend(fontsize=8, loc="upper right")
fig.savefig(os.path.join(OUT, "fig_eviction_vs_alpha.pdf")); plt.close(fig)

# ---------- fig 3: stop map ----------
fig, axes = plt.subplots(1, 2, figsize=(7.5, 3.2), sharey=True)
for ax, cel, T, title in ((axes[0], v6c, T_ECC, "ECC, V6 (n=10 per cell)"), (axes[1], v7c, T_PROXY, "ZKP-cost proxy, V7 (n=5 per cell)")):
    for (out, a), (s, n) in cel.items():
        frac = s / n
        ax.scatter(out, a, s=90, c=[frac], cmap="Greys", vmin=0, vmax=1, edgecolors="black", zorder=3)
        ax.annotate(f"{s}/{n}", (out, a), textcoords="offset points", xytext=(0, 9), ha="center", fontsize=7)
    for a in (0.1, 0.3, 0.5):
        thr = n_alpha(a) * T
        ax.plot([thr, thr], [a - 0.05, a + 0.05], color="black", lw=1.5, zorder=2)
        ax.annotate(f"{n_alpha(a)}x{T:.0f}={thr:.0f}", (thr, a - 0.055), fontsize=6.5, ha="center", va="top")
    ax.set_xscale("log"); ax.set_xticks([250, 500, 1000, 2000, 3000, 5000])
    ax.get_xaxis().set_major_formatter(matplotlib.ticker.ScalarFormatter()); ax.tick_params(axis="x", labelsize=8)
    ax.set_yticks([0.1, 0.3, 0.5]); ax.set_ylim(0.0, 0.62); ax.set_xlabel("Outage duration (ms)"); ax.set_title(title, fontsize=9)
axes[0].set_ylabel(r"$\alpha$")
fig.suptitle("Physical stops per cell (fill = fraction stopped); bars = threshold n(alpha)*T_cycle", fontsize=9)
fig.savefig(os.path.join(OUT, "fig_stop_map.pdf")); plt.close(fig)

# ---------- fig 4: e2e structure ----------
e2 = pd.read_csv(os.path.join(ROOT, "data", "v7_logs", "e2e_composition_results.csv"))
e2["det"] = (e2.t_detection - e2.t_jam) * 1000
e2["dec"] = (e2.t_first_decay - e2.t_detection) * 1000
e2["evi"] = (e2.t_eviction - e2.t_first_decay) * 1000
e2 = e2.sort_values(["probe_ms", "algo", "iter"]).reset_index(drop=True)
fig, ax = plt.subplots(figsize=(6.5, 3.6))
y = np.arange(len(e2))
ax.barh(y, e2.det, color="0.85", edgecolor="black", label="detection (probe timeout)")
ax.barh(y, e2.dec, left=e2.det, color="0.55", edgecolor="black", label="detection to first trust decay")
ax.barh(y, e2.evi, left=e2.det + e2.dec, color="0.2", edgecolor="black", label="first decay to eviction (one cycle)")
ax.set_yticks(y); ax.set_yticklabels([f"{r.probe_ms} ms / {r.algo} / {r.iter}" for r in e2.itertuples()], fontsize=6.5)
ax.invert_yaxis(); ax.set_xlabel("Time after jam onset (ms)"); ax.legend(fontsize=7, loc="lower right")
fig.savefig(os.path.join(OUT, "fig_e2e_structure.pdf")); plt.close(fig)
print("wrote 4 figures to", OUT)
print("V6 cells:", sorted(v6c.items())); print("V7 cells:", sorted(v7c.items()))
