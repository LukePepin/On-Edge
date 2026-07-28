#!/bin/bash

# ns3_sweep_automation.sh
# Automates the NS-3 M/D/1 EW Queue Saturation parameter sweeps for the thesis

# Navigate to the NS-3 directory
cd ~/ns-3-dev || { echo "NS-3 directory not found at ~/ns-3-dev"; exit 1; }

# Clear previous results to start a fresh dataset
rm -f simulation_results.csv
echo "Starting comprehensive NS-3 M/D/1 EW parameter sweep..."

# Define the variables to sweep
ARRIVAL_RATES=(10 25 50 100 150) # Aggregated cluster frequencies (Hz)
PAYLOAD_SIZES=(64) # Cryptographic payload size locked to 64 bytes (secp256r1)
NODE_COUNTS=(3 5 10 15 20 25 30) # Number of virtual edge nodes pushing the Pi 4
JAMMING_RATES=(0.0 0.1 0.2 0.3) # EW Packet loss (0%, 10%, 20%, 30%) to match Phase 3.5

# Calculate total iterations for progress tracking
TOTAL_TESTS=$((${#ARRIVAL_RATES[@]} * ${#PAYLOAD_SIZES[@]} * ${#NODE_COUNTS[@]} * ${#JAMMING_RATES[@]}))
CURRENT_TEST=1

for lambda in "${ARRIVAL_RATES[@]}"; do
    for payload in "${PAYLOAD_SIZES[@]}"; do
        for nodes in "${NODE_COUNTS[@]}"; do
            for jam in "${JAMMING_RATES[@]}"; do
                echo "[${CURRENT_TEST}/${TOTAL_TESTS}] Testing: Lambda=${lambda}Hz | Payload=${payload}B | Nodes=${nodes} | Jam=${jam}"
                ./ns3 run "scratch/ns3_md1_ew_sim --nNodes=${nodes} --payloadSize=${payload} --lambdaGlobal=${lambda} --ewJammingRate=${jam}" > /dev/null 2>&1
                CURRENT_TEST=$((CURRENT_TEST + 1))
            done
        done
    done
done

echo "Sweep Complete! Dataset generated at ~/ns-3-dev/simulation_results.csv"

# Automatically copy it back to the project folder
cp simulation_results.csv ~/Documents/On-Edge/data/ns3_ew_saturation_sweep.csv
echo "Dataset copied to ~/Documents/On-Edge/data/ns3_ew_saturation_sweep.csv"
