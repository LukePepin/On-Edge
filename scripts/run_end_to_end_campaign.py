import serial
import json
import csv
import time
import sys
import threading
import requests
import itertools
import os

PORT = '/dev/ttyACM0'  # Arduino port on the Pi
BAUD = 115200

# End-to-End Composition Block Parameters
PROBE_INTERVALS = [100, 500]
ALGOS = ["ECC", "ZKP"]
ALPHA = 0.5
ITERS = list(range(1, 6))

# Global Dummy Cloud State
cloud_is_up = True

from http.server import BaseHTTPRequestHandler, HTTPServer

class CloudHealthHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass
        
    def do_GET(self):
        global cloud_is_up
        try:
            if cloud_is_up:
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"status": "ok"}')
            else:
                time.sleep(2.0) # Simulate a hard drop
        except Exception:
            pass

def run_dummy_cloud():
    server = HTTPServer(('127.0.0.1', 8081), CloudHealthHandler)
    server.serve_forever()

def probe_cloud(timeout_ms):
    try:
        res = requests.get('http://127.0.0.1:8081/health', timeout=(timeout_ms/1000.0))
        if res.status_code == 200:
            return True
    except requests.exceptions.RequestException:
        pass
    return False

def process_serial_buffer(ser, serial_buf):
    if ser.in_waiting:
        serial_buf += ser.read(ser.in_waiting).decode('utf-8', errors='ignore')
    
    lines = []
    while '\n' in serial_buf:
        line, serial_buf = serial_buf.split('\n', 1)
        line = line.strip()
        if line:
            lines.append(line)
    return lines, serial_buf

def main():
    global cloud_is_up
    print("--- End-to-End Composition Validation Campaign ---")
    
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
    except Exception as e:
        print(f"Failed to connect to Arduino: {e}")
        sys.exit(1)
        
    time.sleep(2)
    ser.reset_input_buffer()
    
    os.makedirs('data/v7_logs', exist_ok=True)
    outfile = 'data/v7_logs/e2e_composition_results.csv'
    
    # Start Dummy Cloud Server
    t = threading.Thread(target=run_dummy_cloud, daemon=True)
    t.start()
    
    total_runs = len(PROBE_INTERVALS) * len(ALGOS) * len(ITERS)
    run_idx = 1
    
    with open(outfile, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['probe_ms', 'algo', 'alpha', 'iter', 
                         't_jam', 't_detection', 't_first_decay', 't_eviction', 
                         'detection_window_ms', 'eviction_latency_ms', 'total_exposure_ms',
                         'predicted_total_ms', 'residual_ms'])
                         
        for p, algo, iter_num in itertools.product(PROBE_INTERVALS, ALGOS, ITERS):
            print(f"[{run_idx}/{total_runs}] Probe: {p}ms, Algo: {algo}, Iter: {iter_num}")
            
            # Configure Arduino
            config_payload = json.dumps({"algo": algo, "alpha": ALPHA})
            ser.write(f"{config_payload}\n".encode())
            time.sleep(0.5)
            
            serial_buf = ""
            cloud_is_up = True
            
            t_start = time.time()
            t_jam = 0
            t_detection = 0
            t_first_decay = 0
            t_eviction = 0
            
            next_probe = time.time()
            sentry_thinks_cloud_is_down = False
            evicted = False
            
            # 1. Normal operation (3 seconds)
            while time.time() - t_start < 3.0:
                if time.time() >= next_probe:
                    probe_cloud(p)
                    next_probe = time.time() + (p / 1000.0)
                
                lines, serial_buf = process_serial_buffer(ser, serial_buf)
                time.sleep(0.01)
                
            # 2. Inject Network Jam
            cloud_is_up = False
            t_jam = time.time()
            next_probe = time.time() # Immediately trigger next probe attempt
            
            while not evicted and (time.time() - t_jam < 10.0):
                # Sentry Probe Loop
                if time.time() >= next_probe and not sentry_thinks_cloud_is_down:
                    is_up = probe_cloud(p)
                    if not is_up:
                        t_detection = time.time()
                        sentry_thinks_cloud_is_down = True
                        ser.write(b"ATTACK\n") # Sentry signals crypto node
                    else:
                        next_probe = time.time() + (p / 1000.0)
                
                # Sentry Serial Read Loop
                lines, serial_buf = process_serial_buffer(ser, serial_buf)
                for line in lines:
                    if "trust_score" in line:
                        try:
                            msg = json.loads(line)
                            trust = float(msg["trust_score"])
                            
                            if t_detection > 0 and trust < 100.0 and t_first_decay == 0:
                                t_first_decay = time.time()
                                
                            if trust <= 30.0 and t_eviction == 0:
                                t_eviction = time.time()
                                evicted = True
                        except:
                            pass
                time.sleep(0.01)
                
            # 3. Recover
            cloud_is_up = True
            ser.write(b"RECOVER\n")
            time.sleep(1.0) # Let it settle
            
            # 4. Metrics
            if not evicted:
                print("  -> ERROR: Did not evict within 10 seconds. (Instrumentation Failure)")
                with open('data/v7_logs/e2e_failures.log', 'a') as fail_log:
                    fail_log.write(f"Failed trial: Probe={p}, Algo={algo}, Alpha={ALPHA}, Iter={iter_num}\n")
                continue
                
            detection_window = (t_detection - t_jam) * 1000
            eviction_latency = (t_eviction - t_detection) * 1000
            total_exposure = (t_eviction - t_jam) * 1000
            
            cycle_time = 125.0 if algo == "ECC" else 247.0
            n_cycles = 2 # for alpha=0.5
            offset = 123.5 # midpoint of 0-247
            predicted_total = (2 * p) + (n_cycles * cycle_time) + offset
            
            residual = total_exposure - predicted_total
            
            print(f"  -> Total Exposure: {total_exposure:.1f}ms (Predicted: {predicted_total:.1f}ms) | Residual: {residual:+.1f}ms")
            
            writer.writerow([p, algo, ALPHA, iter_num, 
                             t_jam, t_detection, t_first_decay, t_eviction,
                             round(detection_window,2), round(eviction_latency,2), round(total_exposure,2),
                             round(predicted_total,2), round(residual,2)])
                             
            run_idx += 1
            
    print("\nEnd-to-End Campaign Complete. Results in data/v7_logs/e2e_composition_results.csv")

if __name__ == "__main__":
    main()
