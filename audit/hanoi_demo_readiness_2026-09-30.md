# Hanoi Demonstration Readiness

September 30, 2026. This is a working plan for the 11:00 a.m. demonstration, not a lab handoff or evidence that the full physical sequence has run.

## Current State

- `Hanoi-Algorithms` is a separate local Git repository. On branch `codex/hanoi-demo-prep`, the solver returns the correct seven moves for the standard three-disk setup. The Streamlit dashboard can solve, display status, step through every move, and export a checked logical job plan. The export does not move the robot. Its working state editor uses explicit move controls; direct graphical drag-and-drop is not yet connected to Python state.
- On-Edge has 24 recorded `source_approach` poses, six levels on each of four posts. They are raw and not replay validated. No pickup, clearance, place, or retreat waypoint has yet been established by these records.
- [Pose geometry analysis](hanoi_pose_geometry_2026-09-30.md) estimates a 41.14 mm vertical step. Fifteen of the 24 captures differ from the straight-post/shared-level fit by more than 5 mm. Post 2, level 4 differs by 22.88 mm in XY. The derived CSV is for reviewing and re-teaching points; it is not a motion input.
- The current On-Edge V8 robot code controls an arm trajectory for the earlier timing study; the separate Hanoi solver has no robot-control connection. The gripper helper confirms output changes while stationary but does not command arm motion.

## Start With the Repeatable Software Path

From the local `Hanoi-Algorithms` directory, run the dashboard with its local environment:

```powershell
.\.venv\Scripts\python.exe -m streamlit run app.py
```

The standard initial state is `[[3, 2, 1], [], [], [], []]`, target C. Press Solve. The displayed result should have seven moves. Step through all seven to reach ` [[], [], [3, 2, 1], [], []] `. Open Robot Job Plan Preview to see the checked logical sequence and download it. The plan is planning only, with no robot commands or approved trajectories.

The current dashboard also offers improper states and additional solver rules for a separate software demonstration. Label those demonstrations as simulated until every corresponding physical move has an explicit, validated procedure.

## Lab Work Between 8 and 11 a m

1. Confirm the real peg mapping to A, B, C, and possibly Queue, the disk count, active TCP, fixture setup, gripper state, robot program state, and that no earlier motion goal can resume. Check the first measured TCP against the pendant in the same frame.
2. Select the exact seven-move path and recheck only the posts and levels it uses. Review the largest fit disagreements in the geometry report. Do not substitute a fitted coordinate for a taught target without a supervised validation.
3. Teach and validate source pickup, straight lift above the post, clearance over the tallest stack, destination approach and release, and retreat. Location 6 has not been established as clearance; no location 7 is inferred.
4. Validate one grasp-transfer-release job with a real disk and physical placement confirmation. The robot trajectory between waypoints must be checked, not only the endpoints. Reconcile the object and stack state after any uncertain grasp or interrupted move.
5. Attempt the seven-job physical sequence only after the move runner, gripper commands, and every used motion segment have been validated with the lab operator. Record the initial state, each completed move, any intervention, and the final physical arrangement.
6. Keep the dashboard's complete simulated solution ready as the presentation fallback. If the physical sequence is incomplete, describe exactly which individual robot transfers were observed.

## Go or No Go for a Physical Full Solution

A full robot run requires a confirmed mapping from solver pegs to physical posts, validated waypoints and clearances for every used height, reliable gripper control, a robot runner that executes exactly one checked move at a time, and physical confirmation of each transfer. As of this note, the runner and full set of validated poses are missing. The lab session must establish them before a physical full-solution claim is made.
