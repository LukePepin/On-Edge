#!/usr/bin/env bash
# READ-ONLY preflight for the V8 acquisition host (Raspberry Pi).
# Changes nothing, opens no serial port, sends nothing to the monitor or the robot.
#   bash v8/scripts/pi_preflight.sh
# For robot mode, source ROS first:  source /opt/ros/humble/setup.bash  (and the UR driver workspace)
set -u
cd "$(dirname "$0")/../.." || exit 1

echo "== host"
hostname; uname -srm; python3 --version
echo "== repository"
git rev-parse --short HEAD 2>/dev/null && git status --porcelain | head -20
echo "== python modules"
python3 -c "import serial; print('pyserial', serial.__version__)" 2>/dev/null || echo "pyserial MISSING (sudo apt install python3-serial)"
python3 -c "import rclpy; print('rclpy importable')" 2>/dev/null || echo "rclpy not importable (source /opt/ros/humble/setup.bash for robot mode)"
python3 -c "import ur_dashboard_msgs.msg; print('ur_dashboard_msgs importable')" 2>/dev/null || echo "ur_dashboard_msgs not importable (safety-mode topic unavailable)"
python3 -c "import control_msgs.action; print('control_msgs importable')" 2>/dev/null || echo "control_msgs not importable (trajectory unavailable)"
echo "== serial devices"
ls -l /dev/serial/by-id/ 2>/dev/null || echo "no /dev/serial/by-id entries"
ls -l /dev/ttyACM* 2>/dev/null || echo "no /dev/ttyACM* devices"
id -nG | tr ' ' '\n' | grep -qx dialout && echo "user is in group dialout" || echo "user NOT in dialout: serial access may be refused"
for p in /dev/ttyACM*; do
  [ -e "$p" ] || continue
  python3 - "$p" <<'PY'
import sys
sys.path.insert(0, "v8")
from onedge_v8.transport import port_users
users = port_users(sys.argv[1])
print(sys.argv[1], "held open by PID(s)", users if users else "none")
PY
done
echo "== historical launchers still running? (must be stopped before V8 uses the port)"
pgrep -af "joint_logger|stream_wrist_kinematics|run_campaign|run_test.sh|onedge_v8" || echo "none"
echo "== disk"
df -h . | tail -1
echo "== ROS environment"
if command -v ros2 >/dev/null 2>&1; then
  echo "ROS_DISTRO=${ROS_DISTRO:-unset} ROS_DOMAIN_ID=${ROS_DOMAIN_ID:-unset} ROS_LOCALHOST_ONLY=${ROS_LOCALHOST_ONLY:-unset} RMW=${RMW_IMPLEMENTATION:-default}"
  timeout 15 ros2 topic list 2>/dev/null | grep -E "joint_states|safety_mode|robot_program_running" || echo "(UR driver topics not visible: driver not running or different ROS environment)"
else
  echo "ros2 not on PATH (bench mode does not need it)"
fi
echo "== software tests (simulated transport only; safe to run)"
echo "   python3 -m unittest discover -s v8/tests"
