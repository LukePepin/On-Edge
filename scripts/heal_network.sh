#!/bin/bash
# ==============================================================================
echo "🧹 Clearing all network jamming rules..."
# Remove any existing iptables rules targeting port 8080
while sudo iptables -D OUTPUT -p tcp --dport 8080 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 0.3 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 0.1 -j DROP 2>/dev/null; do :; done
while sudo iptables -D OUTPUT -p tcp --dport 8080 -m statistic --mode random --probability 1.0 -j DROP 2>/dev/null; do :; done

# Clean up any residual tc rules just in case they were left behind by older versions
sudo tc qdisc del dev wlan0 root 2>/dev/null || true
sudo tc qdisc del dev eth0 root 2>/dev/null || true
sudo tc qdisc del dev lo root 2>/dev/null || true

echo "✅ Network restored to 100% nominal connectivity."
