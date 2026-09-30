"""Describe the hand-taught Hanoi geometry without changing or executing poses.

The fitted positions are review aids only. Joint angles and tool orientation in the
capture cannot be combined with fitted TCP coordinates to make an executable pose.
"""

import csv
import hashlib
import math
import shutil
import statistics
from collections import defaultdict
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/hanoi_teaching/hanoi_poses_2026-09-29.csv"
SNAPSHOT = ROOT / "data/hanoi_teaching/hanoi_poses_2026-09-29_raw_snapshot.csv"
CANDIDATES = ROOT / "data/hanoi_teaching/hanoi_pose_geometry_candidates_2026-09-30.csv"
REPORT = ROOT / "audit/hanoi_pose_geometry_2026-09-30.md"


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def line_fit(centers):
    """Project per-peg median XY centers onto a common best-fit line.

    The projected peg spacings remain measured; equal spacing is not assumed.
    """
    points = list(centers.values())
    mean_x = statistics.mean(point[0] for point in points)
    mean_y = statistics.mean(point[1] for point in points)
    xx = statistics.mean((x - mean_x) ** 2 for x, _ in points)
    yy = statistics.mean((y - mean_y) ** 2 for _, y in points)
    xy = statistics.mean((x - mean_x) * (y - mean_y) for x, y in points)
    angle = 0.5 * math.atan2(2 * xy, xx - yy)
    direction = (math.cos(angle), math.sin(angle))
    projections = {}
    for peg, (x, y) in centers.items():
        distance_along = (x - mean_x) * direction[0] + (y - mean_y) * direction[1]
        projections[peg] = (
            mean_x + distance_along * direction[0],
            mean_y + distance_along * direction[1],
        )
    return projections


def linear_fit(points):
    center_x = statistics.mean(x for x, _ in points)
    center_y = statistics.mean(y for _, y in points)
    numerator = sum((x - center_x) * (y - center_y) for x, y in points)
    denominator = sum((x - center_x) ** 2 for x, _ in points)
    slope = numerator / denominator
    intercept = center_y - slope * center_x
    return intercept, slope


def summarize_joint(rows, joint):
    lines = []
    for peg in sorted({row["peg"] for row in rows}):
        points = [(row["location"] - 1, row[joint]) for row in rows if row["peg"] == peg]
        intercept, slope = linear_fit(points)
        residual_mm_or_rad = max(abs(value - (intercept + slope * height)) for height, value in points)
        lines.append((peg, slope, residual_mm_or_rad))
    return lines


def main():
    if SNAPSHOT.exists():
        if sha256(SNAPSHOT) != sha256(SOURCE):
            raise RuntimeError("Raw snapshot differs from source; refusing to overwrite it")
    else:
        shutil.copyfile(SOURCE, SNAPSHOT)

    with SOURCE.open(newline="", encoding="utf-8-sig") as stream:
        rows = list(csv.DictReader(stream))
    if not rows:
        raise RuntimeError("Pose CSV is empty")

    records = []
    seen = set()
    for row in rows:
        peg, location = int(row["peg"]), int(row["location"])
        if (peg, location) in seen:
            raise RuntimeError(f"Duplicate capture for peg {peg}, location {location}")
        seen.add((peg, location))
        if row["pose_role"] != "source_approach" or row["replay_validated"].lower() != "false":
            raise RuntimeError("Unexpected pose role or replay status in the input")
        record = {
            "peg": peg,
            "location": location,
            "source_line": row["source_line"],
            "x": float(row["tcp_x_m"]),
            "y": float(row["tcp_y_m"]),
            "z": float(row["tcp_z_m"]),
            "wrist_1": float(row["wrist_1_rad"]),
            "wrist_2": float(row["wrist_2_rad"]),
            "wrist_3": float(row["wrist_3_rad"]),
        }
        if not all(math.isfinite(value) for key, value in record.items() if key not in {"source_line"}):
            raise RuntimeError(f"Nonfinite coordinate in peg {peg}, location {location}")
        records.append(record)

    pegs = sorted({row["peg"] for row in records})
    locations = sorted({row["location"] for row in records})
    if len(records) != len(pegs) * len(locations):
        raise RuntimeError("Pose grid is incomplete")

    by_peg = defaultdict(list)
    by_location = defaultdict(list)
    for record in records:
        by_peg[record["peg"]].append(record)
        by_location[record["location"]].append(record)
    peg_centers = {
        peg: (statistics.median(row["x"] for row in group), statistics.median(row["y"] for row in group))
        for peg, group in by_peg.items()
    }
    projected = line_fit(peg_centers)
    heights = {location: statistics.median(row["z"] for row in group) for location, group in by_location.items()}
    z_base, z_pitch = linear_fit([(location - 1, heights[location]) for location in locations])

    output = []
    for row in sorted(records, key=lambda item: (item["peg"], item["location"])):
        x_fit, y_fit = projected[row["peg"]]
        z_fit = heights[row["location"]]
        xy_delta_mm = 1000 * math.hypot(row["x"] - x_fit, row["y"] - y_fit)
        z_delta_mm = 1000 * (row["z"] - z_fit)
        output.append({
            "peg": row["peg"],
            "location": row["location"],
            "source_line": row["source_line"],
            "raw_tcp_x_m": f'{row["x"]:.15f}',
            "raw_tcp_y_m": f'{row["y"]:.15f}',
            "raw_tcp_z_m": f'{row["z"]:.15f}',
            "fitted_tcp_x_m": f"{x_fit:.15f}",
            "fitted_tcp_y_m": f"{y_fit:.15f}",
            "fitted_tcp_z_m": f"{z_fit:.15f}",
            "raw_minus_fit_xy_mm": f"{xy_delta_mm:.2f}",
            "raw_minus_fit_z_mm": f"{z_delta_mm:.2f}",
            "large_difference_over_5_mm": str(xy_delta_mm > 5 or abs(z_delta_mm) > 5).lower(),
            "analysis_only_do_not_execute": "true",
            "replay_validated": "false",
        })

    with CANDIDATES.open("w", newline="", encoding="utf-8") as stream:
        writer = csv.DictWriter(stream, fieldnames=list(output[0]))
        writer.writeheader()
        writer.writerows(output)

    flagged = [item for item in output if item["large_difference_over_5_mm"] == "true"]
    report = [
        "# Hanoi Pose Geometry Analysis",
        "",
        "September 30, 2026. Analysis of 24 hand-taught source-approach poses. No fitted coordinate has been validated on the robot.",
        "",
        f"Raw source: `data/hanoi_teaching/hanoi_poses_2026-09-29.csv` (SHA-256 `{sha256(SOURCE)}`).",
        "An exact snapshot is `data/hanoi_teaching/hanoi_poses_2026-09-29_raw_snapshot.csv`.",
        "Derived review table: `data/hanoi_teaching/hanoi_pose_geometry_candidates_2026-09-30.csv`.",
        "Visual comparison: [raw captures and fitted geometry](../docs/figures/hanoi_pose_geometry_2026-09-30.png).",
        "",
        "## Geometry Model",
        "",
        "For each peg, the median x and y of its six captures define its measured center. Those four centers are projected onto one best-fit straight line; measured spacing along that line is retained. For each location, the median z of its four captures gives a shared level. These are descriptive fits, not calibrated motion targets. The fit does not infer any clearance, grasp, release, or retreat pose.",
        "",
        f"A straight-line fit to the six shared height medians suggests a vertical step of {z_pitch * 1000:.2f} mm per location. The maximum height-median deviation from that equal-step model is {max(abs(heights[loc] - (z_base + z_pitch * (loc - 1))) for loc in locations) * 1000:.2f} mm. The review table uses the per-level medians and does not impose equal spacing.",
        "",
        "| Peg | Median x m | Median y m | Line fitted x m | Line fitted y m | Center off line mm |",
        "| --- | ---: | ---: | ---: | ---: | ---: |",
    ]
    for peg in pegs:
        x, y = peg_centers[peg]
        x_fit, y_fit = projected[peg]
        report.append(f"| {peg} | {x:.6f} | {y:.6f} | {x_fit:.6f} | {y_fit:.6f} | {1000 * math.hypot(x - x_fit, y - y_fit):.2f} |")
    report.extend(["", "| Location | Shared median z m | Equal-step fitted z m |", "| --- | ---: | ---: |"])
    for location in locations:
        report.append(f"| {location} | {heights[location]:.6f} | {z_base + z_pitch * (location - 1):.6f} |")
    report.extend([
        "",
        "## Largest Differences",
        "",
        f"{len(flagged)} of {len(output)} captures differ from the fitted XY center or shared height by more than 5 mm. This threshold marks points to recheck; it is not a robot tolerance. All captures still need path and fixture validation.",
        "",
        "| Peg | Location | XY difference mm | Signed Z difference mm |",
        "| --- | ---: | ---: | ---: |",
    ])
    for item in sorted(flagged, key=lambda item: max(float(item["raw_minus_fit_xy_mm"]), abs(float(item["raw_minus_fit_z_mm"]))), reverse=True):
        report.append(f'| {item["peg"]} | {item["location"]} | {item["raw_minus_fit_xy_mm"]} | {item["raw_minus_fit_z_mm"]} |')
    report.extend([
        "",
        "## Wrist Consistency",
        "",
        "Wrist joint values are examined for trends with height only. They are not averaged into new joint targets. The fitted Cartesian positions cannot be paired with the recorded joint angles or quaternions as an executable pose.",
        "",
        "| Joint | Peg | Slope rad per location | Maximum deviation from a linear trend rad |",
        "| --- | ---: | ---: | ---: |",
    ])
    for joint in ("wrist_1", "wrist_2", "wrist_3"):
        for peg, slope, residual in summarize_joint(records, joint):
            report.append(f"| {joint} | {peg} | {slope:.4f} | {residual:.4f} |")
    report.extend([
        "",
        "## Lab Check Before Motion",
        "",
        "Confirm the active TCP and base frame against the pendant. Re-teach large-difference points and a separate post-clearance waypoint. Check jaw alignment, vertical lift along each post, clearance over the tallest stack, and every interpolated segment with the robot under supervision. Keep any accepted calibrated targets separate from this raw export and this analysis table. Record the physical peg mapping to solver A, B, C, and Queue before sending any solution move to the arm.",
        "",
    ])
    REPORT.write_text("\n".join(report), encoding="utf-8")
    print(f"Reviewed {len(records)} poses; {len(flagged)} flagged above 5 mm; height step {z_pitch * 1000:.2f} mm")
    print(f"Wrote {CANDIDATES.relative_to(ROOT)} and {REPORT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
