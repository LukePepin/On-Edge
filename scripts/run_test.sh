#!/bin/bash
# ==============================================================================
# UR5 Parameterized Single-Shot Trial Wrapper
# ==============================================================================
# Executes exactly one isolated trial. Uses getopts for safe parameterized input.
# Example: ./scripts/run_test.sh --algo ZKP --nodes 2 --loss 10 --iter 1

UR5_IP="192.168.0.149"
WLAN_INTERFACE="wlan0"
WORKSPACE_DIR="$HOME/Documents/On-Edge"

# ------------------------------------------------------------------------------
# 1. Parse Arguments
# ------------------------------------------------------------------------------
ALGO=""
NODES=""
LOSS=""
ITER=""

# We use standard getopts for short flags or manual parsing for long flags
while [[ "$#" -gt 0 ]]; do
    case $1 in
        -a|--algo) ALGO="$2"; shift ;;
        -n|--nodes) NODES="$2"; shift ;;
        -l|--loss) LOSS="$2"; shift ;;
        -i|--iter) ITER="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$ALGO" ] || [ -z "$NODES" ] || [ -z "$LOSS" ] || [ -z "$ITER" ]; then
    echo "Usage: $0 --algo <ZKP/ECC/CLOUD> --nodes <int> --loss <0/10/20/30> --iter <int>"
    exit 1
fi

echo "==========================================================="
echo "   SINGLE-SHOT TRIAL: $ALGO | Nodes: $NODES | Jamming: $LOSS% | Iter: $ITER"
echo "==========================================================="

cd $WORKSPACE_DIR
source install/setup.bash

# ------------------------------------------------------------------------------
# 2. Network Jamming (Idempotent cleanup -> Inject)
# ------------------------------------------------------------------------------
echo "[1/6] Preparing Network Interface ($WLAN_INTERFACE)..."
sudo tc qdisc del dev $WLAN_INTERFACE root 2>/dev/null || true

if [ "$LOSS" -gt 0 ]; then
    echo "      Injecting $LOSS% Packet Loss (Exempting UR5 on $UR5_IP)..."
    sudo tc qdisc add dev $WLAN_INTERFACE root handle 1: prio bands 3
    sudo tc qdisc add dev $WLAN_INTERFACE parent 1:2 handle 20: netem loss $LOSS%
    sudo tc filter add dev $WLAN_INTERFACE protocol ip parent 1:0 prio 1 u32 match ip dst $UR5_IP flowid 1:1
    sudo tc filter add dev $WLAN_INTERFACE protocol ip parent 1:0 prio 1 u32 match ip src $UR5_IP flowid 1:1
    sudo tc filter add dev $WLAN_INTERFACE protocol ip parent 1:0 prio 2 u32 match ip dst 0.0.0.0/0 flowid 1:2
else
    echo "      Clean Network (0% Loss)."
fi

# ------------------------------------------------------------------------------
# 3. Start Background Loggers
# ------------------------------------------------------------------------------
echo "[2/6] Spooling up Loggers..."
mkdir -p data
sudo tshark -i $WLAN_INTERFACE -f "udp" -a duration:30 -w data/trial_${ALGO}_n${NODES}_loss${LOSS}_iter${ITER}.pcap > /dev/null 2>&1 &
TSHARK_PID=$!

ros2 run sentry_logic joint_logger --ros-args -p algo:=$ALGO -p nodes:=$NODES -p loss:=$LOSS -p iteration:=$ITER > /dev/null 2>&1 &
LOGGER_PID=$!

sleep 2 # Let the logger and sniffer stabilize

# ------------------------------------------------------------------------------
# 4. Execute Kinematics
# ------------------------------------------------------------------------------
echo "[3/6] Executing Kinematic Trajectory..."
ros2 run sentry_logic stream_wrist_kinematics

# ------------------------------------------------------------------------------
# 5. Data Archival
# ------------------------------------------------------------------------------
echo "[4/6] Archiving Data & Terminating Loggers..."
kill -INT $LOGGER_PID 2>/dev/null
sudo kill $TSHARK_PID 2>/dev/null
wait $LOGGER_PID 2>/dev/null

# ------------------------------------------------------------------------------
# 6. Safety Reset
# ------------------------------------------------------------------------------
echo "[5/6] Executing Dashboard Safety Reset on Port 29999..."
python3 scripts/clear_safety_stop.py $UR5_IP

# ------------------------------------------------------------------------------
# 7. Cleanup
# ------------------------------------------------------------------------------
echo "[6/6] Cleaning up network rules..."
sudo tc qdisc del dev $WLAN_INTERFACE root 2>/dev/null || true

echo "✅ Trial Complete! System returned to baseline state."
