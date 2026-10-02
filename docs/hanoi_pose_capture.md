# Capture Hanoi poses

Use Windows PowerShell from `C:\Users\lukep\Documents\Projects\On-Edge`.
Teach the pose in freedrive, then stop moving before running:

```powershell
.\v8\scripts\capture_hanoi.ps1 1 5
```

The two numbers are peg and location. Pegs are 1–4. Locations 1–6 are disk
positions; location 7 is Luke's newly taught clearance label, not a seventh disk
position. Capturing location 7 automatically uses the `clearance` role.
The default pose role is `source_approach`, matching the first four captures.
Luke uses labels **5–8** for the side approach/withdrawal points of physical
pegs **1–4**, respectively: physical peg number plus four, at the same level.
These are waypoint groups, not additional disk posts. New label-5–8 captures
default to role `side_approach`; earlier `source_approach` or `pickup_entry`
records are preserved. For example `(8,6)` is beside peg 4's level-6 grasp;
`(5,1)` is beside peg 1's level-1 placement.
For a different role:

```powershell
.\v8\scripts\capture_hanoi.ps1 1 1 -Role pickup
```

Supported roles: `source_approach`, `pickup`, `pickup_entry`, `side_approach`, `clearance`,
`destination_approach`, `place`, `place_withdrawal`, `retreat`, `home`.
`pickup_entry` is beside the disk at grasp height for horizontal jaw insertion.
`place_withdrawal` is beside a released disk for horizontal jaw withdrawal.
Location 6 is not established as post clearance.
Clearance at location 7 must be physically taught; it is never inferred from
stack spacing. Earlier location-7 captures labelled `source_approach` remain
unchanged and are interpreted as clearance according to Luke's clarification.

Each command reads the current stationary pose, appends the full raw record on
the Pi, downloads the log, rebuilds and verifies the CSV, and copies the CSV back
to the Pi. It never commands the arm or gripper. Both fixture/freedrive notes are
included in the CSV. Repeated captures retain earlier records.

Files in `data/hanoi_teaching/`:

- `2026-09-29.jsonl`: raw poses, gripper events, and errors.
- `hanoi_poses_2026-09-29.csv`: all pose captures, with full recorded precision.

These commands continue the September 29 teaching session, even if run tomorrow.
The CSV retains each capture's actual UTC timestamp. Do not edit the generated
CSV to clean or align targets; store adjusted targets separately.

If capture succeeded but export or syncing failed, recover without another capture:

```powershell
.\v8\scripts\capture_hanoi.ps1 -SyncOnly
```

If PowerShell blocks scripts, use the one-command form:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File .\v8\scripts\capture_hanoi.ps1 1 5
```

The Pi must be reachable through existing SSH access, with its UR driver running
in localhost-only ROS mode. The exporter uses this Windows user's bundled Codex
Node runtime and spreadsheet library. It fails clearly if unavailable.
Capture checks reject moving, missing, or stale incoming telemetry. The helper
also reads the robot's read-only secondary interface, requires its controller
timestamp to advance, and compares direct joints/TCP translation with ROS values.
The earlier driver failure demonstrated that fresh ROS timestamps alone cannot
establish fresh hardware feedback. Compare the first taught pose against the
pendant and document the active tool setting.
