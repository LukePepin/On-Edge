#!/usr/bin/env python3
import serial
import time
import json
import sys
import socket
import csv
import datetime
import os
import threading

UR_IP = "192.168.0.149"
UR_PORT = 29999
CLOUD_IP = "192.168.0.12" # Laptop IP (update if needed)
CLOUD_PORT = 8080

def get_serial_ports():
    if sys.platform == 'win32':
        return 'COM3', 'COM4'
    return '/dev/ttyACM0', '/dev/ttyACM1'

def dashboard_cmd(cmd):
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect((UR_IP, UR_PORT))
        s.sendall((cmd + '\n').encode('utf-8'))
        response = s.recv(1024).decode('utf-8')
        s.close()
        return response.strip()
    except Exception as e:
        return f"Error: {e}"

def start_robot_motion():
    print("  [Dashboard] Unlocking Protective Stop...")
    dashboard_cmd("unlock protective stop")
    time.sleep(2)
    print("  [Dashboard] Hitting Play on UR Teach Pendant (Kinematic Sweep)...")
    dashboard_cmd("play")

def main():
    print("=======================================================")
    print("   DISTRIBUTED DUAL-ARDUINO SWAPOVER ORCHESTRATOR")
    print("=======================================================\n")
    
    crypto_port, sentry_port = get_serial_ports()
    
    try:
        print(f"Connecting to Main Crypto Node on {crypto_port}...")
        crypto_ser = serial.Serial(crypto_port, 115200, timeout=0.1)
        
        print(f"Connecting to Sentry Brain Node on {sentry_port}...")
        sentry_ser = serial.Serial(sentry_port, 115200, timeout=0.1)
        
        time.sleep(2)
        crypto_ser.reset_input_buffer()
        sentry_ser.reset_input_buffer()
    except Exception as e:
        print(f"FATAL: Could not connect to both Arduinos. Did you plug both in? ({e})")
        return

    os.makedirs("data", exist_ok=True)
    timestamp_str = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    log_filename = f"data/distributed_swapover_log_{timestamp_str}.csv"
    
    csv_file = open(log_filename, "w", newline="")
    writer = csv.writer(csv_file)
    writer.writerow(["timestamp", "node", "algorithm", "cycle", "exec_time_ms", "trust_score"])

    # Pre-Flight
    crypto_ser.write((json.dumps({"algo": "CLOUD", "alpha": 1.0}) + '\n').encode('utf-8'))
    print("[SYSTEM BOOT] Booting robot motion for Cloud Phase...")
    start_robot_motion()
    time.sleep(2)

    cloud_socket = None
    state = "CLOUD"
    trial_count = 1
    cloud_active_start = 0

    print(f"\n--- [TRIAL {trial_count}/20] AWAITING CLOUD CONNECTION ---")

    while trial_count <= 20:
        if state == "CLOUD":
            # Attempt to connect/read from Cloud
            if not cloud_socket:
                try:
                    cloud_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    cloud_socket.settimeout(2.0)
                    cloud_socket.connect((CLOUD_IP, CLOUD_PORT))
                    print(f"\n[CLOUD ACTIVE] TCP Socket Connected to Laptop IdP ({CLOUD_IP})")
                    cloud_active_start = time.time()
                except Exception:
                    time.sleep(1)
                    continue

            try:
                data = cloud_socket.recv(1024)
                if not data:
                    raise ConnectionResetError("Zero bytes read")
                
                # Auto-simulate Jamming after 5 seconds to gather data seamlessly
                if time.time() - cloud_active_start > 5.0:
                    raise RuntimeError("Auto-Jamming Triggered for Dataset Collection")
                    
            except Exception as e:
                print("\n[JAMMING ACTIVE] 🧨 WARNING: TCP Socket severed! Cloud lost!")
                cloud_socket.close()
                cloud_socket = None
                state = "EDGE_MESH"
                
                # Signal the Sentry Arduino that we lost the cloud
                sentry_ser.write(b'JAMMED\n')
                crypto_ser.write(b'ATTACK\n') # Safely halt robot immediately
                
        elif state == "EDGE_MESH":
            # Listen to Sentry Arduino (The Brain)
            sentry_line = sentry_ser.readline().decode('utf-8', errors='ignore').strip()
            if sentry_line:
                if sentry_line.startswith("{") and "progress" not in sentry_line:
                    print(f"  [SENTRY NODE]: {sentry_line}")
                    
                if "START_ZKP" in sentry_line:
                    print("\n[EDGE MESH INITIALIZATION] Sentry commanded ZKP initialization!")
                    crypto_ser.write((json.dumps({"algo": "ZKP", "alpha": 0.5}) + '\n').encode('utf-8'))
                    time.sleep(1)
                    start_robot_motion() # Resume motion after ZKP is active
                    
                elif "START_ECC" in sentry_line:
                    print("\n[EDGE MESH CONTINUOUS] Sentry commanded ECC hot-swap!")
                    crypto_ser.write((json.dumps({"algo": "ECC", "alpha": 0.5}) + '\n').encode('utf-8'))
                    
                elif "REJOIN_CLOUD" in sentry_line:
                    print("\n[CLOUD REJOIN] Sentry confirmed stability. Rejoining Cloud!")
                    crypto_ser.write(b'ATTACK\n') # Halt robot for cloud transition
                    crypto_ser.write((json.dumps({"algo": "CLOUD", "alpha": 1.0}) + '\n').encode('utf-8'))
                    time.sleep(1)
                    start_robot_motion()
                    state = "CLOUD"
                    trial_count += 1
                    if trial_count <= 20:
                        print(f"\n--- [TRIAL {trial_count}/20] AWAITING CLOUD CONNECTION ---")

            # Continuously Log Crypto Arduino
            crypto_line = crypto_ser.readline().decode('utf-8', errors='ignore').strip()
            if crypto_line.startswith("{") and "exec_time_ms" in crypto_line:
                try:
                    parsed = json.loads(crypto_line)
                    algo = "ZKP" if parsed["exec_time_ms"] > 200 else "ECC"
                    writer.writerow([time.time(), "CRYPTO_NODE", algo, parsed.get("cycle", 0), parsed.get("exec_time_ms", 0), parsed.get("trust_score", 0)])
                    csv_file.flush()
                    if parsed.get("cycle", 0) % 5 == 0:
                        print(f"  [CRYPTO NODE] {algo} Cycle Validated: {parsed['exec_time_ms']}ms")
                except:
                    pass

    print(f"\nDistributed Suite Complete. Saved to {log_filename}")
    crypto_ser.close()
    sentry_ser.close()

if __name__ == '__main__':
    main()
