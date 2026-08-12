#!/usr/bin/env python3
import subprocess
import time
import socket
import itertools
import os
import argparse

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
        return False, False, 100.0
        
    latest_file = max(files, key=os.path.getctime)
    try:
        with open(latest_file, 'r') as f:
            reader = csv.reader(f)
            headers = next(reader)
            
            trust_idx = headers.index('trust_score')
            attack_idx = headers.index('attack_active')
            
            rows = list(reader)
            if len(rows) < 50: return False, False, 100.0
            
            attack_fired = False
            stop_occurred = False
            min_trust = 100.0
            
            for row in rows:
                attack = int(row[attack_idx])
                trust = float(row[trust_idx])
                
                if attack == 1:
                    attack_fired = True
                    
                if attack_fired:
                    if trust < min_trust:
                        min_trust = trust
                        
                    if trust <= 30.0:
                        stop_occurred = True
                        
        return attack_fired, stop_occurred, min_trust
    except Exception as e:
        print(f"[Validator] Exception parsing CSV: {e}")
        return False, False, 100.0

import random
import itertools

def main():
    parser = argparse.ArgumentParser(description="Master Automation Orchestrator")
    parser.add_argument('--half', type=int, choices=[1, 2], help="Which half of the test to run (1 or 2)")
    args = parser.parse_args()

    print("=====================================================")
    print("   MASTER AUTOMATION ORCHESTRATOR (V7 Real-ZKP Confirmatory Campaign)")
    # The V7 Real-ZKP Confirmatory Matrix (75 trials)
    algos = ["ZKP"]
    outages = [250, 500, 1000, 3000, 5000] # Attack Duration (ms)
    alphas = [0.1, 0.3, 0.5]
    iters = list(range(1, 6))
    
    configurations = list(itertools.product(algos, outages, alphas))
    
    # 1. Generate a Flat Matrix of 120 scheduled runs
    schedule = []
    for config in configurations:
        for iter_num in iters:
            schedule.append({
                'algo': config[0],
                'outage': config[1],
                'alpha': config[2],
                'iter_num': iter_num,
                'attempt': 1
            })
            
    print(f"Total Unique Configurations: {len(configurations)}")
    print(f"Total Physical Trials Scheduled: {len(schedule)}")
    print("Applying pseudo-random shuffle (seed=42) to guarantee ANOVA i.i.d. error independence...")
    
    # 2. Apply Initial Shuffle (Deterministic seed so both halves align)
    random.seed(42)
    random.shuffle(schedule)
    
    # Slice the schedule if requested
    if args.half == 1:
        schedule = schedule[:len(schedule)//2]
        print(f"--- RUNNING FIRST HALF ({len(schedule)} Trials) ---")
    elif args.half == 2:
        schedule = schedule[len(schedule)//2:]
        print(f"--- RUNNING SECOND HALF ({len(schedule)} Trials) ---")
    
    target_runs = len(schedule)
    valid_runs_completed = 0
    
    print("Starting in 5 seconds. Please ensure you are clear of the robot cell!")
    time.sleep(5)
    
    # 3. Pop and Execute with Dynamic Handoff
    while len(schedule) > 0:
        trial = schedule.pop(0)
        algo = trial['algo']
        outage = trial['outage']
        alpha = trial['alpha']
        iter_num = trial['iter_num']
        attempt = trial['attempt']
        
        print(f"\n[{valid_runs_completed+1}/{target_runs}] Starting Trial: {algo} | Outage/Spoof {outage}ms | Alpha {alpha} | Iter {iter_num} (Attempt {attempt})")
        print(f"Remaining in Randomized Queue: {len(schedule) + 1}")
        
        cmd = [
            "./scripts/run_test.sh",
            "--algo", algo,
            "--outage", str(outage),
            "--iter", str(iter_num),
            "--alpha", str(alpha)
        ]
        
        try:
            subprocess.run(cmd, check=True)
        except subprocess.CalledProcessError as e:
            print(f"Trial failed with exit code {e.returncode}. Aborting campaign.")
            return
            
        # 4. Dynamic Self-Healing Catch
        valid, stop_occurred, min_trust = validate_trial(algo, outage, alpha, iter_num)
        if valid:
            print(f"✅ Trial mathematically valid! Stop occurred: {stop_occurred}, Min Trust: {min_trust:.2f}")
            valid_runs_completed += 1
            
            # Log to sub-eviction summary
            summary_file = 'data/sub_eviction_summary.csv'
            file_exists = os.path.isfile(summary_file)
            with open(summary_file, 'a', newline='', encoding='utf-8') as sf:
                swriter = csv.writer(sf)
                if not file_exists:
                    swriter.writerow(['algo', 'outage_ms', 'alpha', 'iter_num', 'stop_occurred', 'min_trust'])
                swriter.writerow([algo, outage, alpha, iter_num, int(stop_occurred), min_trust])
                
        else:
            # 5. Reshuffle the Remainder
            print("❌ Trial discarded (Attack failed to fire or telemetry corrupted).")
            print("Appending replacement to the queue and reshuffling...")
            trial['attempt'] += 1
            schedule.append(trial)
            random.shuffle(schedule)  # Reshuffle the remaining pool
            
        # Autonomous Recovery via Dashboard Server
        recover_robot()

if __name__ == "__main__":
    main()
