import pandas as pd
import glob
import os

def main():
    print("Combining v7 Core Campaign Data...")
    
    csv_files = glob.glob('data/trial_ZKP_outage*.csv')
    if not csv_files:
        print("No trial CSV files found for V7")
        return
        
    dfs = []
    for file in csv_files:
        if 'iter99' in file: # skip the smoke test
            continue
            
        basename = os.path.basename(file)
        parts = basename.split('_')
        
        algo = parts[1]
        outage = int(parts[2].replace('outage', ''))
        alpha = float(parts[3].replace('ewma', '')) / 10.0
        iteration = int(parts[4].replace('iter', ''))
        
        df = pd.read_csv(file)
        
        # Add metadata columns
        df['algo'] = algo
        df['outage_ms'] = outage
        df['alpha'] = alpha
        df['iteration'] = iteration
        
        dfs.append(df)
        
    combined_df = pd.concat(dfs, ignore_index=True)
    out_path = 'data/v7_logs/combined_v7_campaign.csv'
    combined_df.to_csv(out_path, index=False)
    print(f"Successfully combined {len(dfs)} files into {out_path}")
    print(f"Total Rows: {len(combined_df)}")

if __name__ == "__main__":
    main()
