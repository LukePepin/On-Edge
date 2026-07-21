import pandas as pd
import sys

def main():
    sys.stdout.reconfigure(encoding='utf-8')
    print("=== M/M/1 Queue Variable Extraction ===")
    try:
        df = pd.read_csv('data/timeseries_evaluation.csv')
    except FileNotFoundError:
        print("Error: Could not find data/timeseries_evaluation.csv")
        sys.exit(1)

    # Arrival Rate (λ)
    # The physical system was designed to have a 50Hz kinematic loop (from Phase 3.5 Objective 2)
    # But for the ZKP polling, let's look at the timestamps to see the literal arrival frequency in the CSV
    time_diffs = df['timestamp'].diff().dropna()
    avg_interval_s = time_diffs.mean()
    # In the sweep, we logged 1x per second. But the actual edge node processes continuous streams.
    # We will provide the empirical Service Rate (μ) directly from the latency.
    
    print("\n[Service Rate (μ) by Payload Size]")
    print("Formula: μ = 1000ms / Average Latency (packets per second)\n")
    
    if 'payload_bytes' in df.columns:
        summary = df.groupby('payload_bytes')['latency_ms'].mean()
        for payload, avg_lat in summary.items():
            mu = 1000.0 / avg_lat
            print(f"Payload {int(payload)}B:")
            print(f"  -> Avg Latency: {avg_lat:.2f} ms")
            print(f"  -> Service Rate (μ): {mu:.2f} packets/sec")
            
            # If Arrival Rate (λ) exceeds Service Rate (μ), the queue grows infinitely (Livelock)
            # The UR5 kinematic stream runs at 50Hz (λ = 50)
            lambda_rate = 50.0 
            rho = lambda_rate / mu
            
            status = "STABLE" if rho < 1.0 else "UNSTABLE (LIVELOCK)"
            print(f"  -> Traffic Intensity (ρ) at 50Hz (λ=50): {rho:.2f} [{status}]\n")

if __name__ == "__main__":
    main()
