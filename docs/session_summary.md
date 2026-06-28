# Project Walkthrough: Session Summary

## What We Accomplished Today

Today was a massive turning point for the thesis. We successfully completed **Phase 2 (Cryptographic Profiling)** and officially broke ground on **Phase 3 (Physical Robotics)**.

### 1. The 64-Byte Threshold & The Central Limit Theorem
We started by running rigorous profiling sweeps on the Arduino Nano 33 BLE to see how long it takes to process simulated Zero-Knowledge Proof (ZKP) attributes of varying payload sizes.
- We discovered that a **128-byte** or **256-byte** payload consistently breached the 500ms safety limit. This crashed the simulated node's performance metric and triggered an immediate EWMA Trust Score eviction.
- We theorized that a **64-byte** payload might also fail if it suffered from random algorithmic complexity. However, by rolling independent complexity values for *each individual byte* in the payload, we invoked the **Central Limit Theorem**. 
- The computational variance perfectly averaged out. The 64-byte payload execution time stabilized tightly around `325ms`. Because it consistently stayed under 500ms, its Trust Score hovered safely around `51` and it **never** got evicted.
- *Conclusion:* While we cannot definitively call 64-bytes "mathematically proven" (since we are profiling raw execution time rather than true cryptographic verification time, and real-world network latency must be accounted for), we can conclude that **64-Bytes is the largest payload execution we can currently stabilize with our specific thesis safety goals.**

### 2. UR5 ROS 2 Driver Network Bridge
We transitioned to the physical robotics lab to prepare for the hardware integration phase.
- We wrote a unified installation script (`scripts/setup_ur5_ros2.sh`) to install the `Universal_Robots_ROS2_Driver` and `MoveIt 2` onto our ROS 2 environments.
- We discovered a WSL2 virtualization firewall issue on the Windows PC, so we pivoted to our Raspberry Pi 4 (Edge Supervisor), which natively sits on the local WiFi.
- We configured the **External Control URCap** on the UR5 Teach Pendant, pointed it to the Raspberry Pi's IP address (`192.168.0.149`), and successfully established the reverse TCP bridge.
- We verified the connection by putting the robot in Freedrive mode, moving the heavy shoulder and elbow joints by hand, and watching the Raspberry Pi stream the real-time kinematic telemetry on the `/joint_states` topic.

---

## What We Accomplished Today (June 28, 2026)

### 1. Arduino Trust Monitor Firmware
- Wrote the Phase 2 Zero-Knowledge Proof (ZKP) computation script for the Arduino Nano 33 BLE.
- Implemented the EWMA (Exponentially Weighted Moving Average) Trust Score algorithm natively on the Arduino to measure cryptographic execution delays.
- Verified that sending a >64 byte string to the Arduino simulates a malicious payload, instantly spiking the execution time to 550ms and tanking the trust score.

### 2. The Cryptographic E-Stop (Phase 3.4)
- Developed the ROS 2 bridge node (`trust_monitor_node.py`) to parse the JSON trust score from the Arduino over USB.
- Mapped the trust score directly to the UR5's trajectory controller. When the trust score dips below `30.0`, the Pi instantly injects a high-priority `stopj(5.0)` URScript command to physically E-Stop the UR5!

### 3. Trajectory Controller Interpolation Mathematics
- Encountered strict UR5 trajectory rejection issues when sending target points via ROS 2.
- Diagnosed and solved timestamp rejections by ensuring trajectories were commanded for immediate execution rather than past timestamps.
- Diagnosed and solved a mathematically unstable quintic spline explosion (a "whip-crack" effect where the robot requested 82.3 rad/s acceleration to satisfy a 0.0 velocity constraint over 15 seconds). Solved by dropping strict velocity boundaries and allowing the controller to calculate a natural spline.
- Successfully transitioned the Python script from a naive Topic publisher to a robust ROS 2 Action Server (`FollowJointTrajectory`).

---

## Strategic Pivots & Future Researcher Refresher

If you are a future researcher or agent joining this project, here is a critical refresher on the strategic pivots we have made to reach this point:

### 1. The Virtualization Pivot (WSL2 -> Native Pi)
- **Initial Attempt:** We initially tried to run the ROS 2 Cloud Supervisor on a Windows WSL2 instance.
- **The Pivot:** WSL2's internal NAT firewall proved completely unviable for real-time RTDE (Real-Time Data Exchange) UDP streams required by the `ur_robot_driver`. We fully abandoned WSL2 and commandeered a native Raspberry Pi 4 running Ubuntu 22.04 LTS to act as the Supervisor on the local network. 

### 2. The Micro-ROS Pivot (Agent -> Raw Serial)
- **Initial Attempt:** We attempted to run native Micro-ROS on the Arduino Nano 33 BLE.
- **The Pivot:** The Micro-ROS `rmw_microxrcedds` middleware completely exhausted the 256KB SRAM on the Nano 33 BLE when combined with our cryptographic libraries. We pivoted to a **Raw Serial JSON Bridge**. The Arduino now spits out lightweight JSON over USB, and a Python node (`trust_monitor_node.py`) on the Pi parses it and injects it into the ROS 2 DDS ecosystem.

### 3. The Trajectory Interpolation Pivot (Topic -> Action Server)
- **Initial Attempt:** We blindly published `JointTrajectory` messages to the `/scaled_joint_trajectory_controller/joint_trajectory` topic. The controller silently rejected them due to strict UR5 spline tolerances.
- **The Pivot:** We transitioned to the ROS 2 **Action Server** (`FollowJointTrajectory`). This forced a 2-way handshake that explicitly returned mathematical error codes. 
- **The Math Fix:** We discovered that forcing exactly `0.0` velocity boundary conditions over a 15-second gap without specifying accelerations caused a quintic spline explosion (the controller demanded 82 rad/s acceleration to satisfy the curve). By removing the strict `0.0` velocities and omitting a redundant `t=0` starting waypoint, the controller safely fell back to cubic interpolation and accepted the trajectory.

---

## Edge Node Development Workflow

Developing directly on the Raspberry Pi proved to be slow and fraught with compiler architecture mismatches (specifically, ARM64 vs ARM Cortex-M4 float ABI issues). The new, much more efficient workflow separates **development** from **execution**. You will do all the heavy lifting on your fast Windows PC, and use the Pi strictly for what it's good at: running the ROS 2 environment and communicating with the hardware.

### 1. Firmware Development & Compilation (Windows)
All Arduino code (the `edge_node` firmware) will be developed and compiled on your Windows PC.
*   **Why:** Windows has the correct pre-compiled libraries for the Cortex-M4 architecture and compiles much faster.
*   **Tools:** VS Code with PlatformIO (or Arduino IDE).
*   **Action:** Write your micro-ROS code, hit "Build", and compile the `firmware.bin` in seconds instead of minutes.

### 2. Firmware Flashing (Windows)
You will upload the compiled firmware to the Arduino Nano 33 BLE directly from Windows.
*   **Action:** Plug the Arduino into your PC, double-tap the reset button to enter bootloader mode, and use PlatformIO's "Upload" button (or the `bossac` command) to flash the board.

### 3. Hardware Deployment (Raspberry Pi)
Once flashed, the Arduino is completely self-sufficient.
*   **Action:** Unplug the Arduino from your PC and plug it into the Raspberry Pi via USB.

### 4. Supervisor & Network Management (Raspberry Pi via SSH)
The Pi's only job is to act as the micro-ROS supervisor and bridge the Arduino to the wider ROS 2 network.
*   **Action:** In an SSH session, you can run standard ROS 2 commands to verify the data is flowing. Code and flash on **Windows** -> Plug Arduino into **Pi** -> Run the Agent on **Pi via SSH**. 

---

## What We Plan To Do Next Session

1. Run the Arduino trust monitor and the UR5 wrist movement script simultaneously.
2. Physically test the E-Stop trigger by blasting the Arduino with a massive text string payload while the wrist is in motion, validating that the Trust Score drops and stops the robot.
3. Proceed to Phase 3.5: Record the deceleration telemetry into a CSV for the final thesis graphs.
