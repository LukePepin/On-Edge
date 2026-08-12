import serial
import json
import csv
import time
import sys
import threading
import requests
import random
from http.server import BaseHTTPRequestHandler, HTTPServer
import itertools
import os

PORT = 'COM32'  # Arduino port
BAUD = 115200

# Sweep Parameters
PROBE_INTERVALS = [100, 250, 500, 1000]
K_VALUES = [1, 3, 5]
DWELL_VALUES = [0, 1000, 5000]
OUTAGE_PATTERNS = ['clean_drop', 'flapping', 'degraded']

# Global Cloud State for the Dummy Server
current_outage_pattern = 'none'

class CloudIdPHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        pass # Suppress logging
        
    def do_GET(self):
        global current_outage_pattern
        try:
            if current_outage_pattern == 'clean_drop':
                # Simulate hard network drop (timeout)
                time.sleep(2.0)
                return
                
            elif current_outage_pattern == 'flapping':
                # Deterministic harsh flap: 500ms UP, 500ms DOWN
                if (time.time() % 1.0) < 0.5:
                    time.sleep(1.0)
                    return
                else:
                    self.send_response(200)
                    self.send_header('Content-type', 'application/json')
                    self.end_headers()
                    self.wfile.write(b'{"auth": "valid", "status": "ok"}')
                    
            elif current_outage_pattern == 'degraded':
                # High latency but successful (degraded)
                time.sleep(1.5)
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"auth": "valid", "status": "ok"}')
                
            else: # Normal operation
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(b'{"auth": "valid", "status": "ok"}')
        except Exception:
            # Client timed out and closed the connection before we could write.
            # Suppress the socket tracebacks.
            pass

def run_dummy_cloud():
    server = HTTPServer(('127.0.0.1', 8080), CloudIdPHandler)
    server.serve_forever()

def probe_cloud(timeout_ms):
    """
    Active application-level probing. 
    A bare TCP connect is NOT sufficient. We require HTTP 200 and valid JSON payload.
    """
    try:
        res = requests.get('http://127.0.0.1:8080/health', timeout=(timeout_ms/1000.0))
        if res.status_code == 200:
            data = res.json()
            if data.get('status') == 'ok':
                return True
    except requests.exceptions.RequestException:
        pass
    return False

def simulate_rejoin_handshake():
    """
    Simulates Step 3 of the Safety Invariant: Confirming the cloud has accepted authority.
    Returns True if cloud accepts authority.
    """
    return probe_cloud(500) # Quick health check during handoff

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

def run_test_sweep():
    global current_outage_pattern
    
    print(f"Connecting to Sentry Node on {PORT}...")
    try:
        ser = serial.Serial(PORT, BAUD, timeout=0.1)
    except Exception as e:
        print(f"Failed to connect to Arduino: {e}")
        sys.exit(1)
        
    time.sleep(2)
    ser.reset_input_buffer()
    
    os.makedirs('data', exist_ok=True)
    outfile = 'data/cloud_failover_sweep_results_v3.csv'
    
    with open(outfile, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['probe_ms', 'K', 'dwell_ms', 'outage_pattern', 
                         'unmonitored_motion_ms', 'false_rejoin_rate', 
                         'detection_latency_ms', 'recovery_latency_ms', 'oscillation_count'])
                         
        total_runs = len(PROBE_INTERVALS) * len(K_VALUES) * len(DWELL_VALUES) * len(OUTAGE_PATTERNS)
        run = 1
        
        # Start server
        t = threading.Thread(target=run_dummy_cloud, daemon=True)
        t.start()
        
        for probe_ms, k, dwell, pattern in itertools.product(PROBE_INTERVALS, K_VALUES, DWELL_VALUES, OUTAGE_PATTERNS):
            print(f"[{run}/{total_runs}] Testing: Probe={probe_ms}ms, K={k}, Dwell={dwell}ms, Pattern={pattern}")
            
            # Reset Arduino config
            ser.write(f"CONFIG:{k},{dwell}\n".encode())
            time.sleep(0.1)
            ser.reset_input_buffer()
            
            # --- Test Execution Variables ---
            serial_buf = ""
            current_outage_pattern = 'none'
            oscillations = 0
            false_rejoins = 0
            unmonitored_motion_ms = 0
            
            detection_start = 0
            detection_latency = 0
            recovery_start = 0
            recovery_latency = 0
            bootstrap_completion_time = None
            
            state = "CLOUD"
            last_state = "CLOUD"
            
            # 1. Normal operation (3 seconds)
            start_time = time.time()
            next_probe = time.time()
            while time.time() - start_time < 3.0:
                if time.time() >= next_probe:
                    is_up = probe_cloud(probe_ms)
                    ser.write(b"CLOUD_UP\n" if is_up else b"CLOUD_DOWN\n")
                    next_probe = time.time() + (probe_ms / 1000.0)
                    
                lines, serial_buf = process_serial_buffer(ser, serial_buf)
                for line in lines:
                    if "transition" in line:
                        try:
                            state = json.loads(line)['transition']
                        except Exception as e:
                            print(f"[V2 Parse Error] {e} on line: {line}")
                        
                time.sleep(0.01)
                
            # 2. Inject Outage (10 seconds)
            current_outage_pattern = pattern
            detection_start = time.time()
            outage_end = time.time() + 10.0
            next_probe = time.time()
            
            while time.time() < outage_end:
                if time.time() >= next_probe:
                    is_up = probe_cloud(probe_ms)
                    
                    # Active motion without verification
                    if state == "CLOUD" and not is_up:
                        unmonitored_motion_ms += probe_ms
                        
                    ser.write(b"CLOUD_UP\n" if is_up else b"CLOUD_DOWN\n")
                    next_probe = time.time() + (probe_ms / 1000.0)
                
                if bootstrap_completion_time and time.time() >= bootstrap_completion_time:
                    try:
                        ser.write(b"BOOTSTRAP_COMPLETE\n")
                    except Exception: pass
                    bootstrap_completion_time = None
                
                # Check for Serial Responses
                lines, serial_buf = process_serial_buffer(ser, serial_buf)
                for line in lines:
                    if "transition" in line:
                        try:
                            msg = json.loads(line)
                            new_state = msg['transition']
                            if new_state != state:
                                oscillations += 1
                                if state == "CLOUD" and new_state == "ZKP_BOOTSTRAP":
                                    # Use max(1, ...) so it doesn't log 0 if it triggers instantly
                                    detection_latency = max(1, (time.time() - detection_start) * 1000)
                                state = new_state
                                
                            if new_state == "ZKP_BOOTSTRAP":
                                # Simulate crypto node bootstrapping (handled in main loop)
                                bootstrap_completion_time = time.time() + 1.5
                        except Exception as e:
                            print(f"[V2 Parse Error] {e} on line: {line}")
                            
                    elif "INITIATE_REJOIN" in line:
                        # Arduino is gating the rejoin! Execute Safety Invariant Handshake.
                        # We must confirm authority handoff BEFORE allowing motion.
                        handoff_success = simulate_rejoin_handshake()
                        
                        if handoff_success:
                            ser.write(b"REJOIN_CONFIRMED\n")
                            state = "CLOUD"
                            if current_outage_pattern != 'none':
                                false_rejoins += 1
                        else:
                            ser.write(b"REJOIN_FAILED\n")
                
                time.sleep(0.01)
                
            # 3. Restore Network
            current_outage_pattern = 'none'
            recovery_start = time.time()
            recovery_end = time.time() + (dwell / 1000.0) + 10.0
            next_probe = time.time()
            
            while time.time() < recovery_end:
                if time.time() >= next_probe:
                    is_up = probe_cloud(probe_ms)
                    
                    # Active motion without verification
                    if state == "CLOUD" and not is_up:
                        unmonitored_motion_ms += probe_ms
                        
                    ser.write(b"CLOUD_UP\n" if is_up else b"CLOUD_DOWN\n")
                    next_probe = time.time() + (probe_ms / 1000.0)
                
                if bootstrap_completion_time and time.time() >= bootstrap_completion_time:
                    try:
                        ser.write(b"BOOTSTRAP_COMPLETE\n")
                    except Exception: pass
                    bootstrap_completion_time = None
                
                lines, serial_buf = process_serial_buffer(ser, serial_buf)
                for line in lines:
                    if "INITIATE_REJOIN" in line:
                        handoff_success = simulate_rejoin_handshake()
                        if handoff_success:
                            ser.write(b"REJOIN_CONFIRMED\n")
                            # Only set recovery latency on the FIRST successful handoff
                            if recovery_latency == 0:
                                recovery_latency = (time.time() - recovery_start) * 1000
                            state = "CLOUD"
                        else:
                            ser.write(b"REJOIN_FAILED\n")
                            
                if state == "CLOUD":
                    break # Successfully recovered
                    
                time.sleep(0.01)

            # Subtract the expected baseline transitions (CLOUD -> ZKP_BOOTSTRAP -> ECC_STEADY -> CLOUD)
            # to isolate excess churn.
            excess_oscillations = max(0, oscillations - 3)

            writer.writerow([probe_ms, k, dwell, pattern, unmonitored_motion_ms, 
                             false_rejoins, round(detection_latency,2), round(recovery_latency,2), excess_oscillations])
            
            run += 1
            
    print("\nSweep Complete! Results saved to data/cloud_failover_sweep_results.csv")

if __name__ == "__main__":
    run_test_sweep()
