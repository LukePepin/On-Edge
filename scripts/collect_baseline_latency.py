import serial
import json
import csv
import time
import argparse

def collect_data(port, baudrate, samples):
    print(f"Connecting to {port} at {baudrate} baud...")
    
    try:
        ser = serial.Serial(port, baudrate, timeout=3)
    except serial.SerialException as e:
        print(f"Error: {e}")
        print("\n*** IMPORTANT: Make sure the VS Code Serial Monitor is CLOSED before running this script! ***")
        return

    print(f"Connected! Waiting for {samples} samples...")
    
    dataset = []
    
    while len(dataset) < samples:
        try:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue
                
            data = json.loads(line)
            
            # Filter only crypto_profile messages
            if data.get('topic') == 'crypto_profile':
                dataset.append({
                    'sample_id': len(dataset) + 1,
                    'algorithm': data.get('algorithm'),
                    'cycles': data.get('cycles'),
                    'latency_ms': data.get('latency_ms')
                })
                print(f"[{len(dataset)}/{samples}] Captured: {data['latency_ms']} ms")
                
        except json.JSONDecodeError:
            pass # Ignore malformed serial lines
        except Exception as e:
            print(f"Read error: {e}")
            break

    ser.close()
    
    # Save to CSV
    csv_file = "latency_baseline.csv"
    with open(csv_file, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['sample_id', 'algorithm', 'cycles', 'latency_ms'])
        writer.writeheader()
        writer.writerows(dataset)
        
    print(f"\nSuccess! Saved {samples} samples to {csv_file}")
    
    # Calculate basic statistics
    latencies = [row['latency_ms'] for row in dataset]
    avg_latency = sum(latencies) / len(latencies)
    print(f"Average Latency: {avg_latency:.2f} ms")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect ECDSA Latency Data")
    parser.add_argument("--port", type=str, default="COM26", help="Serial port (e.g. COM26)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--samples", type=int, default=30, help="Number of samples to collect")
    args = parser.parse_args()
    
    collect_data(args.port, args.baud, args.samples)
