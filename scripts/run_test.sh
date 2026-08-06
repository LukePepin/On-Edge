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
ALPHA="0.3"

while [[ "$#" -gt 0 ]]; do
    case $1 in
        -a|--algo) ALGO="$2"; shift ;;
        --outage)
            OUTAGE="$2"
            shift
            ;;
        -i|--iter) ITER="$2"; shift ;;
        -p|--alpha) ALPHA="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$ALGO" ] || [ -z "$OUTAGE" ] || [ -z "$ITER" ]; then
    echo "Usage: $0 --algo <ZKP/ECC/CLOUD> --outage <int ms> --iter <int> [--alpha <float>]"
    exit 1
fi

MEMLOCK=$(ulimit -l)
if [ "$MEMLOCK" != "unlimited" ]; then
    echo "ERROR: POSIX Memory lock limit (ulimit -l) is $MEMLOCK, but must be 'unlimited'. Check /etc/security/limits.conf"
    exit 1
fi

echo "==========================================================="
echo "   SINGLE-SHOT TRIAL: $ALGO | Outage: ${OUTAGE}ms | Iter: $ITER | Alpha: $ALPHA"
echo "==========================================================="

cd $WORKSPACE_DIR
source install/setup.bash

# Ensure local telemetry is quarantined from the wireless jamming plane
sudo ip link set dev lo multicast on
export ROS_LOCALHOST_ONLY=1

# --- PRE-FLIGHT ZOMBIE CLEANUP ---
# If a previous trial was Ctrl+C'd, the logger stays alive in the background and will
# violently clash over the serial port on the next run. We must purge it before starting.
pkill -f "sentry_logic/joint_logger" || true
pkill -f "sentry_logic/stream_wrist_kinematics" || true
sudo killall tshark 2>/dev/null || true
# ---------------------------------

# ------------------------------------------------------------------------------
# 2. Network Jamming (Idempotent cleanup -> Inject)
# ------------------------------------------------------------------------------
echo "[1/4] Preparing Network Interface ($WLAN_INTERFACE)..."
# Remove any existing iptables rules targeting port 8080
while sudo iptables -D OUTPUT -p tcp --dport 8080 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 0.3 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 0.1 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 1.0 -j DROP 2>/dev/null; do :; done
# Note: Deterministic network outages are now dynamically triggered by the Python orchestrator
# when the strike zone is reached.

# ------------------------------------------------------------------------------
# 3. Spool Up Data Loggers
# ------------------------------------------------------------------------------
echo "[2/4] Spooling up Loggers..."
mkdir -p data
ALPHA_STR="ewma${ALPHA#0.}"
TIMESTAMP=$(date +%s)

# tshark drops root privileges when writing files, causing Permission Denied in user dirs.
# We bypass this by writing to the world-writable /tmp dir, then moving it later.
PCAP_TMP="/tmp/trial_${ALGO}_outage${OUTAGE}_${ALPHA_STR}_iter${ITER}_${TIMESTAMP}.pcap"
taskset 0x7 sudo tshark -i $WLAN_INTERFACE -f "udp" -a duration:120 -w $PCAP_TMP > /dev/null 2>&1 &

taskset 0x7 ros2 run sentry_logic joint_logger --ros-args -p algo:=$ALGO -p outage:=$OUTAGE -p iteration:=$ITER -p alpha:=$ALPHA -p timestamp:=$TIMESTAMP &
LOGGER_PID=$!
sudo chrt -f 99 -p $LOGGER_PID

echo "⏳ Waiting for Arduino Dynamic Handshake to complete (approx 5 seconds)..."
sleep 6 # Wait for the Python logger to finish its boot-loop and engage the Optocoupler HIGH

echo "⚠️ SAFEGUARD CLEARED (Optocoupler RED). YOU NOW HAVE 4 SECONDS TO PRESS 'PLAY' ON THE URCAP!"
sleep 4 # Allow operator to hit play on the teach pendant before kinematics execute

# ------------------------------------------------------------------------------
# 4. Execute Unified Kinematics + Attack hook
# ------------------------------------------------------------------------------
echo "Switching to pure passthrough kinematics to prevent UR5 controller jitter..."
# We execute this swap AFTER the user presses Play (clearing the Safeguard Stop) 
# to guarantee the UR5 driver doesn't deadlock while processing the switch request!
taskset 0x7 ros2 control switch_controllers --activate passthrough_trajectory_controller --deactivate scaled_joint_trajectory_controller forward_position_controller > /dev/null 2>&1 || true

echo "[3/4] Executing Kinematic Trajectory (Autonomous Attack Injection Enabled)..."
# Pass ALGO to kinematics to dynamically select the 5s (ZKP) or 15s (CLOUD) sweep
# Run in the background to apply chrt, then wait for it to unblock bash orchestrator
taskset 0x7 ros2 run sentry_logic stream_wrist_kinematics --ros-args -p algo:=$ALGO &
KINEMATICS_PID=$!
sudo chrt -f 99 -p $KINEMATICS_PID
wait $KINEMATICS_PID

echo "⏳ Trajectory complete. Waiting 3 seconds for trailing flatline data to stabilize..."
sleep 3

# ------------------------------------------------------------------------------
# 5. Data Archival & Cleanup
# ------------------------------------------------------------------------------
echo "[4/4] Archiving Data & Terminating Loggers..."
pkill -f "sentry_logic/joint_logger" || true
pkill -f "sentry_logic/stream_wrist_kinematics" || true
sudo killall tshark 2>/dev/null || true

# Move the PCAP from /tmp to the secure data directory
sudo mv $PCAP_TMP data/ 2>/dev/null || true

echo "Cleaning up network rules..."
while sudo iptables -D OUTPUT -p tcp --dport 8080 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 0.3 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 0.1 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 1.0 -j DROP 2>/dev/null; do :; done

# Forcibly restore terminal state in case a forcefully killed ROS 2 or tshark node mangled the TTY settings
stty sane

echo "✅ Trial Complete! Please restart URCap on Teach Pendant for next run."
