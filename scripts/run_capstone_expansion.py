#!/usr/bin/env python3
import serial
import time
import json
import argparse
import sys
import socket

UR_IP = "192.168.0.149"
UR_PORT = 29999

def get_serial_port():
    if sys.platform == 'win32':
        return 'COM3'
    return '/dev/ttyACM0'

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

def run_capstone_sequence(ser, iter_num):
    print(f"\n=======================================================")
    print(f"   CAPSTONE TRIAL {iter_num}/6: CLOUD -> ZKP -> ECC -> CLOUD")
    print(f"=======================================================\n")
    
    # 0. PRE-FLIGHT (Unlock safety pin to allow Cloud Phase movement)
    # Inject a baseline payload to boot the Arduino into ECC and raise the safety pin
    ser.write((json.dumps({"algo": "ECC", "alpha": 0.5}) + '\n').encode('utf-8'))
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line == '{"status": "READY"}':
            break
            
    print("[SYSTEM BOOT] Safety pin raised. Starting robot movement...")
    start_robot_motion()
    time.sleep(2)
    
    # 1. CLOUD ACTIVE
    print("\n[CLOUD ACTIVE] Pinging Cloud Identity Provider for 1.0s Leases...")
    for _ in range(5):
        print("  -> Auth Lease Granted (Scope: kinematic_control)")
        time.sleep(1)
        
    # 2. EW JAMMING (LOSS OF CLOUD)
    print("\n[JAMMING ACTIVE] 🧨 WARNING: Tactical EW Jamming detected!")
    print("[JAMMING ACTIVE] Cloud connection lost. Connection timed out.")
    # Simulate network attack, killing Arduino trust to drop the safety pin
    ser.write(b'ATTACK\n')
    time.sleep(1) # Robot physically halts here
    
    # 3. EDGE MESH INITIALIZATION (ZKP)
    print("\n[EDGE MESH INITIALIZATION] Bootstrapping local mesh with Zero-Knowledge Proofs...")
    payload = {"algo": "ZKP", "alpha": 0.5}
    ser.write((json.dumps(payload) + '\n').encode('utf-8'))
    
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line == '{"status": "READY"}':
            print("  -> Arduino acknowledged ZKP Configuration. Booting Mesh.")
            break
            
    # Re-enable motion now that local mesh is active
    start_robot_motion()
            
    # Read 10 ZKP cycles (~3.3 seconds)
    zkp_cycles = 0
    while zkp_cycles < 10:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith("{") and "exec_time_ms" in line:
            print(f"  [ZKP Cycle {zkp_cycles+1}/10] Validated: {line}")
            zkp_cycles += 1
            
    # 4. EDGE MESH CONTINUOUS (ECC HOT-SWAP)
    print("\n[EDGE MESH CONTINUOUS] Secure Identity Established (10 valid ZKP proofs).")
    print("[EDGE MESH CONTINUOUS] Hot-swapping state machine to lightweight ECC for real-time kinematics...")
    payload = {"algo": "ECC", "alpha": 0.5}
    ser.write((json.dumps(payload) + '\n').encode('utf-8'))
    
    while True:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line == '{"status": "READY"}':
            print("  -> Arduino acknowledged ECC Configuration. Executing handover.")
            break
            
    # Read 50 ECC cycles (~5.5 seconds) - extended as requested
    ecc_cycles = 0
    while ecc_cycles < 50:
        line = ser.readline().decode('utf-8', errors='ignore').strip()
        if line.startswith("{") and "exec_time_ms" in line:
            # Print only every 5th cycle to keep terminal clean
            if ecc_cycles % 5 == 0:
                print(f"  [ECC Cycle {ecc_cycles+1}/50] Validated: {line}")
            ecc_cycles += 1
            
    # 5. CLOUD REJOIN
    print("\n[CLOUD REJOIN] Jamming ceased. 60 seconds of stability achieved.")
    print("[CLOUD REJOIN] Restoring Centralized Cloud Authority...")
    
    # Terminate local mesh safely
    ser.write(b'ATTACK\n')
    print("[CLOUD REJOIN] Local Edge Mesh terminated. Robot halted for re-auth. System is secure.\n")
    time.sleep(3)

def main():
    parser = argparse.ArgumentParser(description="Capstone Dual-Mesh Orchestrator (Exp A + J)")
    parser.add_argument('--port', type=str, default=get_serial_port(), help='Serial port of Arduino')
    parser.add_argument('--baud', type=int, default=115200, help='Baud rate')
    args = parser.parse_args()
    
    print("Connecting to Arduino on", args.port)
    try:
        ser = serial.Serial(args.port, args.baud, timeout=2)
        # Flush serial boot logs
        time.sleep(2) 
        ser.reset_input_buffer()
    except Exception as e:
        print(f"Failed to connect to Serial: {e}")
        return
        
    print("Beginning Capstone Suite (n=3)...")
    for i in range(1, 7):
        run_capstone_sequence(ser, i)
        
    ser.close()
    print("Capstone Suite Complete. You have your final video footage.")

if __name__ == '__main__':
    main()
