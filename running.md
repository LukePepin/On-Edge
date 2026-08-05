# On-Edge: Automated Testing Runbook

This guide contains the exact terminal commands required to execute the fractional factorial kinematic testing on the Raspberry Pi 4 supervisor.

## 1. Terminal 1: Repository Sync & Build
Before starting a testing session, ensure the Pi has the latest code and the ROS 2 workspace is built.
```bash
cd ~/Documents/On-Edge
git pull origin main
colcon build --packages-select sentry_logic
source install/setup.bash
```

## 2. Terminal 2: Physical UR5 Bridge
This terminal connects the ROS 2 environment to the physical UR5 controller via the RTDE interface. This bridge is insulated from the wireless jamming sweeps by the `ROS_LOCALHOST_ONLY=1` configuration.
```bash
cd ~/Documents/On-Edge
source install/setup.bash
ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5 robot_ip:=192.168.0.149
```
*Wait for the terminal to display `Robot ready to receive control commands.`*

## 3. Terminal 3: Test Execution
Use this terminal to run the automated factorial tests. The `run_test.sh` script dynamically sets up the 0-100% `iptables` jammer, spawns the 50Hz `joint_logger_node`, and executes the high-speed 10s spline array (`stream_wrist_kinematics.py`).

**Syntax:**
```bash
./scripts/run_test.sh --algo <ZKP|CLOUD> --nodes <INT> --loss <0|30|60|90> --iter <INT>
```

**Example 1: Baseline Cloud Run (0% Loss)**
```bash
./scripts/run_test.sh --algo CLOUD --nodes 2 --loss 0 --iter 1
```

**Example 2: ZKP Mesh Run (60% Loss, Alpha 0.5)**
```bash
./scripts/run_test.sh --algo ZKP --nodes 2 --loss 60 --iter 1 --alpha 0.5
```

*Note: The script takes exactly 48 seconds to run (15s for the trajectory + 3s spool up + 30s mechanical standstill buffer). Ensure you manually restart the external URCap program on the UR5 Teach Pendant between every run.*

---

## 4. Complete Inventory of Executed Scripts & Firmware

Before beginning the 54-run fractional factorial campaign, please manually verify the integrity and configuration of the following core files. 

### A. Arduino Firmware (Microcontroller Edge Node)
- **`firmware/unified_trust_monitor_template/unified_trust_monitor_template.ino`**
  *Purpose:* The single C++ firmware flashed to the Arduino. It parses the dynamic `{"algo": "ZKP", "alpha": 0.3}` JSON payload over USB serial, executes the corresponding cryptographic verification (ZKP or ECC), updates the EWMA trust score, and toggles the 24V PNP hardware safety optocoupler.

### B. Cloud Infrastructure (Windows PC)
- **`scripts/cloud_idp_server_1s.py`**
  *Purpose:* Mock Identity Provider serving strict 1.0-second TTL JSON Web Tokens to expose the ISO-13849 vulnerability window during mild network jamming.
- **`scripts/cloud_idp_server_1s_failback.py`**
  *Purpose:* The full "Cloud-Edge-Cloud" variant that monitors a secondary Pi via background thread pinging and simulates authority failback after 5 minutes of continuous uptime.

### C. Automated Orchestration (Raspberry Pi Supervisor)
- **`scripts/run_test.sh`**
  *Purpose:* The primary bash entrypoint. It receives the parameterized matrix values, dynamically injects `iptables` packet loss (0-100%), spins up `tshark` background network loggers, executes the ROS 2 nodes, and cleanly purges all background zombie processes (`pkill`) after exactly 48 seconds.

### D. ROS 2 Execution Nodes (Raspberry Pi Supervisor)
- **`src/sentry_logic/sentry_logic/joint_logger_node.py`**
  *Purpose:* The central data ingestion hub. It executes the dynamic serial handshake with the Arduino, queries the UR5 IMU to calculate the Exponential Moving Average (EMA) mechanical deceleration, and outputs the final cycle-accurate timestamped CSV payload at exactly 50Hz.
- **`src/sentry_logic/sentry_logic/stream_wrist_kinematics.py`**
  *Purpose:* The kinematic engine. It connects to the UR5 via the ROS 2 `ActionClient`, calculates the smooth cubic-spline robotic trajectory (avoiding quintic "whip-crack" errors), and dynamically spawns an async thread to execute the physical network attack exactly 0.5 seconds after motion begins.
