#!/usr/bin/env python3
import os
import glob
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sys

def plot_latest_trial():
    # Find the most recently generated CSV in the data directory
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'data')
    csv_files = glob.glob(os.path.join(data_dir, '*.csv'))
    
    if not csv_files:
        print(f"No CSV files found in {data_dir}. Run a trial first!")
        sys.exit(1)
        
    latest_file = max(csv_files, key=os.path.getctime)
    print(f"Loading telemetry from: {os.path.basename(latest_file)}")
    
    # Load the data
    df = pd.read_csv(latest_file)
    
    # Calculate a clean relative time array (starting at t=0)
    # The nanosec column needs to be padded to 9 digits to accurately construct the float
    df['time_absolute'] = df['timestamp_sec'] + (df['timestamp_nanosec'] * 1e-9)
    df['time'] = df['time_absolute'] - df['time_absolute'].iloc[0]
    
    # Down-sample for smoother interactive performance in browser
    # 50Hz data can get heavy over 60 trials; we plot every 2nd row (25Hz) if file is large
    if len(df) > 500:
        df = df.iloc[::2, :]
        print("Down-sampled dataset for smooth Plotly rendering.")

    # Create subplots: 
    # Top: Trust Score (Gamma)
    # Bottom: Deceleration (EMA Filtered IMU)
    fig = make_subplots(
        rows=2, cols=1, 
        shared_xaxes=True,
        vertical_spacing=0.1,
        subplot_titles=("Cryptographic Trust Decay (Γ)", "Mechanical Deceleration (EMA Filtered)")
    )

    # Plot Trust Score
    fig.add_trace(
        go.Scatter(
            x=df['time'], y=df['trust_score'], 
            name="Trust Score", 
            line=dict(color='crimson', width=3, shape='hv'),
            fill='tozeroy'
        ),
        row=1, col=1
    )

    # Plot EMA Filtered IMU Acceleration (ax, ay, az)
    fig.add_trace(
        go.Scatter(x=df['time'], y=df['imu_ax_ema'], name="a_x (EMA)", line=dict(color='royalblue', width=2)),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['time'], y=df['imu_ay_ema'], name="a_y (EMA)", line=dict(color='darkorange', width=2)),
        row=2, col=1
    )
    fig.add_trace(
        go.Scatter(x=df['time'], y=df['imu_az_ema'], name="a_z (EMA)", line=dict(color='mediumseagreen', width=2)),
        row=2, col=1
    )

    # Styling and Layout
    fig.update_layout(
        title_text=f"Real-Time Telemetry Dashboard | {os.path.basename(latest_file)}",
        height=800,
        hovermode="x unified",
        template="plotly_dark",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    fig.update_yaxes(title_text="Trust (%)", range=[-5, 105], row=1, col=1)
    fig.update_yaxes(title_text="Acceleration (m/s²)", row=2, col=1)
    fig.update_xaxes(title_text="Time (seconds)", row=2, col=1)

    # Save to HTML and automatically open in browser
    output_html = os.path.join(data_dir, "latest_telemetry_dashboard.html")
    fig.write_html(output_html)
    print(f"✅ Dashboard generated: {output_html}")
    
    # Attempt to open it in the default web browser (works natively on Windows)
    import webbrowser
    webbrowser.open(f"file://{output_html}")

if __name__ == '__main__':
    plot_latest_trial()
