#!/usr/bin/env python3
"""
SentryC2 Network Sniffer
Captures TCP traffic between Docker container and Niryo Ned2 robot
Measures latency and logs baseline metrics for resilience testing
"""
from scapy.all import sniff, IP, TCP, ICMP
import time
import pandas as pd

LOG_FILE = "baseline_metrics_h0.csv"

def packet_callback(packet):
    if IP in packet:
        timestamp = time.time()
        
        # Determine protocol and direction
        if TCP in packet:
            protocol = "TCP"
            direction = "OUTbound" if packet[IP].src == packet[IP].dst else "INbound" # simplified
        elif ICMP in packet:
            protocol = "ICMP_PING"
            direction = "ECHO_REQ" if packet[ICMP].type == 8 else "ECHO_REPLY"
        else:
            return
            
        length = len(packet)
        
        # Log to CSV (Append mode)
        with open(LOG_FILE, "a") as f:
            f.write(f"{timestamp},{protocol},{direction},{length}\n")

def main():
    print(f"SentryC2: Sniffing traffic for baseline...")
    print(f"Logging to: {LOG_FILE}")
    print("Note: This requires root/sudo privileges")
    
    # Create CSV header if file doesn't exist
    try:
        with open(LOG_FILE, "x") as f:
            f.write("timestamp,protocol,direction,packet_length\n")
    except FileExistsError:
        pass
    
    print(f"Starting packet capture on all interfaces...")
    print(f"Filter: ICMP (Ping) and TCP")
    
    # Sniff ICMP (ping) and TCP
    sniff(filter="icmp or tcp", prn=packet_callback, store=0)

if __name__ == '__main__':
    main()
