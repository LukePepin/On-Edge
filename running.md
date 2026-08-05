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

**Example 2: ZKP Mesh Run (60% Loss)**
```bash
./scripts/run_test.sh --algo ZKP --nodes 2 --loss 60 --iter 1
```

*Note: The script takes exactly 48 seconds to run (15s for the trajectory + 3s spool up + 30s mechanical standstill buffer). Ensure you manually restart the external URCap program on the UR5 Teach Pendant between every run.*
