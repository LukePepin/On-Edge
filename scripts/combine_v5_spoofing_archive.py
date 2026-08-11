import os
import glob
import subprocess
import shutil

def combine_csv_files(input_dir, output_csv):
    print(f"Combining CSV files from {input_dir} into {output_csv}...")
    csv_files = glob.glob(os.path.join(input_dir, "*.csv"))
    
    if not csv_files:
        print("No CSV files found.")
        return

    # Sort files to maintain chronological/alphabetical order
    csv_files.sort()

    with open(output_csv, 'w', encoding='utf-8') as outfile:
        # Write the header from the first file
        with open(csv_files[0], 'r', encoding='utf-8') as first_file:
            header = first_file.readline().strip()
            # Append new columns to the header
            outfile.write(header + ",algo,outage_ms,ewma_alpha,iteration,timestamp\n")

        # Process each file line-by-line to inject the parameters
        for file in csv_files:
            # Expected filename: trial_ZKP_outage5000_ewma1_iter2_1786135368.csv
            basename = os.path.basename(file)
            parts = basename.replace(".csv", "").split("_")
            
            try:
                algo = parts[1]
                outage = parts[2].replace("outage", "")
                ewma = parts[3].replace("ewma", "")
                iteration = parts[4].replace("iter", "")
                timestamp = parts[5]
                param_string = f",{algo},{outage},{ewma},{iteration},{timestamp}\n"
            except IndexError:
                # Fallback if a filename doesn't perfectly match the pattern
                param_string = f",{basename},unknown,unknown,unknown,unknown\n"

            with open(file, 'r', encoding='utf-8') as infile:
                infile.readline() # Skip the original header
                for line in infile:
                    # Strip any existing newlines from the line, then append parameters and a new newline
                    outfile.write(line.strip() + param_string)
                
    print(f"Successfully combined {len(csv_files)} CSV files into {output_csv}")

def combine_pcap_files(input_dir, output_pcap):
    print(f"\nCombining PCAP files from {input_dir} into {output_pcap}...")
    pcap_files = glob.glob(os.path.join(input_dir, "*.pcap"))
    
    if not pcap_files:
        print("No PCAP files found.")
        return

    pcap_files.sort()
    
    # PCAP files are binary and have headers, they CANNOT be simply concatenated like text.
    # We must use 'mergecap' (a command-line tool included with Wireshark/tshark).
    mergecap_paths = [
        "mergecap", # If it's in the PATH
        r"C:\Program Files\Wireshark\mergecap.exe",
        r"C:\Program Files (x86)\Wireshark\mergecap.exe"
    ]
    
    mergecap_exe = None
    for path in mergecap_paths:
        try:
            subprocess.run([path, "-V"], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            mergecap_exe = path
            break
        except FileNotFoundError:
            continue
            
    if not mergecap_exe:
        print("Error: 'mergecap' (Wireshark) is required to safely merge PCAP files without corrupting headers.")
        print("Please install Wireshark or ensure mergecap is in your system PATH, then re-run this script.")
        print("Skipping PCAP merge.")
        return
        
    cmd = [mergecap_exe, "-w", output_pcap] + pcap_files
    
    print(f"Running mergecap with {len(pcap_files)} files...")
    try:
        subprocess.run(cmd, check=True)
        print(f"Successfully combined {len(pcap_files)} PCAP files into {output_pcap}")
    except subprocess.CalledProcessError as e:
        print(f"Failed to merge PCAP files: {e}")

if __name__ == "__main__":
    archive_dir = os.path.join("data", "v5_spoofing_archive")
    
    if not os.path.exists(archive_dir):
        print(f"Directory not found: {archive_dir}")
        exit(1)
        
    combined_csv = os.path.join("data", "combined_v5_spoofing.csv")
    combined_pcap = os.path.join("data", "combined_v5_spoofing.pcap")
    
    combine_csv_files(archive_dir, combined_csv)
    combine_pcap_files(archive_dir, combined_pcap)
    
    print("\nDone. Original files in v5_spoofing_archive were not modified.")
