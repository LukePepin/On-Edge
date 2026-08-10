#!/usr/bin/env python3
import argparse
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import base64
import threading
import subprocess
import sys

# Cloud-Edge-Cloud Identity Provider (IdP) Emulation & Failback Monitor
# 1. Issues strict 1.0s TTL leases to the primary supervisor node.
# 2. Asynchronously monitors the local edge mesh via ping.
# 3. If the connection stabilizes for the threshold duration, it restores cloud authority.

SECONDARY_PI_IP = "on-edge-pi.local" 
FAILBACK_THRESHOLD_SECONDS = 60 # Set to 60s for demo purposes (Thesis specifies 5 mins)

class MockCloudIdP(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/auth/lease':
            self._set_headers()
            
            # 1.0 second TTL safety ceiling
            current_time = int(time.time())
            exp_time = current_time + 1 
            
            payload = {
                "sub": "edge_sentry_node",
                "iat": current_time,
                "exp": exp_time,
                "scope": "kinematic_control",
                "auth_source": "CLOUD_EDGE_CLOUD_BASELINE"
            }
            
            header = base64.b64encode(b'{"alg":"HS256","typ":"JWT"}').decode('utf-8')
            b64_payload = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
            signature = "mock_signature_xxyyzz"
            jwt_token = f"{header}.{b64_payload}.{signature}"
            
            response = {
                "access_token": jwt_token,
                "token_type": "Bearer",
                "expires_in": 1
            }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
            print(f"[IdP] Issued 1.0s OAuth Lease. Client: {self.client_address}")
        else:
            self.send_response(404)
            self.end_headers()
            
    # Suppress default HTTP logging to keep terminal clean
    def log_message(self, format, *args):
        pass

def monitor_secondary_node():
    """
    Background thread that monitors the edge connection.
    Requires uninterrupted uptime to trigger a failback.
    """
    continuous_uptime = 0
    
    print(f"[Failback Monitor] Started monitoring edge stability at {SECONDARY_PI_IP}...")
    
    while True:
        try:
            # Ping syntax for Windows (1 ping, 1000ms timeout)
            # If running on Linux/Pi, change '-n' to '-c' and '-w' to '-W 1'
            ping_args = ['ping', '-c', '1', '-W', '1', SECONDARY_PI_IP] if sys.platform != 'win32' else ['ping', '-n', '1', '-w', '1000', SECONDARY_PI_IP]
            
            result = subprocess.run(
                ping_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if result.returncode == 0:
                continuous_uptime += 1
                if continuous_uptime % 10 == 0:
                    print(f"[Failback Monitor] Edge connection stable for {continuous_uptime}s...")
                    
                if continuous_uptime >= FAILBACK_THRESHOLD_SECONDS:
                    print(f"\n=======================================================")
                    print(f"[Failback Monitor] {FAILBACK_THRESHOLD_SECONDS} SECONDS OF CONTINUOUS STABILITY ACHIEVED.")
                    print(f"[Failback Monitor] INITIATING CLOUD-EDGE-CLOUD REJOIN...")
                    print(f"[Failback Monitor] Re-asserting centralized Cloud Auth Authority.")
                    print(f"=======================================================\n")
                    # Reset counter to simulate a completed failback
                    continuous_uptime = 0
            else:
                if continuous_uptime > 0:
                    print(f"[Failback Monitor] Connection lost! Resetting stability counter from {continuous_uptime}s to 0s.")
                # Do not spam if already 0
                continuous_uptime = 0
                
        except Exception as e:
            print(f"[Failback Monitor] Ping error: {e}")
            continuous_uptime = 0
            
        time.sleep(1)

def run(port=8080):
    monitor_thread = threading.Thread(target=monitor_secondary_node, daemon=True)
    monitor_thread.start()
    
    server_address = ('', port)
    httpd = HTTPServer(server_address, MockCloudIdP)
    print(f"Starting Cloud-Edge-Cloud Identity Provider on port {port}...")
    print("Serving STRICT 1.0-second OAuth Leases at http://localhost:8080/api/auth/lease")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("\nStopping Cloud IdP.")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Cloud-Edge-Cloud Failback Emulation")
    parser.add_argument('--port', type=int, default=8080, help='Port to serve IdP on')
    args = parser.parse_args()
    run(port=args.port)
