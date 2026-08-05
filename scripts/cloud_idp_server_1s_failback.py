#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import base64
import threading
import subprocess
import sys

# Cloud-Edge-Cloud Identity Provider (IdP) Emulation
# 1. Issues 1.0s TTL leases to the primary supervisor node.
# 2. Asynchronously monitors a secondary Edge Node (e.g., Pi #2).
# 3. If the secondary node maintains a connection for 5 continuous minutes,
#    it restores cloud authority ("Failback").

PORT = 8080
SECONDARY_PI_IP = "192.168.0.150" # Change this to the actual 2nd Pi's IP

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

def monitor_secondary_node():
    """
    Background thread that monitors the secondary Pi.
    Requires 5 minutes (300 seconds) of uninterrupted uptime to trigger a failback.
    """
    continuous_uptime = 0
    failback_threshold = 300 # 5 minutes
    
    print(f"[Failback Monitor] Started monitoring secondary node at {SECONDARY_PI_IP}...")
    
    while True:
        try:
            # Ping syntax for Windows (1 ping, 1000ms timeout)
            # If running on Linux, change '-n' to '-c' and '-w' to '-W 1'
            result = subprocess.run(
                ['ping', '-n', '1', '-w', '1000', SECONDARY_PI_IP],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            if result.returncode == 0:
                continuous_uptime += 1
                if continuous_uptime % 60 == 0:
                    print(f"[Failback Monitor] Secondary node {SECONDARY_PI_IP} stable for {continuous_uptime}s...")
                    
                if continuous_uptime >= failback_threshold:
                    print(f"\n=======================================================")
                    print(f"[Failback Monitor] 5 MINUTES OF CONTINUOUS STABILITY ACHIEVED.")
                    print(f"[Failback Monitor] INITIATING CLOUD-EDGE-CLOUD REJOIN...")
                    print(f"[Failback Monitor] Re-asserting centralized Cloud Auth Authority.")
                    print(f"=======================================================\n")
                    # Reset counter to simulate a completed failback
                    continuous_uptime = 0
            else:
                if continuous_uptime > 0:
                    print(f"[Failback Monitor] Ping failed! Resetting stability counter from {continuous_uptime}s to 0s.")
                continuous_uptime = 0
                
        except Exception as e:
            print(f"[Failback Monitor] Ping error: {e}")
            continuous_uptime = 0
            
        time.sleep(1) # Ping every 1 second

def run(server_class=HTTPServer, handler_class=MockCloudIdP, port=PORT):
    # Start the failback monitor thread
    monitor_thread = threading.Thread(target=monitor_secondary_node, daemon=True)
    monitor_thread.start()
    
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting Cloud-Edge-Cloud Identity Provider on port {port}...")
    print("Serving STRICT 1.0-second OAuth Leases at http://localhost:8080/api/auth/lease")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Stopping Cloud IdP.")

if __name__ == '__main__':
    run()
