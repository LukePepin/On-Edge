#!/bin/bash
# ==============================================================================
# Cloud-Targeted Network Jammer (DIL Environment Simulator)
# ==============================================================================

WLAN_INTERFACE="wlan0"
LOSS=$1

if [ -z "$LOSS" ]; then
    echo "Usage: bash scripts/jam_cloud.sh <loss_percentage>"
    echo "Example: bash scripts/jam_cloud.sh 30"
    echo "Example: bash scripts/jam_cloud.sh 100"
    exit 1
fi

echo "🧹 Cleaning previous network rules..."
sudo tc qdisc del dev $WLAN_INTERFACE root 2>/dev/null || true

echo "🔥 Injecting ${LOSS}% packet loss exclusively on Cloud Auth (Port 8080)..."
sudo tc qdisc add dev $WLAN_INTERFACE root handle 1: prio bands 3
sudo tc qdisc add dev $WLAN_INTERFACE parent 1:2 handle 20: netem loss ${LOSS}%

# Route ONLY Port 8080 (Cloud Auth) to the Jamming Lane
sudo tc filter add dev $WLAN_INTERFACE protocol ip parent 1:0 prio 2 u32 match ip dport 8080 0xffff flowid 1:2

echo "✅ Cloud Auth is now jammed at ${LOSS}%. SSH is completely safe!"
