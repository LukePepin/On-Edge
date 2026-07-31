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
sudo tc qdisc del dev $ACTIVE_IFACE root 2>/dev/null || true
sudo tc qdisc del dev lo root 2>/dev/null || true

echo "🔥 Injecting ${LOSS}% packet loss on $ACTIVE_IFACE and loopback..."
# Setup External Interface (wlan0 / eth0)
sudo tc qdisc add dev $ACTIVE_IFACE root handle 1: prio bands 3
sudo tc qdisc add dev $ACTIVE_IFACE parent 1:2 handle 20: netem loss ${LOSS}%

# Exempt SSH on External Interface
sudo tc filter add dev $ACTIVE_IFACE protocol ip parent 1:0 prio 1 u32 match ip sport 22 0xffff flowid 1:1
sudo tc filter add dev $ACTIVE_IFACE protocol ip parent 1:0 prio 1 u32 match ip dport 22 0xffff flowid 1:1

# Exempt UR5 IP (Just in case it's connected)
UR5_IP="192.168.0.149"
sudo tc filter add dev $ACTIVE_IFACE protocol ip parent 1:0 prio 1 u32 match ip dst $UR5_IP flowid 1:1
sudo tc filter add dev $ACTIVE_IFACE protocol ip parent 1:0 prio 1 u32 match ip src $UR5_IP flowid 1:1

# Route ALL OTHER TRAFFIC to the Jamming Lane on External
sudo tc filter add dev $ACTIVE_IFACE protocol ip parent 1:0 prio 2 u32 match ip dst 0.0.0.0/0 flowid 1:2

# Setup Loopback Interface (In case you are running the Cloud Server on the Pi itself)
sudo tc qdisc add dev lo root handle 1: prio bands 3
sudo tc qdisc add dev lo parent 1:2 handle 20: netem loss ${LOSS}%
sudo tc filter add dev lo protocol ip parent 1:0 prio 2 u32 match ip dst 0.0.0.0/0 flowid 1:2

echo "✅ Network is now jammed at ${LOSS}% on $ACTIVE_IFACE & lo. SSH remains safe!"
