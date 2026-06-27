import serial
import json
import csv
import time
import argparse
import threading
import random

def network_jitter_injector(ser, stop_event):
    """
    Background thread that randomly blasts 256-byte dummy payloads down the Serial port.
    This forces the Arduino's hardware UART to throw interrupts to the Cortex-M4 CPU,
    stealing clock cycles from the ZKP math and simulating true RTOS network jitter.
    """
    dummy_payload = b"ROS2_DDS_NETWORK_INTERRUPT_SIMULATION_" * 6 + b"\n"
    while not stop_event.is_set():
        # Sleep for a random interval between 0.1 and 1.2 seconds
        time.sleep(random.uniform(0.1, 1.2))
        try:
            ser.write(dummy_payload)
            ser.flush()
        except serial.SerialException:
            break

def collect_data(port, baudrate, duration_seconds):
    print(f"Connecting to {port} at {baudrate} baud...")
    
    try:
        ser = serial.Serial(port, baudrate, timeout=6)
    except serial.SerialException as e:
        print(f"Error: {e}")
        print("\n*** IMPORTANT: Make sure the VS Code Serial Monitor is CLOSED before running this script! ***")
        return

    print(f"Connected! Recording timeseries for {duration_seconds} seconds...")
    print("-> Phase 2.4B: Jitter Injection Thread STARTED. Firing random dummy DDS packets.")
    
    stop_event = threading.Event()
    jitter_thread = threading.Thread(target=network_jitter_injector, args=(ser, stop_event))
    jitter_thread.daemon = True
    jitter_thread.start()
    
    dataset = []
    
    # Track the current state to build the timeseries row
    current_bytes = None
    current_latency = None
    current_score = None
    is_evicted = False
    
    start_time = time.time()
    
    while (time.time() - start_time) < duration_seconds:
        try:
            line = ser.readline().decode('utf-8').strip()
            if not line:
                continue
                
            data = json.loads(line)
            topic = data.get('topic')
            
            if topic == 'crypto_profile' and data.get('algorithm') == 'zkp_sweep':
                current_bytes = data.get('payload_bytes')
                current_latency = data.get('latency_ms')
                
            elif topic == 'trust_score':
                current_score = data.get('score')
                is_evicted = False
                
            elif topic == 'eviction':
                current_score = data.get('score')
                is_evicted = True
                print(f"   -> [CRITICAL] Node evicted at {current_bytes}-bytes! Score: {current_score}")
                
            elif topic == 'eviction_hold':
                current_score = data.get('score')
                is_evicted = True
                
            elif topic == 'trust_score_reset':
                current_score = 100
                is_evicted = False
                print(f"-> Moving to next payload size. Trust Score Reset to 100.")

            # We log a row every time we get a trust score update (which happens 1x per second)
            if topic in ['trust_score', 'eviction', 'eviction_hold'] and current_bytes is not None:
                dataset.append({
                    'timestamp': round(time.time() - start_time, 2),
                    'payload_bytes': current_bytes,
                    'latency_ms': current_latency,
                    'trust_score': current_score,
                    'evicted': is_evicted
                })
                print(f"Logged: {current_bytes}B | Latency: {current_latency}ms | Score: {current_score} | Evicted: {is_evicted}")

        except json.JSONDecodeError:
            pass # Ignore malformed serial lines
        except Exception as e:
            print(f"Read error: {e}")
            break

    stop_event.set()
    jitter_thread.join(timeout=1.0)
    ser.close()
    
    # Save Unified Timeseries to CSV
    csv_filename = "timeseries_evaluation.csv"
    with open(csv_filename, mode='w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['timestamp', 'payload_bytes', 'latency_ms', 'trust_score', 'evicted'])
        writer.writeheader()
        writer.writerows(dataset)
        
    print(f"\nSuccess! Saved {len(dataset)} data points to {csv_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Collect ZKP Timeseries Data")
    parser.add_argument("--port", type=str, default="COM26", help="Serial port (e.g. COM26)")
    parser.add_argument("--baud", type=int, default=115200, help="Baud rate")
    parser.add_argument("--duration", type=int, default=300, help="Test duration in seconds (Default 300s / 5 mins)")
    args = parser.parse_args()
    
    collect_data(args.port, args.baud, args.duration)
