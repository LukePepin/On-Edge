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

echo "⏳ Waiting 2 seconds for logger to initialize..."
sleep 2

echo "🔥 [2/3] Initiating 10-Second Cryptographic Attack..."
python3 scripts/trigger_attack.py

echo "💾 [3/3] Terminating Logger to flush CSV data..."
kill -INT $LOGGER_PID 2>/dev/null
wait $LOGGER_PID 2>/dev/null

echo "✅ Phase 2 Validation Complete! Check the CSV output."
