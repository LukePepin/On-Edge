# Capture Hanoi poses

Use Windows PowerShell from `C:\Users\lukep\Documents\Projects\On-Edge`.
Teach the pose in freedrive, then stop moving before running:

```powershell
.\v8\scripts\capture_hanoi.ps1 1 5
```

The two numbers are peg and location. Pegs are 1–3, locations 1–6.
The default pose role is `source_approach`, matching the first four captures.
For a different role:

```powershell
.\v8\scripts\capture_hanoi.ps1 1 1 -Role pickup
```

Supported roles: `source_approach`, `pickup`, `clearance`, `destination_approach`,
`place`, `retreat`, `home`. Location 6 is not established as post clearance.
No location 7 is inferred or generated.

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
Capture checks reject moving, missing, or stale incoming telemetry. The earlier
driver failure demonstrated that fresh ROS timestamps alone cannot establish
fresh hardware feedback; compare the first taught pose against the pendant.
