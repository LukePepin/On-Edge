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

# Find the active interface that is currently routing traffic
ACTIVE_IFACE=$(ip route get 8.8.8.8 | grep -oP '(?<=dev )[^ ]+')
if [ -z "$ACTIVE_IFACE" ]; then
    ACTIVE_IFACE="wlan0"
fi

echo "🧹 Cleaning previous network rules..."
# Remove any existing iptables rules targeting port 8080
while sudo iptables -D OUTPUT -p tcp --dport 8080 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 0.3 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 0.1 -j DROP 2>/dev/null; do :; done
# Clean up any residual tc rules just in case they were left behind
sudo tc qdisc del dev wlan0 root 2>/dev/null || true
sudo tc qdisc del dev eth0 root 2>/dev/null || true
sudo tc qdisc del dev lo root 2>/dev/null || true

if [ "$LOSS" -eq 100 ]; then
    echo "🔥 Injecting 100% packet loss exclusively on Cloud Auth (Port 8080)..."
    sudo iptables -A OUTPUT -p tcp --dport 8080 -j DROP
else
    # Convert percentage to a probability float (e.g. 30 -> 0.30)
    PROB=$(echo "scale=2; $LOSS / 100" | bc)
    echo "🔥 Injecting ${LOSS}% packet loss exclusively on Cloud Auth (Port 8080)..."
    sudo iptables -A OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability $PROB -j DROP
fi

echo "✅ Cloud Auth is now jammed at ${LOSS}%. SSH is mathematically safe!"
