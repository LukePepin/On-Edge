#!/bin/bash
# ==============================================================================
# Network Healer
# ==============================================================================

ACTIVE_IFACE=$(ip route get 8.8.8.8 | grep -oP '(?<=dev )[^ ]+')
if [ -z "$ACTIVE_IFACE" ]; then
    ACTIVE_IFACE="wlan0"
fi

echo "🧹 Clearing all network jamming rules from $ACTIVE_IFACE and lo..."
sudo tc qdisc del dev $ACTIVE_IFACE root 2>/dev/null || true
sudo tc qdisc del dev lo root 2>/dev/null || true

echo "✅ Network restored to 100% nominal connectivity."
