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
        -l|--loss) LOSS="$2"; shift ;;
        -i|--iter) ITER="$2"; shift ;;
        -p|--alpha) ALPHA="$2"; shift ;;
        *) echo "Unknown parameter passed: $1"; exit 1 ;;
    esac
    shift
done

if [ -z "$ALGO" ] || [ -z "$LOSS" ] || [ -z "$ITER" ]; then
    echo "Usage: $0 --algo <ZKP/ECC/CLOUD> --loss <25/50/75> --iter <int> [--alpha <float>]"
    exit 1
fi

if [[ "$LOSS" != "0" && "$LOSS" != "25" && "$LOSS" != "50" && "$LOSS" != "75" && "$LOSS" != "100" ]]; then
    echo "ERROR: --loss must be exactly 25, 50, or 75 (0 and 100 permitted for extreme control tests)."
    exit 1
fi

if [[ "$ALPHA" != "0.1" && "$ALPHA" != "0.3" && "$ALPHA" != "0.5" ]]; then
    echo "ERROR: --alpha must be exactly 0.1, 0.3, or 0.5."
    exit 1
fi

MEMLOCK=$(ulimit -l)
if [ "$MEMLOCK" != "unlimited" ]; then
    echo "ERROR: POSIX Memory lock limit (ulimit -l) is $MEMLOCK, but must be 'unlimited'. Check /etc/security/limits.conf"
    exit 1
fi

echo "==========================================================="
echo "   SINGLE-SHOT TRIAL: $ALGO | Jamming: $LOSS% | Iter: $ITER | Alpha: $ALPHA"
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
# 2. Network Perturbation Injection (NetEm)
# ------------------------------------------------------------------------------
if [ "$ALGO" == "CLOUD" ] || [ "$ALGO" == "ZKP" ]; then
    echo "      Injecting $LOSS% Packet Loss on Cloud Auth (Port 8080)..."
    sudo tc qdisc del dev $WLAN_INTERFACE root 2>/dev/null || true
    # Removed /dev/null to debug if interface exists
    sudo tc qdisc add dev $WLAN_INTERFACE root netem loss $LOSS%
    sudo iptables -A OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability $(echo "scale=2; $LOSS/100" | bc) -j DROP
fi

# ------------------------------------------------------------------------------
# 3. Spool Up Data Loggers
# ------------------------------------------------------------------------------
echo "[2/4] Spooling up Loggers..."
mkdir -p data/60_trial_run
ALPHA_STR="ewma${ALPHA#0.}"

# tshark drops root privileges when writing files, causing Permission Denied in user dirs.
# We bypass this by writing to the world-writable /tmp dir, then moving it later.
PCAP_TMP="/tmp/trial_${ALGO}_loss${LOSS}_${ALPHA_STR}_iter${ITER}.pcap"
taskset 0x7 sudo tshark -i $WLAN_INTERFACE -f "udp" -a duration:80 -w $PCAP_TMP &
TSHARK_PID=$!

taskset 0x7 ros2 run sentry_logic joint_logger --ros-args -p algo:=$ALGO -p loss:=$LOSS -p iteration:=$ITER -p alpha:=$ALPHA &
LOGGER_PID=$!

echo "⏳ Waiting for Arduino Dynamic Handshake to complete (approx 5 seconds)..."
sleep 6 # Wait for the Python logger to finish its boot-loop and engage the Optocoupler HIGH

echo "⚠️ SAFEGUARD CLEARED (Optocoupler RED). YOU NOW HAVE 4 SECONDS TO PRESS 'PLAY' ON THE URCAP!"
sleep 4 # Allow operator to hit play on the teach pendant before kinematics execute

# ------------------------------------------------------------------------------
# 4. Execute Unified Kinematics + Attack hook
# ------------------------------------------------------------------------------
echo "[3/4] Executing Kinematic Trajectory (Autonomous Attack Injection Enabled)..."
# Pass ALGO to kinematics to dynamically select the 5s (ZKP) or 15s (CLOUD) sweep
# Run in the FOREGROUND so bash natively blocks! (Timeout managed dynamically by Python)
taskset 0x7 ros2 run sentry_logic stream_wrist_kinematics --ros-args -p algo:=$ALGO

echo "⏳ Trajectory complete. Waiting 3 seconds for trailing flatline data to stabilize..."
sleep 3

# ------------------------------------------------------------------------------
# 5. Data Archival & Cleanup
# ------------------------------------------------------------------------------
echo "[4/4] Archiving Data & Terminating Loggers..."
pkill -f "sentry_logic/joint_logger" || true
pkill -f "sentry_logic/stream_wrist_kinematics" || true
sudo kill -2 $TSHARK_PID 2>/dev/null

# Move the PCAP from /tmp to the secure data directory
sudo mv $PCAP_TMP data/60_trial_run/ 2>/dev/null || true

echo "Cleaning up network rules..."
while sudo iptables -D OUTPUT -p tcp --dport 8080 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 0.3 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 0.1 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 1.0 -j DROP 2>/dev/null; do :; done

echo "✅ Trial Complete! Please restart URCap on Teach Pendant for next run."
