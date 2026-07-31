#!/bin/bash
# ==============================================================================
# Phase 2 Validation: Joint Logger + 10s Trigger Attack
# ==============================================================================

WORKSPACE_DIR="$HOME/Documents/On-Edge"
cd $WORKSPACE_DIR
source install/setup.bash

echo "🚀 [1/3] Spooling up ROS 2 Joint Logger in the background..."
mkdir -p data/60_trial_run
taskset 0x7 ros2 run sentry_logic joint_logger --ros-args -p algo:=ZKP_TEST -p nodes:=1 -p loss:=0 -p iteration:=99 > /dev/null 2>&1 &
LOGGER_PID=$!

echo "⏳ Waiting 3 seconds for logger and serial port to initialize..."
sleep 3

echo "🔥 [2/3] Initiating 10-Second Cryptographic Attack via ROS 2 Service..."
ros2 service call /inject_attack std_srvs/srv/Trigger "{}"

echo "⏳ Waiting 12 seconds for the attack to finish..."
sleep 12

echo "💾 [3/3] Terminating Logger to flush CSV data..."
pkill -f joint_logger_node
sleep 2

echo "✅ Phase 2 Validation Complete! Check the CSV output."
