import pandas as pd
import sys

def main():
    try:
        df = pd.read_csv('data/timeseries_evaluation.csv')
    except FileNotFoundError:
        print("Could not find data/timeseries_evaluation.csv")
        sys.exit(1)

    print("=== Timeseries Evaluation Summary ===")
    print(f"Total entries: {len(df)}")
    
    # Analyze by payload size
    print("\n-- Latency by Payload Size --")
    if 'payload_bytes' in df.columns:
        summary = df.groupby('payload_bytes')['latency_ms'].agg(['mean', 'min', 'max', 'count'])
        for payload, row in summary.iterrows():
            print(f"Payload {int(payload)}B: Mean={row['mean']:.2f}ms | Min={row['min']:.2f}ms | Max={row['max']:.2f}ms | Count={int(row['count'])}")
    
    # Check evictions
    if 'evicted' in df.columns:
        evictions = df[df['evicted'] == True]
        if not evictions.empty:
            print("\n-- Eviction Events --")
            for _, row in evictions.iterrows():
                print(f"At t={row['timestamp']:.2f}s: Payload {int(row['payload_bytes'])}B triggered eviction (Latency: {row['latency_ms']:.2f}ms, Trust: {row['trust_score']})")
        else:
            print("\n-- Eviction Events --")
            print("No nodes were evicted during this evaluation.")

if __name__ == "__main__":
    main()
