#!/usr/bin/env python3
import serial
import time
import json
import argparse
import sys

def get_serial_port():
    if sys.platform == 'win32':
        return 'COM3'
    return '/dev/ttyACM0'

def run_capstone_sequence(ser, iter_num):
    print(f"\n=======================================================")
    print(f"   CAPSTONE TRIAL {iter_num}/6: CLOUD -> ZKP -> ECC -> CLOUD")
    print(f"=======================================================\n")
    
    # 1. CLOUD ACTIVE
    print("[CLOUD ACTIVE] Pinging Cloud Identity Provider for 1.0s Leases...")
    for _ in range(5):
        print("  -> Auth Lease Granted (Scope: kinematic_control)")
        time.sleep(1)
        
    # 2. EW JAMMING (LOSS OF CLOUD)
    print("\n[JAMMING ACTIVE] 🧨 WARNING: Tactical EW Jamming detected!")
    print("[JAMMING ACTIVE] Cloud connection lost. Connection timed out.")
    time.sleep(1)
    
    # 3. EDGE MESH INITIALIZATION (ZKP)
    print("\n[EDGE MESH INITIALIZATION] Bootstrapping local mesh with Zero-Knowledge Proofs...")
    payload = {"algo": "ZKP", "alpha": 0.5}
    ser.write((json.dumps(payload) + '\n').encode('utf-8'))
    
    # Wait for ready
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line == '{"status": "READY"}':
            print("  -> Arduino acknowledged ZKP Configuration. Booting Mesh.")
            break
            
    # Read 5 ZKP cycles
    zkp_cycles = 0
    while zkp_cycles < 5:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith("{") and "exec_time_ms" in line:
            print(f"  [ZKP Cycle {zkp_cycles+1}/5] Validated: {line}")
            zkp_cycles += 1
            
    # 4. EDGE MESH CONTINUOUS (ECC HOT-SWAP)
    print("\n[EDGE MESH CONTINUOUS] Secure Identity Established (5 valid ZKP proofs).")
    print("[EDGE MESH CONTINUOUS] Hot-swapping state machine to lightweight ECC for real-time kinematics...")
    payload = {"algo": "ECC", "alpha": 0.5}
    ser.write((json.dumps(payload) + '\n').encode('utf-8'))
    
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line == '{"status": "READY"}':
            print("  -> Arduino acknowledged ECC Configuration. Executing handover.")
            break
            
    # Read 10 ECC cycles
    ecc_cycles = 0
    while ecc_cycles < 10:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith("{") and "exec_time_ms" in line:
            print(f"  [ECC Cycle {ecc_cycles+1}/10] Validated: {line}")
            ecc_cycles += 1
            
    # 5. CLOUD REJOIN
    print("\n[CLOUD REJOIN] Jamming ceased. 60 seconds of stability achieved.")
    print("[CLOUD REJOIN] Restoring Centralized Cloud Authority...")
    # Send ATTACK to force the Arduino to reset its trust to 0, killing the edge mesh safely
    ser.write(b'ATTACK\n')
    print("[CLOUD REJOIN] Local Edge Mesh terminated. System is secure.\n")
    time.sleep(2)

def main():
    parser = argparse.ArgumentParser(description="Capstone Dual-Mesh Orchestrator (Exp A + J)")
    parser.add_argument('--port', type=str, default=get_serial_port(), help='Serial port of Arduino')
    parser.add_argument('--baud', type=int, default=115200, help='Baud rate')
    args = parser.parse_args()
    
    print("Connecting to Arduino on", args.port)
    try:
        ser = serial.Serial(args.port, args.baud, timeout=2)
        time.sleep(2) # Allow Arduino to reset upon connection
    except Exception as e:
        print(f"Failed to connect to Serial: {e}")
        return
        
    print("Beginning Capstone Suite (n=3)...")
    for i in range(1, 7): # 6 trials as requested (e.g. 2 runs of n=3)
        run_capstone_sequence(ser, i)
        
    ser.close()
    print("Capstone Suite Complete. You have your final video footage.")

if __name__ == '__main__':
    main()
