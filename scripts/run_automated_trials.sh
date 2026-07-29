#!/bin/bash
# ==============================================================================
# UR5 Automated Latin Square Trial Execution Wrapper
# Orchestrates: Network Jamming -> Kinematics -> Attack -> Safety Reset
# ==============================================================================

# User Variables
UR5_IP="192.168.0.149"
WLAN_INTERFACE="wlan0"
WORKSPACE_DIR="$HOME/Documents/On-Edge"

# Ensure we are in the workspace
cd $WORKSPACE_DIR
source install/setup.bash

echo "==========================================================="
echo "   UR5 AUTOMATED TRIAL EXECUTION WRAPPER (AUTOMATIC RESET) "
echo "==========================================================="
echo "⚠️  WARNING: ROBOT WILL MOVE AUTOMATICALLY. CLEAR WORKCELL! ⚠️"
echo "==========================================================="
read -p "Press ENTER to acknowledge safety and begin execution..."

# Example: Running 5 iterations of a specific Jamming Level
# Note: To run fully unattended overnight, trials must be grouped by 
# Cryptographic Algorithm (ZKP/ECC/CLOUD) to avoid needing to physically 
# swap the Arduino USB connection on /dev/ttyACM0 between randomized trials.

ALGO="ZKP"
NODES=10
LOSS_LEVELS=(0 10 20 30)
ITERATIONS=5

for loss in "${LOSS_LEVELS[@]}"; do
    for ((i=1; i<=ITERATIONS; i++)); do
        
        echo ""
        echo "-----------------------------------------------------------"
        echo "🚀 STARTING: $ALGO | Nodes: $NODES | Jamming: $loss% | Iteration: $i/$ITERATIONS"
        echo "-----------------------------------------------------------"

        # 1. Idempotent Network Provisioning
        if [ "$loss" -gt 0 ]; then
            echo "[1/5] Injecting $loss% Packet Loss on $WLAN_INTERFACE..."
            sudo tc qdisc replace dev $WLAN_INTERFACE root netem loss $loss%
        else
            echo "[1/5] Cleaning Network Interface (0% Loss)..."
            sudo tc qdisc del dev $WLAN_INTERFACE root 2>/dev/null || true
        fi

        # 2. Start TShark & Logger (Backgrounded)
        echo "[2/5] Spooling up TShark and Joint Logger Data Pipelines..."
        mkdir -p data
        sudo tshark -i $WLAN_INTERFACE -f "udp" -a duration:30 -w data/trial_${ALGO}_n${NODES}_loss${loss}_iter${i}.pcap > /dev/null 2>&1 &
        TSHARK_PID=$!
        
        ros2 run sentry_logic joint_logger --ros-args -p algo:=$ALGO -p nodes:=$NODES -p loss:=$loss -p iteration:=$i > /dev/null 2>&1 &
        LOGGER_PID=$!

        sleep 2 # Let the logger and sniffer stabilize

        # 3. Kinematic Spool-up (Blocking until trajectory finishes or E-Stops)
        echo "[3/5] Executing Kinematic Trajectory & 50% Strike Zone..."
        ros2 run sentry_logic stream_wrist_kinematics
        
        # 4. Data Archival 
        echo "[4/5] Archiving Data & Terminating Loggers..."
        kill -INT $LOGGER_PID 2>/dev/null
        sudo kill $TSHARK_PID 2>/dev/null
        wait $LOGGER_PID 2>/dev/null

        # 5. Automated Safety Reset
        echo "[5/5] Executing Dashboard Safety Reset on Port 29999..."
        python3 scripts/clear_safety_stop.py $UR5_IP

        echo "✅ Trial Complete. Cooling down for 3 seconds..."
        sleep 3

    done
done

echo ""
echo "🎉 ALL TRIALS COMPLETED SUCCESSFULLY!"
# Final network cleanup
sudo tc qdisc del dev $WLAN_INTERFACE root 2>/dev/null || true
