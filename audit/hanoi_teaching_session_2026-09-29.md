# Hanoi teaching session — September 29, 2026

## Agreed immediate goal

One runnable physical Hanoi transfer for September 30 at 11:00 a.m., accompanied by Luke's revised thesis proposal. Live signed delegation is not required for this demonstration. Fresh positions will be taught; the position arrays in the old `Hanoi_5_disks.txt` are not calibration for the reattached fixture.

## Setup and changes made

- Luke confirmed the arm stationary, gripper empty/clear, and old demo stopped before jaw testing. He subsequently confirmed the pendant showed Normal.
- Pi: `seeker@on-edge-pi.local`; checkout `/home/seeker/Documents/On-Edge`; robot `192.168.0.149`.
- The V8 campaign was actually PAUSED between trials, with three completed and no current attempt. Ended it through its campaign-abort API and preserved the completed session. No Nano configuration or safeguard rearm command was issued.
- The old UR driver was publishing old robot values while logging `Background reading is not running`. Its reported safeguard stop and repeated nonzero velocities disagreed with the robot's direct dashboard status (Normal, program stopped).
- Restarted the UR driver and removed its identified leftover processes. An intermediate driver startup stalled during controller loading and was stopped. The successful launch uses `activate_joint_controller:=false`: no arm motion controller was activated for teaching.
- Successful launch log on Pi: `/home/seeker/v8_logs/ur_driver_hanoi_20260929_175819.log`. The unchanged factory-calibration mismatch still needs resolution before relying on model-derived Cartesian motion.
- Created `v8/scripts/hanoi_teach.py` locally and copied it to the Pi. It has status, open, close, and named-capture commands. It does not send arm trajectories or change the Nano.
- Seven checks passed for stationary-window acceptance and rejection of stale, insufficient, gapped, moving, drifting, or nonfinite joint data. These are software checks, not a hardware safety certification.

## Observations

- 21:58:35 UTC: helper received a stationary sample with all six reported joint velocities zero. TCP source is `/tcp_pose_broadcaster/pose`, frame `base`; joint positions are recorded in radians. This was a diagnostic sample, not a taught waypoint.
- 21:58:49–50 UTC: OPEN request accepted; subsequent IO feedback reported output 16 on and 17 off.
- 22:01:53 UTC: OPEN resent at Luke's request and acknowledged. Luke confirmed the jaws were already fully open.
- 22:02:29 UTC: CLOSE sent at Luke's request and acknowledged; output 16 off and 17 on. Luke confirmed that the jaws closed.
- 22:03:07 UTC: OPEN sent to prepare for pose teaching and acknowledged; output 16 on and 17 off. Physical reopening remains to be observed.
- 22:05:57 UTC: captured `peg1_location1_source_approach` at Luke's identified position (1,1), taught in freedrive. All six reported joint velocities were zero. Raw TCP in `base`: x=0.5986395545054213 m, y=0.29463210467241446 m, z=0.46609303004799785 m. This is an approach pose, not a confirmed grasp or clearance pose.
- Capture log on Pi: `/home/seeker/Documents/On-Edge/data/hanoi_teaching/2026-09-29.jsonl`. It contains diagnostic failures as well as successful checks; errors are not poses.

## Luke's fixture and teaching notes

1. Each Hanoi stack is on a post. When removing a disk, lift it straight up along the post before lateral transfer. The post ends just above location 6, and location 7 is not feasible. **Location 6 is not established as sufficient clearance.** Measure and validate a separate clearance pose without inventing a location 7 or inferring a clearance height from this first approach pose.
2. All pose data are taught using freedrive. Small inconsistencies may need correction when building the motion sequence. Preserve original measured coordinates and orientations; store any later adjusted targets and the reason for each adjustment separately. Do not silently round, align, smooth, or substitute taught coordinates.

Requested pose export: `data/hanoi_teaching/hanoi_poses_2026-09-29.csv`. One pose per row, named joint angles/velocities, TCP position and quaternion, units in headers, peg/location/role, provenance, and both notes. Raw values remain unadjusted and replay is not yet validated.

## Capture protocol

Luke teaches each position with the pendant, stops moving, then identifies the position to capture. Record named waypoints for the chosen disk, source peg, destination peg, approach, grasp, lift/clearance, release, and retreat. Record the active TCP/tool offset and fixture reference with the session. A saved endpoint is not validation of the path connecting endpoints.

The helper appends captures without overwriting previous entries. Each record includes named joints, position/velocity, reported TCP pose and frame, tool outputs, timestamps, and a note. All captures begin with `replay_validated: false`.

Before accepting the first taught pose, compare its reported TCP with the pendant using the same base frame and active TCP. Fresh ROS receive timestamps alone do not prove that the hardware data source is updating; the driver failure above is direct evidence of that limitation.

## Next steps

1. OPEN state and physical CLOSE confirmed by Luke; reopening command acknowledged before teaching.
2. Choose one disk and two pegs; document tool/frame settings.
3. Teach and capture the required positions, one at a time.
4. Validate the transfer path and gripper sequence before calling it runnable.
