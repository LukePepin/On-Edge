#!/bin/bash
# ==============================================================================
# UR5 RTDE Watchdog Hardening Script
# ==============================================================================
# This script clones the Universal Robots ROS 2 driver from source and injects
# a 500-cycle keepalive buffer to prevent CycloneDDS discovery storms from 
# dropping the reverse interface during runtime.

WORKSPACE_DIR="$HOME/Documents/On-Edge"
DRIVER_SRC_DIR="$WORKSPACE_DIR/src/Universal_Robots_ROS2_Driver"

echo "==========================================================="
echo "   UR5 RTDE WATCHDOG HARDENING PATCH (KEEP-ALIVE: 500)     "
echo "==========================================================="

# 1. Clone the driver from source if it doesn't exist
if [ ! -d "$DRIVER_SRC_DIR" ]; then
    echo "[1/4] Cloning Universal_Robots_ROS2_Driver from source..."
    cd $WORKSPACE_DIR/src
    git clone -b humble https://github.com/UniversalRobots/Universal_Robots_ROS2_Driver.git
else
    echo "[1/4] Driver source already exists. Pulling latest..."
    cd $DRIVER_SRC_DIR
    git pull
fi

# 2. Inject the Watchdog Keepalive Fix
echo "[2/4] Injecting 500-cycle RTDE keepalive buffer..."
HW_INTERFACE_FILE="$DRIVER_SRC_DIR/ur_robot_driver/src/hardware_interface.cpp"

if grep -q "setKeepaliveCount(500)" "$HW_INTERFACE_FILE"; then
    echo "      -> Patch already applied. Skipping."
else
    sed -i 's/ur_driver_->startRTDECommunication();/ur_driver_->setKeepaliveCount(500);\n  ur_driver_->startRTDECommunication();/g' "$HW_INTERFACE_FILE"
    echo "      -> Successfully patched hardware_interface.cpp"
fi

# 3. Clean and Rebuild the Workspace
echo "[3/4] Recompiling the ROS 2 Workspace (This may take a few minutes)..."
cd $WORKSPACE_DIR
# Only remove the specific driver build/install artifacts to save time, or do a full clean
rm -rf build/ur_robot_driver install/ur_robot_driver
colcon build --symlink-install --packages-select ur_robot_driver

# 4. Source the new build
echo "[4/4] Sourcing updated environment..."
source install/setup.bash

echo "✅ RTDE Watchdog Hardening Complete! The bridge is now resilient to CPU spikes."
