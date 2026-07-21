import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import os

def generate_thesis_graphs():
    print("Generating Academic Graphs from NS-3 Telemetry...")
    
    # Load dataset
    csv_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'ns3_livelock_sweep_massive.csv')
    docs_path = os.path.join(os.path.dirname(__file__), '..', 'docs')
    
    try:
        df = pd.read_csv(csv_path)
    except FileNotFoundError:
        print(f"Error: Could not find {csv_path}")
        return

    # Set thesis-friendly seaborn style
    sns.set_theme(style="whitegrid", context="paper", font_scale=1.2)

    # Reconstruct the Global Kinematic Frequency (lambda) since the CSV stores the per-node lambda
    # We round it to handle floating point precision issues (e.g., 49.999 -> 50.0)
    df['GlobalLambda'] = (df['ArrivalRate'] * df['Nodes']).round(0)

    # For the main thesis graphs, we isolate the 50Hz robotic kinematic baseline
    df_50hz = df[df['GlobalLambda'] == 50.0].copy()

    if df_50hz.empty:
        print("No 50Hz data found in the CSV to plot.")
        return

    # ---------------------------------------------------------
    # GRAPH 1: The Livelock Mathematical Boundary (Traffic Intensity)
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=df_50hz, 
        x='Nodes', 
        y='TrafficIntensity', 
        hue='PayloadSize', 
        palette='viridis', 
        marker='o',
        linewidth=2.5
    )

    # Draw the Livelock failure boundary at rho = 1.0
    plt.axhline(y=1.0, color='red', linestyle='--', linewidth=2, label='Livelock Boundary (ρ = 1.0)')
    
    plt.title("Decentralized Cluster Scalability (50Hz Kinematic Load)", fontsize=16, fontweight='bold')
    plt.xlabel("Active Edge Nodes (N)", fontsize=14)
    plt.ylabel("Traffic Intensity (ρ = λ / μ)", fontsize=14)
    plt.legend(title="Payload Size (Bytes)")
    plt.tight_layout()
    
    boundary_graph_path = os.path.join(docs_path, 'livelock_boundary.png')
    plt.savefig(boundary_graph_path, dpi=300)
    print(f"Saved: {boundary_graph_path}")

    # ---------------------------------------------------------
    # GRAPH 2: The Physical Latency Explosion
    # ---------------------------------------------------------
    plt.figure(figsize=(10, 6))
    sns.lineplot(
        data=df_50hz, 
        x='Nodes', 
        y='AvgDelayMs', 
        hue='PayloadSize', 
        palette='magma', 
        marker='s',
        linewidth=2.5
    )

    plt.title("M/M/1 Queue Latency Explosion", fontsize=16, fontweight='bold')
    plt.xlabel("Active Edge Nodes (N)", fontsize=14)
    plt.ylabel("Average Queue Delay (ms)", fontsize=14)
    plt.yscale("log") # Log scale because latency spikes into the thousands
    plt.legend(title="Payload Size (Bytes)")
    plt.tight_layout()
    
    latency_graph_path = os.path.join(docs_path, 'latency_explosion.png')
    plt.savefig(latency_graph_path, dpi=300)
    print(f"Saved: {latency_graph_path}")

if __name__ == "__main__":
    generate_thesis_graphs()
