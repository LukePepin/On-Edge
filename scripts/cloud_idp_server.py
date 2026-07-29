#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import time
import base64
import sys

# Cloud Identity Provider (IdP) Emulation for the Swap PoC
# Generates Mock JSON Web Tokens (JWT) with a 5-second lease

PORT = 8080

class MockCloudIdP(BaseHTTPRequestHandler):
    def _set_headers(self):
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()

    def do_GET(self):
        if self.path == '/api/auth/lease':
            self._set_headers()
            
            # Create a mock JWT with an issued_at (iat) and expiration (exp)
            current_time = int(time.time())
            exp_time = current_time + 5 # 5 second TTL
            
            payload = {
                "sub": "edge_sentry_node",
                "iat": current_time,
                "exp": exp_time,
                "scope": "kinematic_control",
                "auth_source": "CLOUD_OAUTH_BASELINE"
            }
            
            # Base64 encode for realism
            header = base64.b64encode(b'{"alg":"HS256","typ":"JWT"}').decode('utf-8')
            b64_payload = base64.b64encode(json.dumps(payload).encode('utf-8')).decode('utf-8')
            signature = "mock_signature_xxyyzz"
            
            jwt_token = f"{header}.{b64_payload}.{signature}"
            
            response = {
                "access_token": jwt_token,
                "token_type": "Bearer",
                "expires_in": 5
            }
            
            self.wfile.write(json.dumps(response).encode('utf-8'))
            print(f"[IdP] Issued 5s OAuth Lease. Client: {self.client_address}")
        else:
            self.send_response(404)
            self.end_headers()

def run(server_class=HTTPServer, handler_class=MockCloudIdP, port=PORT):
    server_address = ('', port)
    httpd = server_class(server_address, handler_class)
    print(f"Starting Mock Cloud Identity Provider on port {port}...")
    print("Serving 5-second OAuth Leases at http://localhost:8080/api/auth/lease")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print("Stopping Cloud IdP.")

if __name__ == '__main__':
    run()
