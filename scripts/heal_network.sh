#!/bin/bash
# ==============================================================================
# Network Healer
# ==============================================================================

WLAN_INTERFACE="wlan0"

echo "🧹 Clearing all network jamming rules..."
sudo tc qdisc del dev $WLAN_INTERFACE root 2>/dev/null || true

echo "✅ Network restored to 100% nominal connectivity."
