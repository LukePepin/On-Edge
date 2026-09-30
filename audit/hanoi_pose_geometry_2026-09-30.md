# Hanoi Pose Geometry Analysis

September 30, 2026. Analysis of 24 hand-taught source-approach poses. No fitted coordinate has been validated on the robot.

Raw source: `data/hanoi_teaching/hanoi_poses_2026-09-29.csv` (SHA-256 `6fb4c3957161681c2546a8f4036898dccbfcb792a87e680c85baebbdd115193f`).
An exact snapshot is `data/hanoi_teaching/hanoi_poses_2026-09-29_raw_snapshot.csv`.
Derived review table: `data/hanoi_teaching/hanoi_pose_geometry_candidates_2026-09-30.csv`.
Visual comparison: [raw captures and fitted geometry](../docs/figures/hanoi_pose_geometry_2026-09-30.png).

## Geometry Model

For each peg, the median x and y of its six captures define its measured center. Those four centers are projected onto one best-fit straight line; measured spacing along that line is retained. For each location, the median z of its four captures gives a shared level. These are descriptive fits, not calibrated motion targets. The fit does not infer any clearance, grasp, release, or retreat pose.

A straight-line fit to the six shared height medians suggests a vertical step of 41.14 mm per location. The maximum height-median deviation from that equal-step model is 2.12 mm. The review table uses the per-level medians and does not impose equal spacing.

| Peg | Median x m | Median y m | Line fitted x m | Line fitted y m | Center off line mm |
| --- | ---: | ---: | ---: | ---: | ---: |
| 1 | 0.600669 | 0.292036 | 0.601552 | 0.292840 | 1.19 |
| 2 | 0.522925 | 0.382977 | 0.520989 | 0.381213 | 2.62 |
| 3 | 0.431562 | 0.476638 | 0.432892 | 0.477850 | 1.80 |
| 4 | 0.354747 | 0.564125 | 0.354471 | 0.563873 | 0.37 |

| Location | Shared median z m | Equal-step fitted z m |
| --- | ---: | ---: |
| 1 | 0.457598 | 0.459723 |
| 2 | 0.502724 | 0.500862 |
| 3 | 0.544094 | 0.542002 |
| 4 | 0.582079 | 0.583141 |
| 5 | 0.623302 | 0.624281 |
| 6 | 0.665632 | 0.665420 |

## Largest Differences

15 of 24 captures differ from the fitted XY center or shared height by more than 5 mm. This threshold marks points to recheck; it is not a robot tolerance. All captures still need path and fixture validation.

| Peg | Location | XY difference mm | Signed Z difference mm |
| --- | ---: | ---: | ---: |
| 2 | 4 | 22.88 | -1.14 |
| 4 | 4 | 11.36 | 0.76 |
| 2 | 2 | 11.16 | 0.04 |
| 3 | 6 | 11.11 | -1.49 |
| 4 | 3 | 10.91 | -2.86 |
| 4 | 6 | 10.19 | -1.23 |
| 1 | 3 | 10.11 | 0.41 |
| 3 | 2 | 8.85 | -0.04 |
| 4 | 5 | 8.79 | -1.10 |
| 4 | 1 | 8.51 | 0.74 |
| 1 | 1 | 3.42 | 8.49 |
| 4 | 2 | 7.74 | -3.33 |
| 2 | 1 | 6.84 | -1.88 |
| 3 | 5 | 6.27 | -3.92 |
| 2 | 6 | 6.16 | 1.23 |

## Wrist Consistency

Wrist joint values are examined for trends with height only. They are not averaged into new joint targets. The fitted Cartesian positions cannot be paired with the recorded joint angles or quaternions as an executable pose.

| Joint | Peg | Slope rad per location | Maximum deviation from a linear trend rad |
| --- | ---: | ---: | ---: |
| wrist_1 | 1 | -0.0651 | 0.0901 |
| wrist_1 | 2 | -0.1038 | 0.1930 |
| wrist_1 | 3 | -0.1106 | 0.0691 |
| wrist_1 | 4 | -0.1208 | 0.1211 |
| wrist_2 | 1 | -0.0078 | 0.0438 |
| wrist_2 | 2 | 0.0061 | 0.0880 |
| wrist_2 | 3 | -0.0085 | 0.0648 |
| wrist_2 | 4 | 0.0072 | 0.0565 |
| wrist_3 | 1 | 0.0225 | 0.0439 |
| wrist_3 | 2 | 0.0000 | 0.0000 |
| wrist_3 | 3 | 0.0094 | 0.0315 |
| wrist_3 | 4 | -0.0001 | 0.0001 |

## Lab Check Before Motion

Confirm the active TCP and base frame against the pendant. Re-teach large-difference points and a separate post-clearance waypoint. Check jaw alignment, vertical lift along each post, clearance over the tallest stack, and every interpolated segment with the robot under supervision. Keep any accepted calibrated targets separate from this raw export and this analysis table. Record the physical peg mapping to solver A, B, C, and Queue before sending any solution move to the arm.
