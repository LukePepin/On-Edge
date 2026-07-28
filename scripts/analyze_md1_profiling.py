import os
import glob
import csv
import numpy as np

def analyze_profiling_data():
    data_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'data'))
    csv_files = glob.glob(os.path.join(data_dir, 'md1_profiling_*.csv'))
    
    if not csv_files:
        print("No profiling data found!")
        return

    all_latencies_ns = []
    
    for file in csv_files:
        with open(file, 'r') as f:
            reader = csv.reader(f)
            next(reader, None)  # Skip header
            for row in reader:
                if len(row) >= 2:
                    all_latencies_ns.append(int(row[1]))
                    
    if not all_latencies_ns:
        print("No data points found in CSVs.")
        return
        
    latencies_ms = np.array(all_latencies_ns) / 1_000_000.0
    
    mu_avg = np.mean(latencies_ms)
    mu_max = np.max(latencies_ms)
    variance = np.var(latencies_ms)
    c_v = np.std(latencies_ms) / mu_avg if mu_avg > 0 else 0
    
    print("\n" + "="*50)
    print(" 📊 PHASE 1: M/D/1 SERVICE RATE PROFILING EXTRACTED")
    print("="*50)
    print(f"Total Requests Analyzed : {len(latencies_ms)}")
    print(f"Mean Service Time (μ)   : {mu_avg:.4f} ms")
    print(f"Max Service Time        : {mu_max:.4f} ms")
    print(f"Variance (σ²)           : {variance:.6f}")
    print(f"Coefficient of Var (Cv) : {c_v:.6f}")
    print("="*50)
    
    if c_v < 0.1:
        print("✅ SUCCESS: Cv approaches 0. System behaves as a deterministic M/D/1 queue.")
    else:
        print("⚠️ WARNING: High variance detected. Hardware interrupts may be interfering.")

if __name__ == '__main__':
    analyze_profiling_data()
