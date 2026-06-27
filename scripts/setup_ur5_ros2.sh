#!/bin/bash
# Dual-Node UR5 ROS 2 Humble Setup Script
# Run this on both the Raspberry Pi 4 (Edge Supervisor) and Windows WSL (Cloud Supervisor)

set -e

echo "=================================================="
echo " Starting UR5 ROS 2 Humble Installation (Phase 3)"
echo "=================================================="

# 1. Update and upgrade existing packages
echo "[1/4] Updating apt repositories..."
sudo apt-get update && sudo apt-get upgrade -y

# 2. Install Universal Robots ROS 2 Driver
echo "[2/4] Installing Universal Robots ROS 2 Driver..."
sudo apt-get install -y ros-humble-ur

# 3. Install MoveIt 2 (Required for Kinematic Trajectory Planning)
echo "[3/4] Installing MoveIt 2..."
sudo apt-get install -y ros-humble-moveit

# 4. Install ROS 2 Control (Hardware Abstraction Layer)
echo "[4/4] Installing ROS 2 Control frameworks..."
sudo apt-get install -y ros-humble-ros2-control ros-humble-ros2-controllers

echo "=================================================="
echo " Installation Complete!"
echo " "
echo " Next Steps:"
echo " 1. Ensure the UR5 robot is turned on."
echo " 2. Ensure the 'External Control' URCap is installed on the Teach Pendant."
echo " 3. Verify connection by running:"
echo "    ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5 robot_ip:=192.168.0.145"
echo "=================================================="
