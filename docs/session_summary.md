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

## What We Plan To Do Tomorrow

Tomorrow, we will merge the cryptography from Phase 2 into the physical robot from Phase 3. 

### 1. Windows WSL Port Forwarding (The Cloud Supervisor)
Before we write any robotic control code, we must get your Windows PC talking natively to the UR5. 
- Because WSL operates in a hidden Virtual Machine, the UR5's TCP traffic is bouncing off the Windows firewall. 
- We will write a custom PowerShell script using `netsh portproxy` to dynamically grab your WSL instance's IP address and bore a tunnel straight through Windows on ports `50001-50004`. 
- This will allow you to launch heavy 3D tools like RViz and MoveIt 2 directly from your PC.

### 2. The Cryptographic E-Stop (Phase 3.3 & 3.4)
> [!CAUTION]
> **PHYSICAL SAFETY REMINDER:** Before we begin this phase, you MUST physically unmount the robot from your desk and move it to the center of the room. We will be commanding the robot at high speeds, and it must have a full 360-degree range of motion completely clear of obstacles!

Once the network is solid and the robot is moved, we will build the final safety system:
- We will map the Arduino's EWMA Trust Score into the ROS 2 environment.
- We will write a node that monitors that score. If the ZKP overhead exceeds 500ms and the score drops below 30, the ROS 2 environment will instantly issue a priority `HALT` command to the UR5 trajectory controller.
- Finally, we will run the UR5 at high speeds, force a cryptographic failure, and measure the physical deceleration curve to prove the entire software-to-hardware pipeline stops the robot within the ISO 13849-1 500ms safety standard.
