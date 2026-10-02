# Hanoi lab preflight — September 30, 2026

## New material reviewed

Reviewed the new demo-readiness plan, raw and derived pose geometry, revised Sodhi paper notes, and Hanoi solver changes. No newer top-level Downloads files were found after September 29 at 6 p.m. Eastern. Initialized only the Hanoi-Algorithms submodule at its recorded commit `1f85ec19309030165f390a6128983307f2fccf4e`.

The pose table contains 24 measurements: four posts and six levels per post. Original records and the raw snapshot remain unchanged. Fitted geometry remains analysis only.

## Luke's clarification

Luke confirmed today that the open jaws were at the actual disk grasp/release height for yesterday's captures, and that the jaws can lift a disk completely above the post. The original `source_approach` labels therefore do not describe the intended height accurately. This clarification does not establish endpoint accuracy or validate a trajectory. Preserve the recorded labels and values; explicitly identify selected grasp/release targets in the eventual motion configuration.

Dedicated clearance poses are still needed. A lateral transfer must begin only after the held disk clears its source post, then descend along the destination post. Do not infer location 7 or assume location 6 is sufficient clearance.

## Robot interface recovery

- The existing driver again reported `Background reading is not running` while ROS and V8 continued receiving samples. Receive timestamps alone were misleading.
- Before restarting, direct robot dashboard checks reported Normal, robot mode Running, program not running, and `STOPPED null`. V8 was inactive. Robot serial reported `2016352526` at `192.168.0.149`.
- Extracted factory calibration with the installed `ur_calibration` tool and saved it on the Pi and locally at `audit/calibration/ur5_factory_2026-09-30.yaml`. Its hash is `calib_17575711881469972235`.
- Terminated the identified old UR driver process group, verified its members, and relaunched with the extracted calibration and `activate_joint_controller:=false`.
- New Pi driver PID: `16800`; log: `/home/seeker/v8_logs/ur_driver_hanoi_20260930.log`. Startup negotiated RTDE protocol 2 at 125 Hz. No background-reading failure or calibration mismatch was found in the inspected new log.
- Controller listing confirms passthrough and other arm motion controllers are inactive. No arm motion, gripper command, or dashboard Play command was sent during this preflight.
- Read-only helper status at 14:33:26 UTC returned zero joint velocities, TCP frame `base`, XYZ approximately **(-85.35, -358.24, 914.65) mm**, and tool outputs 16 and 17 both off. Compare these coordinates with the pendant's base-frame active TCP before teaching or executing. The active TCP and physical jaw state still require operator confirmation.
- Pi diagnostic record: `audit/hanoi_preflight_2026-09-30.jsonl`.

## Logical job preparation

Added `v8/scripts/hanoi_plan.py`, which runs the existing solver and validates its result without any robot-control imports or commands. The default three-disk plan contains seven one-disk jobs from A to C; physical post mapping is deliberately unset pending Luke's fixture mapping. Queue and Ground are excluded.

Saved plan: `audit/hanoi_logical_plan_2026-09-30.json`. Checks passed for seven jobs and rejection of wrong top disks, illegal stacks, Ground pickup, unmapped Queue, and overwriting an existing output. The bundled Python has no pytest; the relevant assertions were run directly.

Updated capture documentation to match the already implemented four-post range.

## Awaiting lab choices

Confirm today's deadline and required physical result, current disk arrangement and post mapping, pendant TCP/tool settings, and the exact source and destination for the first supervised transfer. Then capture the missing clearance poses, establish the path and gripper sequence, and validate one complete physical transfer before attempting additional jobs.

## Subsequent fixture and hardware checks

- Luke reports all six disks on peg 4, positions 1–6. Peg 4 is an additional usable post, originally intended to help resolve illegal stacks. Disk sizes/order are not established by this report. The default three-disk logical example is therefore not today's physical initial state.
- Proposed first physical job: transfer the top disk from peg 4, level 6, to peg 3, level 1, conditional on peg 3 being empty. A complete solver run is not yet the agreed physical milestone.
- Direct read-only secondary interface on port 30012 returned three successive robot-state packets with advancing controller timestamps. Active TCP offset is `[0.08573, 0.08573, 0.1651, 0, 0, 0]` (translation metres, rotation vector radians). The robot reports connected, enabled, powered on, no emergency/protective stop, and no running/paused program.
- Added `v8/scripts/hanoi_hardware_state.py` and integrated its check into the teaching helper. Capture/status/gripper preparation now rejects nonadvancing direct hardware timestamps, direct motion above the stationary threshold, ROS-to-hardware joint disagreement over 0.005 rad, or TCP translation disagreement over 2 mm. These thresholds detect inconsistent feedback; they are not grasp accuracy or trajectory tolerances.
- Copied both helpers to the Pi and ran read-only status successfully. Direct hardware and ROS positions agreed, with reported zero joint velocities. No jaw or arm command was issued.
- Asked Luke to compare the pendant's Base-feature Tool Position and TCP Configuration before proceeding. Reading a configured TCP offset does not establish that it represents the physical jaw grasp point accurately.

Protocol reference: [Universal Robots primary/secondary interface documentation](https://docs.universal-robots.com/tutorials/communication-protocol-tutorials/primary-secondary-guide.html).

## Pendant confirmation and calibrated planner

- Luke confirmed pendant Feature `Base`, tool `TCP_2`, Tool Position `(-85.35, -358.24, 914.65)` mm, and peg 3 empty. He could not locate Installation and noted the configured TCP might not lie exactly at the jaw tips. No tool setting was changed.
- The recorded joint poses remain usable as taught physical configurations without redefining the tool origin. Straight translation with fixed orientation preserves the translation of every point rigidly attached to the gripper. Collision clearance must account for the jaws and held disk, not just the configured TCP.
- Added `v8/scripts/hanoi_planner.launch.py`: calibrated UR5 model with MoveIt planning services and `allow_trajectory_execution: false`. Pi planning launch PID `17608`, log `/home/seeker/v8_logs/hanoi_planner_20260930.log`. Fixture, gripper and disk collision geometry have not been added; planner self-collision checks alone do not validate fixture clearance.
- Added and ran `v8/scripts/hanoi_check_poses.py`. It computes model `tool0` forward kinematics, applies the directly read active TCP offset, and compares against controller/taught poses in `base`. Live residual was 0.0065 mm. Recorded source `peg4_location6_source_approach` residual was 0.0357 mm; destination `peg3_location1_source_approach` residual was 0.0366 mm. Orientation residuals were under 0.0001 rad. This establishes numerical consistency of model, frames and current tool offset, not physical grasp precision or replay validation.
- Asked Luke to teach an empty-gripper source clearance above peg 4, aligned with the level-6 grasp position and retaining grasp orientation, accounting for the bottom of the held disk clearing the post. Awaiting “source clearance ready” before capturing.

## Source clearance capture

- Luke positioned the gripper above post 4 and reported clearance for movement between all posts. Captured `peg4_location6_clearance` at `2026-09-30T14:51:46.468056+00:00`; synced raw records and regenerated CSV on both machines. There are now 25 poses. The location-6 identifier links the clearance role to the source grasp; it is not a claim that stack level 6 clears the post.
- Raw clearance TCP in `base`: `(0.3476976166359411, 0.5929177600038604, 0.7725834435612121)` m. Compared with the source grasp, height increased 108.18 mm, XY shifted 23.28 mm, and orientation changed 8.25 degrees. A direct interpolation to that raw pose would not be a straight vertical lift.
- Added `v8/scripts/hanoi_plan_lift.py` to derive a separate candidate retaining raw grasp XY/orientation and using the taught clearance Z, then calculate new joint samples through the calibrated Cartesian planner. It never executes and preserves original records.
- Source candidate planned completely (`fraction=1.0`), with 12 joint samples and maximum adjacent joint change 0.04905 rad. Saved on both machines as `audit/hanoi_peg4_lift_candidate_2026-09-30.json`. This is a planning result only: fixture/held-disk collision geometry, execution timing, and physical path validation remain outstanding. No arm or gripper command was sent.
- Next teaching step: destination clearance above empty peg 3, followed by planning and reviewing the complete first-transfer path.

## Clearance labels on all posts

- Luke independently captured `(3,7)`, `(2,7)`, and `(1,7)` as clearance above each post. All three are present in the Pi and local raw logs, with direct hardware checks. There are now 28 poses, synced on both machines.
- Existing names are `peg3_location7_source_approach`, `peg2_location7_source_approach`, and `peg1_location7_source_approach`. Preserve these raw records; Luke's clarification establishes their clearance role. This supersedes the earlier naming restriction against location 7: it is now an explicitly taught clearance label, not a seventh disk slot or an extrapolated pose.
- Clearance TCP Z: peg 3 0.7520509710098673 m; peg 2 0.7506379955035825 m; peg 1 0.7480034790950038 m. Peg 4's earlier clearance remains `peg4_location6_clearance`, Z 0.7725834435612121 m.
- Preserved Luke's change permitting location 7 in `capture_hanoi.ps1`; added automatic role `clearance` for future location-7 captures and rejection of explicitly conflicting roles. Updated capture documentation accordingly.
- The initial peg 3 Cartesian lift computation completed but its default time parameterization compressed the 295 mm lift into about 1.8 seconds; a 0.0829 rad change between returned 0.1-second samples exceeded the candidate guard. Refining the geometric step alone did not change this timing/resampling behavior. No candidate was accepted or executed.
- Updated the planning-only launch with conservative joint planning limits (0.06 rad/s, 0.06 rad/s²), and disabled the Move/Execute action capabilities in addition to `allow_trajectory_execution: false`. Restarted only the identified planner; new launch PID `19198`, log `/home/seeker/v8_logs/hanoi_planner_slow_20260930.log`. Planning services are present. Subsequent peg 3 planning calls timed out at both 15 and 45 seconds. This remains unresolved and does not justify motion.

## First physical test: peg 4 level 6 to peg 1 level 1

- Luke explicitly requested this transfer and confirmed gripper/peg 1 empty, freedrive released, hands/tools clear, and presence at the pendant to stop the test.
- Restoring the Move action capability while retaining `allow_trajectory_execution: false` restored responding Cartesian services. The standalone Execute capability remains disabled. Peg 1's slow lift plan completed with 134 samples and maximum adjacent joint change 0.0060 rad.
- Added calibrated URDF forward-kinematics helper and one-job runner: `v8/scripts/hanoi_kinematics.py` and `v8/scripts/hanoi_single_transfer.py`. All arm goals use the passthrough controller; no p0 is sent. The runner plans each segment, validates sampled vertical XY/orientation and clearance travel, scales timing by two, monitors Nano/Dashboard/direct hardware state, checks endpoints, records events, cancels on interruption, and stops the robot program when exiting. Pick and transfer are separate supervised stages; physical grasp confirmation is required before transfer, and attempted stages cannot automatically replay.
- Planned all seven segments from the current peg 1 clearance position. File: `audit/hanoi_transfer_4_6_to_1_1_20260930.json`. Planned vertical XY residuals were under 0.003 mm; this is numerical model consistency, not measured physical accuracy. Fixture/gripper/disk collision geometry is still absent.
- With no pendant program loaded, restarted the identified UR driver in headless mode, motion controller initially inactive, using the same calibration. Driver PID `20295`; Pi log `/home/seeker/v8_logs/ur_driver_hanoi_headless_20260930.log`. The ROS control program started and the active TCP offset stayed unchanged.
- Pick attempt began at 15:28:39 UTC. Open outputs acknowledged at 15:28:41. The initial vertical rise completed at 15:28:46, and travel above peg 4 completed at 15:29:18. Descent to source started at 15:29:18 with planned duration 11.505 s.
- At 15:29:28 the runner detected a changed safety mode, cancelled its trajectory, and sent dashboard Stop. The driver log identifies `ROBOT_EMERGENCY_STOP` followed by power-off transitions. It subsequently reported Normal and Idle. **Source descent did not complete; Close was never sent; no disk transfer occurred.** No stop reset/rearm/brake-release command was issued by this runner.
- Read-only status afterward: Normal, Idle, program stopped, no emergency/protective flag currently set, zero velocities, Nano fresh/D12 high. TCP at that check approximately `(358.885, 579.819, 661.573)` mm. Cause of the emergency stop is not yet established; Luke was asked about contact, unexpected movement, pendant warnings, and whether he pressed Stop/changed power or brakes. No further motion is authorized by a successful-test claim.
- Event record copied locally: `audit/hanoi_transfer_4_6_to_1_1_20260930.events.jsonl`. Improve future errors to include the exact dashboard safety response instead of a generic message.

Headless control reference: [Universal Robots ROS 2 driver startup](https://docs.universal-robots.com/Universal_Robots_ROS2_Documentation/doc/ur_robot_driver/ur_robot_driver/doc/usage/startup.html).

## Operator correction: horizontal pickup entry required

- Luke confirmed the arm moved to the target and that **he pressed E-stop** because the pickup procedure was wrong. An open gripper cannot descend directly onto the piece. It must move outside the stack to the desired level, enter horizontally toward the peg, close, then lift straight up.
- The stopped test is therefore a procedure error, not evidence of a Nano trigger or unexplained automatic emergency stop. The earlier planned top-down source descent is superseded and must not be replayed.
- Revised source route: high travel above an outside entry point; vertical descent beside the stack; horizontal insertion at the grasp height with fixed orientation; close; vertical lift clear of the post. Requested a new empty-gripper `peg4_location6_pickup_entry` capture from Luke. The new candidate will retain the taught entry XY, source grasp Z/orientation, and compute fresh IK; original capture values will stay intact.
- Added `pickup_entry` and `place_withdrawal` capture roles. The one-job runner now requires the entry capture and explicitly rejects old top-down plans. Horizontal insertion gets a sampled height/orientation check; closure occurs only after insertion completes.
- Asked Luke to confirm destination handling: descending with the held disk onto peg 1, opening, and withdrawing sideways. Destination withdrawal remains to be defined before calling the corrected full job ready. No further motion or E-stop reset was sent.

## Peg 8 approach group and placement withdrawal

- Luke taught label 8 as the approach group for physical peg 4. Seven new raw records are present: levels 1–6, with two records labelled level 4. There are now 35 poses, synced. The second level-4 record is near the separately captured level-5 pose; preserve this duplicate and review it before future level-4 use. The current level-6 approach is unique.
- `peg8_location6_source_approach` is 31.31 mm away in XY from peg 4's level-6 grasp, 1.260 mm higher, with a 2.939-degree orientation difference. The runner accepts this capture as the pickup entry. It records the mapping and derives entry Z/orientation from the actual grasp while retaining raw approach XY, then recomputes the Cartesian path and joints.
- Preserved Luke's capture range expansion to 1–8 and updated documentation. Label 8 is an approach group, not a physical disk post; future level-1–6 captures for label 8 default to `pickup_entry`. Other extra labels are not yet mapped for execution.
- Luke confirmed placement requires sideways withdrawal. Updated the route to lower the held disk, open, withdraw horizontally, then rise outside the stack. Requested a taught `peg1_location1_place_withdrawal` point. The runner refuses a full plan or execution that lacks horizontal withdrawal.
- No new arm/gripper commands were sent after the stopped attempt.

## Complete side-approach data and corrected plan

- Luke supplied side points for every physical peg using label `physical peg + 4`, matching the same numbered level: 5→1, 6→2, 7→3, 8→4. All 53 pose records are synced. There are 24 physical grasp/place heights, four taught clearance records, and 25 side records including the preserved duplicate at label 8 level 4.
- No extra withdrawal teaching is needed for this job: `peg5_location1_source_approach` supplies the side withdrawal of physical peg 1 at level 1. Updated runner mapping and documentation, and changed future label-5–8 captures to the shared `side_approach` role. Prior raw labels stay unchanged.
- Completed the corrected nine-segment plan at 16:10:19 UTC: rise outside the current post, travel above source side entry, descend outside source, insert horizontally, lift vertically after closure, travel at clearance, descend onto destination, withdraw horizontally after opening, then rise outside destination.
- New file: `audit/hanoi_transfer_4_6_to_1_1_v2_20260930.json`, copied locally. All Cartesian paths completed and sampled constraints passed; vertical XY residuals remain below 0.003 mm in the model. Side-point Z/orientation are derived from their corresponding grasp/place target so insertion/withdrawal stays level with fixed orientation; their raw values are preserved. This is not yet physical validation.
- Asked Luke to confirm the +4 mapping and current readiness: gripper/peg 1 empty, all six disks on peg 4, freedrive released, hands/tools clear, presence at pendant, and current gripper position. Awaiting readiness before any corrected physical attempt.

## Corrected physical pickup stage

- Luke confirmed matching levels, gripper empty, all disks on peg 4, and current gripper position `(7,6)`. Continued the previously authorized one-job test.
- Initial corrected startup at 16:17:42 UTC failed before any jaw command or trajectory. The driver had automatically restored the passthrough controller when the ROS program restarted, so requesting activation again with strict switching was rejected. Updated startup to read controller states, accept a verified already-active passthrough controller, reject competing arm controllers, and verify readback if activation races automatic restoration. Preflight-only failure history may be retried; any logged gripper or trajectory attempt still blocks pickup replay.
- Corrected pickup began at 16:19:48 UTC. Controller ready at 16:19:51; OPEN acknowledged at 16:19:53. Rise completed 16:20:05; travel above side entry completed 16:20:16; descent **beside** the stack completed 16:20:30; horizontal insertion completed 16:20:35; CLOSE output acknowledged 16:20:37. The robot program then stopped normally at the grasp position.
- All motion segments returned success and passed direct hardware endpoint checks. No lift or transfer has been sent yet. Close acknowledgement is not grasp sensing: asked Luke to confirm the disk is seated correctly in the jaws and the lifting path is clear before proceeding.
- Future segment-completion events now record the verified actual joints and direct TCP pose as well as controller success, so transfer/release endpoints are retained.

## Lift, transfer, release and sideways retreat

- Luke explicitly confirmed “disk is seated lift and transfer.” Started the transfer stage at 16:26:14 UTC with `--grasp-confirmed`; the robot control program was restarted and the passthrough controller readback confirmed active.
- Straight lift completed at 16:26:29; travel above peg 1 completed 16:27:02; descent to peg 1 level 1 completed 16:27:32; OPEN output acknowledged 16:27:34; sideways withdrawal completed 16:27:39; final rise outside the post completed 16:28:10. All five trajectory actions succeeded, and each endpoint passed the direct hardware check before continuing.
- Final program Stop was acknowledged at 16:28:10.107980 UTC. The full corrected nine-segment motion sequence is complete. No next job was admitted or queued.
- Final direct TCP from the verified retreat endpoint: approximately `(585.506, 264.102, 772.568)` mm in `base`. This is the raised withdrawal position beside peg 1, not the source or a pose over peg 4.
- Asked Luke to confirm the physical result: one disk correctly resting on peg 1, five remaining on peg 4, gripper empty/open. Motion/gripper acknowledgements establish command completion; physical placement remains pending operator confirmation.
- Complete event record copied to `audit/hanoi_transfer_4_6_to_1_1_v2_20260930.events.jsonl`. Initial failed top-down procedure and controller preflight failure remain in their original records; they are not counted as successful transfers.

## Physical placement failed; pickup-only recovery

- Luke reported that the destination descent missed the target and explicitly answered that placement needs correction. **The v2 run is a completed command sequence with unsuccessful physical placement, not a successful disk transfer.** Cause is not yet quantified. The original peg 1 level-1 taught target must not be reused as a validated placement target.
- Luke asked to pick the disk back up at `(4,6)` so he can align it over peg A using freedrive. He confirmed the disk was back on peg 4 level 6, gripper empty, freedrive released and path clear, with him at the pendant.
- Added pickup-only planning and a separate source-lift command. Pickup-only plans omit destination motion and explicitly refuse transfer. New full-transfer plans require a newly taught `peg1_location1_place` capture; legacy destination descent is rejected. Source approach/grasp data that worked remain unchanged.
- New recovery plan: `audit/hanoi_pickup_only_4_6_v3_20260930.json`. It has source side travel, descent outside the stack, horizontal insertion, and an optional source lift. Only the pickup stage has been requested for execution before Luke's manual teaching; no destination command will be sent.
- Recovery pickup started 16:33:30 UTC; controller readback ready 16:33:33. Source side travel completed 16:34:11, descent beside the stack 16:34:24, horizontal insertion 16:34:30, and CLOSE acknowledged 16:34:31. The robot program stopped normally at the grasp position. No source lift or destination motion was sent in recovery.
- Recovery plan and full event record copied locally. Luke will visually check seating, then use freedrive to lift straight clear of the source post and align the held disk over peg A. A newly aligned clearance pose and properly seated placement pose remain to be recorded before another automatic descent.
