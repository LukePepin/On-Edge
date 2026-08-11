import serial
import json
import csv
import time
import sys
import os
import numpy as np
from scipy import stats

PORT = 'COM32'  # Change to /dev/ttyACM0 on the Raspberry Pi
BAUD = 115200
RUNS = 300
PAYLOAD_BYTES = 64
CYCLES_PER_MS = 64000.0
OUTPUT_FILE = 'data/real_zkp_profiling.csv'

def main():
    print(f"Connecting to ZKP Profiler on {PORT}...")
    try:
        ser = serial.Serial(PORT, BAUD, timeout=2)
    except serial.SerialException as e:
        print(f"Failed to connect: {e}")
        print("Please check the PORT variable or ensure the Arduino is plugged in.")
        sys.exit(1)

    time.sleep(2)  # Wait for Arduino reboot on serial connection
    ser.reset_input_buffer()

    print(f"Starting {RUNS} genuine cryptographic execution cycles...")
    os.makedirs('data', exist_ok=True)
    
    exec_times_ms = []

    with open(OUTPUT_FILE, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['cycle', 'start_cycles', 'end_cycles', 'total_cycles', 'exec_time_ms', 'res1', 'res2', 'keybyte'])
        
        valid_runs = 0
        i = 0
        
        while valid_runs < RUNS:
            i += 1
            # 1. Generate fresh random data on the host
            payload = os.urandom(PAYLOAD_BYTES)
            
            # 2. Transmit to Arduino
            ser.write(payload)
            ser.flush()
            
            # 3. Read response
            response = ser.readline().decode('utf-8').strip()
            
            try:
                data = json.loads(response)
                start = data['start']
                end = data['end']
                res1 = data.get('res1', 1)
                res2 = data.get('res2', 1)
                keybyte = data.get('keybyte', 0)
                
                # uECC_compute_public_key returns 0 if the random 32 bytes aren't a valid private key.
                # A rejected key returns almost instantly, contaminating timing. Drop these.
                if res1 == 0 or res2 == 0:
                    continue
                    
                total_cycles = end - start
                exec_time_ms = total_cycles / CYCLES_PER_MS
                
                exec_times_ms.append(exec_time_ms)
                writer.writerow([valid_runs, start, end, total_cycles, exec_time_ms, res1, res2, keybyte])
                
                valid_runs += 1
                
                # Print every 25th run to show progress
                if valid_runs % 25 == 0:
                    print(f"Completed {valid_runs}/{RUNS} runs...")
                    
            except json.JSONDecodeError:
                print(f"Malformed response from Arduino: {response}")
                
            time.sleep(0.01)

    # Statistical Analysis
    exec_times_ms = np.array(exec_times_ms)
    
    mean = np.mean(exec_times_ms)
    sd = np.std(exec_times_ms)
    min_val = np.min(exec_times_ms)
    max_val = np.max(exec_times_ms)
    p95 = np.percentile(exec_times_ms, 95)
    
    print("\n==================================================")
    print(f"PROFILING COMPLETE: {RUNS} Runs")
    print(f"Saved raw log to {OUTPUT_FILE}")
    print("==================================================")
    print(f"Mean:   {mean:.2f} ms")
    print(f"SD:     {sd:.2f} ms")
    print(f"Min:    {min_val:.2f} ms")
    print(f"Max:    {max_val:.2f} ms")
    print(f"95th %: {p95:.2f} ms")
    print("==================================================")
    
    # Shapiro-Wilk test for normality
    stat, p = stats.shapiro(exec_times_ms)
    print("\nShapiro-Wilk Normality Test:")
    print(f"Statistic: {stat:.4f}, p-value: {p:.4e}")
    if p > 0.05:
        print("Result: Distribution appears Normal (Gaussian).")
    else:
        print("Result: Distribution is NOT Normal.")
        print("  --> This is a real finding! Cryptographic workloads often exhibit")
        print("      heavy-tailed distributions on bare metal due to data-dependent")
        print("      arithmetic operations (e.g. modular reductions).")

    print("\nNext Steps:")
    print("Use the 95th percentile or max execution time in your latency model:")
    print("T_stop = cycle_time * ceil(log(0.3) / log(1 - alpha))")

if __name__ == "__main__":
    main()
