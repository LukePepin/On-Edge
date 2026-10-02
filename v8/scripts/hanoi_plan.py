#!/usr/bin/env python3
"""Generate checked logical Hanoi jobs. This command never controls the robot."""
import argparse
import json
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--disks", type=int, default=3)
    parser.add_argument("--target", choices=("A", "B", "C"), default="C")
    parser.add_argument("--initial", help="JSON stacks [A,B,C,Queue,Ground], bottom to top")
    parser.add_argument("--output", type=Path, help="Save a new JSON file; existing files are preserved")
    args = parser.parse_args()
    if not 1 <= args.disks <= 6:
        parser.error("--disks must be between 1 and 6")
    solver_dir = Path(__file__).resolve().parents[2] / "Hanoi-Algorithms"
    if not (solver_dir / "hanoi_final_flag.py").is_file():
        parser.error("Initialize the solver: git submodule update --init -- Hanoi-Algorithms")
    sys.path.insert(0, str(solver_dir))
    from hanoi.demo_plan import PlanError, build_logical_robot_plan
    from hanoi_final_flag import solve_hanoi

    try:
        initial = json.loads(args.initial) if args.initial else [list(range(args.disks, 0, -1)), [], [], [], []]
        # Validate the initial physical scope before calling the solver. Empty
        # moves intentionally fail final completion for an unsolved valid state.
        try:
            build_logical_robot_plan(initial, [], target_peg="ABC".index(args.target))
        except PlanError as exc:
            if str(exc) != "The move sequence does not finish with all disks on the target":
                raise
        flags = dict(target_peg="ABC".index(args.target), duplicate_strategy="discard",
                     ground_strategy="greedy_3", illegal_resolution="bfs_3peg")
        plan = build_logical_robot_plan(initial, solve_hanoi(initial, flags), target_peg=flags["target_peg"])
        plan["physical_post_mapping"] = None
        plan["mapping_note"] = "A/B/C must be mapped to confirmed lab posts before execution; Queue and Ground are excluded."
        text = json.dumps(plan, indent=2, allow_nan=False) + "\n"
        if args.output:
            with args.output.open("x", encoding="utf-8") as stream:
                stream.write(text)
            print(f"Saved {len(plan['jobs'])} logical jobs to {args.output}; no robot motion.")
        else:
            print(text, end="")
    except (PlanError, ValueError, TypeError, OSError) as exc:
        parser.error(str(exc))


if __name__ == "__main__":
    main()
