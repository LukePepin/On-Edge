#!/usr/bin/env python3
import subprocess
import time
import socket
import itertools
import os

UR_IP = "192.168.0.149"
UR_PORT = 29999

def dashboard_cmd(cmd):
    print(f"[Dashboard] Sending: {cmd.strip()}")
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(2.0)
        s.connect((UR_IP, UR_PORT))
        s.sendall(cmd.encode('utf-8'))
        response = s.recv(1024).decode('utf-8')
        print(f"[Dashboard] Response: {response.strip()}")
        s.close()
        return True
    except Exception as e:
        print(f"[Dashboard] Error sending '{cmd.strip()}': {e}")
        return False

def recover_robot():
    print("\n--- AUTOMATIC RECOVERY SEQUENCE ---")
    time.sleep(2)  # Give the Arduino time to reset the Optocoupler HIGH (Green)
    
    # 1. Unlock Protective Stop
    dashboard_cmd("unlock protective stop\n")
    time.sleep(2)
    
    # 2. Start the URCap program again
    dashboard_cmd("play\n")
    time.sleep(3)
    
    # Wait for controllers to be fully active before bash takes over
    print("--- RECOVERY COMPLETE, PROCEEDING TO NEXT TRIAL ---\n")

import glob
import csv

def validate_trial(algo, outage, alpha, iter_num):
    search_pattern = f"data/trial_{algo}_outage{outage}_ewma{int(alpha*10)}_iter{iter_num}_*.csv"
    files = glob.glob(search_pattern)
    if not files:
        print("[Validator] No CSV found.")
        return False
        
    latest_file = max(files, key=os.path.getctime)
    try:
        with open(latest_file, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            # Map column indices
            t_sec_idx = headers.index('timestamp_sec')
            t_nano_idx = headers.index('timestamp_nanosec')
            trust_idx = headers.index('trust_score')
            attack_idx = headers.index('attack_active')
            pos_indices = [headers.index(f) for f in ['shoulder_pan_pos', 'shoulder_lift_pos', 'elbow_pos', 'wrist_1_pos', 'wrist_2_pos', 'wrist_3_pos']]
            
            rows = list(reader)
            if len(rows) < 50: return False
            
            t0 = float(rows[0][t_sec_idx]) + (float(rows[0][t_nano_idx]) * 1e-9)
            
            attack_t = None
            eviction_t = None
            consecutive_still_frames = 0
            
            for i in range(1, len(rows)):
                curr_row = rows[i]
                prev_row = rows[i-1]
                
                t = (float(curr_row[t_sec_idx]) + (float(curr_row[t_nano_idx]) * 1e-9)) - t0
                attack = int(curr_row[attack_idx])
                trust = float(curr_row[trust_idx])
                
                if attack_t is None and attack == 1:
                    attack_t = t
                    
                if attack_t is not None and eviction_t is None and trust <= 30.0:
                    eviction_t = t
                    
                # Calculate pos_diff
                pos_diff = sum(abs(float(curr_row[j]) - float(prev_row[j])) for j in pos_indices)
                
                if eviction_t is not None and t > eviction_t:
                    if pos_diff < 0.025:
                        consecutive_still_frames += 1
                        if consecutive_still_frames >= 10:
                            return True
                    else:
                        consecutive_still_frames = 0
                        
        return False
    except Exception as e:
        print(f"[Validator] Exception parsing CSV: {e}")
        return False

def main():
    print("=====================================================")
    print("   MASTER AUTOMATION ORCHESTRATOR (H1, H2, H3, H4)")
    print("=====================================================")
    
    # The Full Factorial Matrix (24 Configurations)
    algos = ["ZKP", "ECC"]
    outages = [500, 1000, 2000, 5000]
    alphas = [0.5, 0.7, 0.9]
    
    configurations = list(itertools.product(algos, outages, alphas))
    
    print(f"Total Configurations Scheduled: {len(configurations)}")
    print("Starting in 5 seconds. Please ensure you are clear of the robot cell!")
    time.sleep(5)
    
    for config_idx, (algo, outage, alpha) in enumerate(configurations):
        valid_runs = 0
        iter_num = 1
        
        while valid_runs < 5:
            print(f"\n[Config {config_idx+1}/{len(configurations)}] Starting Trial: {algo} | Outage {outage}ms | Alpha {alpha} | Valid N: {valid_runs}/5 (Attempt {iter_num})")
            
            # 1. Execute the trial via bash
            cmd = [
                "./scripts/run_test.sh",
                "--algo", algo,
                "--outage", str(outage),
                "--iter", str(iter_num),
                "--alpha", str(alpha)
            ]
            
            try:
                # We use check=True so if bash fails entirely, we stop the campaign.
                subprocess.run(cmd, check=True)
            except subprocess.CalledProcessError as e:
                print(f"Trial failed with exit code {e.returncode}. Aborting campaign.")
                return
                
            # 2. Validate the Trial
            if validate_trial(algo, outage, alpha, iter_num):
                print(f"✅ Trial mathematically valid! Incrementing Valid N.")
                valid_runs += 1
            else:
                print(f"❌ Trial discarded (failed standstill bounds or missed eviction). Retrying.")
            
            iter_num += 1
            
            # 3. Autonomous Recovery via Dashboard Server
            recover_robot()

if __name__ == "__main__":
    main()
