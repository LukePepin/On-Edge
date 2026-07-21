#!/bin/bash

# ns3_sweep_automation.sh
# Automates the NS-3 M/M/1 Queue Livelock parameter sweeps for the thesis

# Navigate to the NS-3 directory
cd ~/ns-3-dev || { echo "NS-3 directory not found at ~/ns-3-dev"; exit 1; }

# Clear previous results to start a fresh dataset
rm -f simulation_results.csv
echo "Starting comprehensive NS-3 M/M/1 parameter sweep..."

# Define the variables to sweep
ARRIVAL_RATES=(10 50 100) # Kinematic frequencies (Hz)
PAYLOAD_SIZES=(1 8 32 64) # Cryptographic payload sizes (Bytes)
NODE_COUNTS=(5 10 15 20 50 100 200) # Number of virtual edge nodes

# Calculate total iterations for progress tracking
TOTAL_TESTS=$((${#ARRIVAL_RATES[@]} * ${#PAYLOAD_SIZES[@]} * ${#NODE_COUNTS[@]}))
CURRENT_TEST=1

for lambda in "${ARRIVAL_RATES[@]}"; do
    for payload in "${PAYLOAD_SIZES[@]}"; do
        for nodes in "${NODE_COUNTS[@]}"; do
            echo "[${CURRENT_TEST}/${TOTAL_TESTS}] Testing: Lambda=${lambda}Hz | Payload=${payload}B | Nodes=${nodes}"
            ./ns3 run "scratch/ns3_mm1_livelock_sim --nNodes=${nodes} --payloadSize=${payload} --lambdaGlobal=${lambda}" > /dev/null 2>&1
            CURRENT_TEST=$((CURRENT_TEST + 1))
        done
    done
done

echo "Sweep Complete! Dataset generated at ~/ns-3-dev/simulation_results.csv"

# Automatically copy it back to the project folder
cp simulation_results.csv ~/Documents/On-Edge/data/ns3_livelock_sweep_massive.csv
echo "Dataset copied to ~/Documents/On-Edge/data/ns3_livelock_sweep_massive.csv"
