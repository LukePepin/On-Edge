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

def main():
    print("=====================================================")
    print("   MASTER AUTOMATION ORCHESTRATOR (H1, H2, H3, H4)")
    print("=====================================================")
    
    # The Full Factorial Matrix (36 Configurations)
    algos = ["ZKP", "ECC", "CLOUD"]
    outages = [500, 1000, 2000, 5000]
    alphas = [0.5, 0.7, 0.9]
    
    configurations = list(itertools.product(algos, outages, alphas))
    
    iters = list(range(1, 6))  # N=5 trials per configuration (G*Power requirement)
    
    # Generate schedule
    schedule = []
    for config in configurations:
        for iter_num in iters:
            schedule.append((*config, iter_num))
            
    total_runs = len(schedule)
    
    print(f"Total Trials Scheduled: {total_runs}")
    print("Starting in 5 seconds. Please ensure you are clear of the robot cell!")
    time.sleep(5)
    
    for i, (algo, outage, alpha, iter_num) in enumerate(schedule):
        print(f"\n[{i+1}/{total_runs}] Starting Trial: {algo} | Outage {outage}ms | Alpha {alpha} | Iter {iter_num}")
        
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
            break
            
        # 2. Autonomous Recovery via Dashboard Server
        recover_robot()

if __name__ == "__main__":
    main()
