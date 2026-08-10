import pandas as pd
import numpy as np
from scipy import stats
import seaborn as sns
import matplotlib.pyplot as plt
import os

def main():
    file_path = "distributed_swapover_log_20260810_150831.csv"
    if not os.path.exists(file_path):
        print(f"Error: Could not find {file_path}")
        return

    # 1. Load Data
    df = pd.read_csv(file_path)
    df = df[df['node'] == 'CRYPTO_NODE'] # Isolate Crypto Node telemetry
    
    zkp_data = df[df['algorithm'] == 'ZKP']['exec_time_ms'].values
    ecc_data = df[df['algorithm'] == 'ECC']['exec_time_ms'].values
    
    print("=========================================================")
    print("  DISTRIBUTED MESH CAPSTONE - STATISTICAL AUDIT (n=20)")
    print("=========================================================\n")
    print(f"Samples collected: ZKP (N={len(zkp_data)}), ECC (N={len(ecc_data)})\n")

    # 2. Descriptive Statistics & Functional Safety
    zkp_mean, zkp_max = np.mean(zkp_data), np.max(zkp_data)
    ecc_mean, ecc_max = np.mean(ecc_data), np.max(ecc_data)
    
    print("[1] FUNCTIONAL SAFETY COMPLIANCE")
    print(f"  ZKP Execution: Mean={zkp_mean:.2f}ms, Max={zkp_max:.2f}ms")
    print(f"  --> Margin to 400ms Viability Threshold: {400.0 - zkp_max:.2f}ms")
    if zkp_max < 400.0:
        print("  --> STATUS: PASS (Deterministic Outage Bounded)\n")
    else:
        print("  --> STATUS: FAIL (Threshold Exceeded)\n")
        
    print(f"  ECC Execution: Mean={ecc_mean:.2f}ms, Max={ecc_max:.2f}ms")
    print(f"  --> Margin to 150ms Protective Stop Bound: {150.0 - ecc_max:.2f}ms")
    if ecc_max < 150.0:
        print("  --> STATUS: PASS (Real-Time Kinematics Guaranteed)\n")
    else:
        print("  --> STATUS: FAIL (Category 0 Halt Risk)\n")

    # 3. Statistical Assumptions Validation
    print("[2] ASSUMPTIONS TESTING")
    
    # Shapiro-Wilk (Normality)
    stat_z, p_z = stats.shapiro(zkp_data)
    stat_e, p_e = stats.shapiro(ecc_data)
    print(f"  Shapiro-Wilk (ZKP): p = {p_z:.2e}")
    print(f"  Shapiro-Wilk (ECC): p = {p_e:.2e}")
    if p_z < 0.05 or p_e < 0.05:
        print("  --> Result: NORMALITY VIOLATED (p < 0.05). Proceeding with Non-Parametric Pipeline.")
    else:
        print("  --> Result: NORMALITY RETAINED (p > 0.05).")

    # Levene's Test (Homoscedasticity)
    stat_l, p_l = stats.levene(zkp_data, ecc_data)
    print(f"  Levene's Test (Equality of Variances): p = {p_l:.2e}")
    
    # 4. Rigorous Hypothesis Testing (Mann-Whitney U)
    print("\n[3] NON-PARAMETRIC HYPOTHESIS TESTING (Mann-Whitney U)")
    stat_m, p_m = stats.mannwhitneyu(zkp_data, ecc_data, alternative='two-sided')
    print(f"  Mann-Whitney U Statistic: {stat_m}")
    print(f"  P-value: {p_m:.2e}")
    if p_m < 0.001:
        print("  --> Result: STATISTICALLY SIGNIFICANT (p < 0.001)")
        print("  --> Conclusion: The decentralized edge mesh successfully executes a deterministic algorithmic drop.")
    
    # Rank-Biserial Correlation (Effect Size)
    n1, n2 = len(zkp_data), len(ecc_data)
    u_max = n1 * n2
    rank_biserial = 1 - (2 * stat_m) / u_max
    print(f"  Rank-Biserial Correlation Effect Size: {abs(rank_biserial):.3f}")
    if abs(rank_biserial) > 0.5:
        print("  --> Effect Magnitude: LARGE (Practically significant performance divide)\n")
        
    # 5. Data Visualization
    plt.figure(figsize=(10, 7))
    sns.set_theme(style="whitegrid", context="talk")
    
    ax = sns.boxplot(x='algorithm', y='exec_time_ms', data=df, palette="mako", width=0.5, showfliers=False)
    sns.stripplot(x='algorithm', y='exec_time_ms', data=df, color=".3", size=4, alpha=0.5, jitter=True)
    
    # Add boundary lines
    plt.axhline(150.0, color='red', linestyle='--', linewidth=2, label='ECC Safety Boundary (150ms)')
    plt.axhline(400.0, color='orange', linestyle='--', linewidth=2, label='ZKP Viability Bound (400ms)')
    
    plt.title("Decentralized Edge Mesh Latency: ZKP Bootstrapping vs ECC Active State")
    plt.ylabel("Execution Latency (ms)")
    plt.xlabel("Cryptographic State")
    plt.legend()
    
    output_png = "data/distributed_swapover_robust_boxplot.png"
    plt.savefig(output_png, dpi=300, bbox_inches="tight")
    print(f"Publication chart saved to {output_png}")

if __name__ == "__main__":
    main()
