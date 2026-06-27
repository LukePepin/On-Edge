#!/bin/bash
# Dual-Node UR5 ROS 2 Humble Setup Script
# Run this on both the Raspberry Pi 4 (Edge Supervisor) and Windows WSL (Cloud Supervisor)

set -e

echo "=================================================="
echo " Starting UR5 ROS 2 Humble Installation (Phase 3)"
echo "=================================================="

# 1. Update and upgrade existing packages
echo "[1/4] Updating apt repositories and injecting ROS 2 GPG keys..."
sudo apt-get update && sudo apt-get install -y curl software-properties-common

# Ensure universe repository is enabled
sudo add-apt-repository universe -y

# Add ROS 2 GPG key
sudo curl -sSL https://raw.githubusercontent.com/ros/rosdistro/master/ros.key -o /usr/share/keyrings/ros-archive-keyring.gpg

# Add ROS 2 repository to sources list
echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/ros-archive-keyring.gpg] http://packages.ros.org/ros2/ubuntu $(. /etc/os-release && echo $UBUNTU_CODENAME) main" | sudo tee /etc/apt/sources.list.d/ros2.list > /dev/null

# Update apt again to pull the newly added ROS 2 packages
sudo apt-get update

# 2. Install Universal Robots ROS 2 Driver & Base ROS 2 Desktop (for 'launch' and RViz)
echo "[2/4] Installing Universal Robots ROS 2 Driver & Desktop..."
sudo apt-get install -y ros-humble-ur ros-humble-desktop

# 3. Install MoveIt 2 (Required for Kinematic Trajectory Planning)
echo "[3/4] Installing MoveIt 2..."
sudo apt-get install -y ros-humble-moveit

# 4. Install ROS 2 Control (Hardware Abstraction Layer)
echo "[4/4] Installing ROS 2 Control frameworks..."
sudo apt-get install -y ros-humble-ros2-control ros-humble-ros2-controllers

# Auto-source ROS 2 for future terminal sessions
if ! grep -q "source /opt/ros/humble/setup.bash" ~/.bashrc; then
    echo "source /opt/ros/humble/setup.bash" >> ~/.bashrc
fi

echo "=================================================="
echo " Installation Complete!"
echo " "
echo " Next Steps:"
echo " 1. Ensure the UR5 robot is turned on."
echo " 2. Ensure the 'External Control' URCap is installed on the Teach Pendant."
echo " 3. Verify connection by running:"
echo "    source /opt/ros/humble/setup.bash"
echo "    ros2 launch ur_robot_driver ur_control.launch.py ur_type:=ur5 robot_ip:=192.168.0.149"
echo "=================================================="
