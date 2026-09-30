"""Plot raw and fitted Hanoi pose geometry for lab review."""

import csv
from pathlib import Path

import matplotlib.pyplot as plt


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/hanoi_teaching/hanoi_pose_geometry_candidates_2026-09-30.csv"
OUTPUT = ROOT / "docs/figures/hanoi_pose_geometry_2026-09-30.png"

with SOURCE.open(newline="", encoding="utf-8") as stream:
    rows = list(csv.DictReader(stream))

colors = {1: "#31688e", 2: "#35b779", 3: "#fde725", 4: "#7b3294"}
figure, (xy, height) = plt.subplots(1, 2, figsize=(13, 5.5), constrained_layout=True)

for peg in sorted({int(row["peg"]) for row in rows}):
    group = sorted((row for row in rows if int(row["peg"]) == peg), key=lambda row: int(row["location"]))
    color = colors[peg]
    xy.scatter(
        [1000 * float(row["raw_tcp_x_m"]) for row in group],
        [1000 * float(row["raw_tcp_y_m"]) for row in group],
        label=f"Post {peg} raw", color=color, alpha=0.75, s=35,
    )
    fitted_xy = (1000 * float(group[0]["fitted_tcp_x_m"]), 1000 * float(group[0]["fitted_tcp_y_m"]))
    xy.scatter([fitted_xy[0]], [fitted_xy[1]], marker="x", color=color, s=120, linewidths=2)
    height.plot(
        [int(row["location"]) for row in group],
        [1000 * float(row["raw_tcp_z_m"]) for row in group],
        marker="o", color=color, alpha=0.75, label=f"Post {peg} raw",
    )

fitted_centers = [
    (1000 * float(next(row for row in rows if int(row["peg"]) == peg)["fitted_tcp_x_m"]),
     1000 * float(next(row for row in rows if int(row["peg"]) == peg)["fitted_tcp_y_m"]))
    for peg in (1, 2, 3, 4)
]
xy.plot([point[0] for point in fitted_centers], [point[1] for point in fitted_centers],
        color="#303030", linestyle="--", linewidth=1.5, label="Fitted post line")
largest = max(rows, key=lambda row: float(row["raw_minus_fit_xy_mm"]))
largest_xy = (1000 * float(largest["raw_tcp_x_m"]), 1000 * float(largest["raw_tcp_y_m"]))
xy.annotate(f'Post {largest["peg"]} level {largest["location"]}', largest_xy,
            xytext=(largest_xy[0] + 9, largest_xy[1] + 15),
            arrowprops={"arrowstyle": "->", "color": "#303030"}, fontsize=9)
xy.set(title="Hand-taught XY positions and fitted post line", xlabel="TCP x in base frame (mm)",
       ylabel="TCP y in base frame (mm)")
xy.grid(alpha=0.2)
xy.legend(fontsize=8, loc="best")

levels = sorted({int(row["location"]) for row in rows})
shared_z = [
    1000 * float(next(row for row in rows if int(row["location"]) == location)["fitted_tcp_z_m"])
    for location in levels
]
height.plot(levels, shared_z, color="#303030", linestyle="--", linewidth=1.5,
            label="Shared level median")
height.set(title="Captured height by stack location", xlabel="Location", ylabel="TCP z in base frame (mm)")
height.set_xticks(levels)
height.grid(alpha=0.2)
height.legend(fontsize=8, loc="best")

figure.suptitle("Analysis only: fitted positions are not validated robot targets", fontsize=12)
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
figure.savefig(OUTPUT, dpi=170, bbox_inches="tight")
print(OUTPUT)
