import pandas as pd
import numpy as np

def main():
    print("--- V6 Sub-Eviction Sweep Results ---")
    df = pd.read_csv('data/v6_logs/sub_eviction_summary.csv')
    
    # Calculate stop rate for each outage/alpha combination
    results = df.groupby(['outage_ms', 'alpha']).agg(
        total_trials=('stop_occurred', 'count'),
        stops=('stop_occurred', 'sum'),
        avg_min_trust=('min_trust', 'mean'),
        std_min_trust=('min_trust', 'std')
    ).reset_index()
    
    results['stop_rate'] = (results['stops'] / results['total_trials']) * 100
    
    print("\nStop Rate Table:")
    print(results[['outage_ms', 'alpha', 'stops', 'total_trials', 'stop_rate', 'avg_min_trust']])
    
    # Mathematical crossover prediction:
    # 50Hz control loop -> cycle_time = 20ms
    # But wait, python logger is 50Hz (20ms), Arduino telemetry is 50Hz?
    cycle_time = 20.0
    
    print("\nTheoretical Crossover Boundaries (assuming 20ms cycle time):")
    for alpha in sorted(df['alpha'].unique()):
        # boundary = cycle_time * ceil(log(0.3)/log(1 - alpha))
        boundary = cycle_time * np.ceil(np.log(0.3) / np.log(1 - alpha))
        print(f"Alpha {alpha}: stops should occur at Outage >= {boundary} ms")

if __name__ == "__main__":
    main()
