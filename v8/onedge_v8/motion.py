"""Motion program 'pick_place_v1' reused from src/sentry_logic/sentry_logic/stream_wrist_kinematics.py.

Same waypoints (degrees, canonical joint order), shortest-path angle normalization, and
two-phase structure: phase 1 approaches 'Pick'; phase 2 sweeps Pick -> Transfer -> Place ->
Transfer -> Pick over 10 s. Velocities are left unspecified so the controller interpolates.

Difference from the historical node: injection is no longer fired 0.5 s after the phase-2
goal is sent. The runner waits for fresh telemetry to confirm the arm is moving first.
"""
from __future__ import annotations

import math

from .telemetry import CANONICAL_JOINTS

POSES_DEG = {
    "Pick": [39.71, -98.55, -97.62, -64.90, -264.58, -280.20],
    "Transfer": [7.19, -80.56, -76.40, -64.90, -264.58, -280.20],
    "Place": [-18.46, -107.23, -101.08, -56.55, -269.20, -204.20],
}
POSES_RAD = {k: [math.radians(d) for d in v] for k, v in POSES_DEG.items()}
PHASE2_SEQUENCE = [("Pick", 1.0), ("Transfer", 3.0), ("Place", 5.0), ("Transfer", 7.0), ("Pick", 10.0)]
SWEEP_S = 10.0
JOINT_NAMES = list(CANONICAL_JOINTS)


def normalize_target(current_rad: float, target_rad: float) -> float:
    diff = (target_rad - current_rad + math.pi) % (2 * math.pi) - math.pi
    return current_rad + diff


def normalized_pose(current: list, pose: str) -> list:
    return [normalize_target(c, t) for c, t in zip(current, POSES_RAD[pose])]


def phase1_points(current: list, approach_s: float = 5.0, time_scale: float = 1.0) -> list:
    return [(normalized_pose(current, "Pick"), approach_s * time_scale)]


def phase2_points(current: list, time_scale: float = 1.0) -> list:
    return [(normalized_pose(current, pose), t * time_scale) for pose, t in PHASE2_SEQUENCE]
