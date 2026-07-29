#!/bin/bash
# ==============================================================================
# OS Networking Buffer Tuning for Pi 4
# ==============================================================================
# Applies the sysctl network optimizations to prevent CycloneDDS packet fragmentation
# from exhausting the UDP sockets and causing the RTDE driver to stall.

echo "==========================================================="
echo "   OS KERNEL NETWORKING HARDENING (BUFFER TUNING)          "
echo "==========================================================="

echo "[1/3] Expanding receive/transmit socket buffers to 2GB max..."
sudo sysctl -w net.core.rmem_max=2147483647
sudo sysctl -w net.core.wmem_max=2147483647

echo "[2/3] Minimizing IP fragment retention time to 3 seconds..."
sudo sysctl -w net.ipv4.ipfrag_time=3
sudo sysctl -w net.ipv4.ipfrag_high_thresh=134217728

echo "[3/3] Forcing loopback multicast optimization for DDS..."
sudo ip link set dev lo multicast on

echo "✅ OS Network tuning applied. These will reset on reboot unless added to /etc/sysctl.conf"
