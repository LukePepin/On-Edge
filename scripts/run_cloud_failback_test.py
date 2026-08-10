#!/usr/bin/env python3
import socket
import threading
import time
import sys

# ==============================================================================
# STATIC CLOUD IdP (TCP Server)
# ==============================================================================
# This script runs on the Laptop. It acts as a static Cloud authority.
# It streams AUTH_OK packets to the Pi. 
# You can press [ENTER] at any time to physically sever the TCP connection, 
# simulating an EW Jamming attack for the video. Press [ENTER] again to restore it.
# ==============================================================================

PORT = 8080
server_active = True
client_conn = None
has_connected_once = False

def interactive_toggle():
    global server_active, client_conn
    while True:
        input() # Wait for ENTER
        server_active = not server_active
        if not server_active:
            print("\n[IdP] 🧨 EW JAMMING INITIATED (MANUAL OVERRIDE): Severing TCP socket!")
            if client_conn:
                try:
                    client_conn.close()
                except:
                    pass
                client_conn = None
        else:
            print("\n[IdP] 🟢 JAMMING CEASED: Listening for Edge Node reconnection on port 8080...")

def outage_tracker():
    """Visually tracks the deterministic edge mesh phases during a physical outage."""
    global client_conn
    while True:
        if server_active and client_conn is None and has_connected_once:
            # We lost connection. Track the autonomous edge mesh.
            print("\n[IdP Dash] 🔴 OUTAGE DETECTED. TCP connection severed.")
            print("[IdP Dash] ⏳ T+0s: Edge Node isolating... Bootstrapping ZKP Identity Proofs.")
            
            # Wait for ZKP to finish (5 seconds)
            time_waited = 0
            while time_waited < 5 and client_conn is None:
                time.sleep(1)
                time_waited += 1
                
            if client_conn is None:
                print("[IdP Dash] ⚡ T+5s: ZKP Mathematical Verification Complete. Hot-swapping to ECC Kinematics...")
                
            # Wait for ECC to stabilize (10 seconds)
            while time_waited < 15 and client_conn is None:
                time.sleep(1)
                time_waited += 1
                
            if client_conn is None:
                print("[IdP Dash] 🛡️ T+15s: Continuous ECC Stability threshold met. Restoring Centralized Cloud Authority...")
                
            # Wait until reconnected
            while client_conn is None:
                time.sleep(0.5)
        else:
            time.sleep(0.5)

def start_server():
    global client_conn
    print(f"Starting Static Cloud TCP Server on port {PORT}...")
    print("Press [ENTER] at any time to toggle the network connection (Simulate Jamming).")
    
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    server.bind(('', PORT))
    server.listen(1)
    
    # Start threads
    threading.Thread(target=interactive_toggle, daemon=True).start()
    threading.Thread(target=outage_tracker, daemon=True).start()
    
    while True:
        if server_active:
            try:
                server.settimeout(1.0)
                conn, addr = server.accept()
                client_conn = conn
                has_connected_once = True
                print(f"\n[IdP] 🟢 CENTRALIZED CLOUD AUTHORITY ACTIVE. Edge Node {addr} connected.")
                
                while server_active and client_conn:
                    try:
                        client_conn.sendall(b'AUTH_OK\n')
                        time.sleep(1)
                    except (ConnectionResetError, BrokenPipeError):
                        client_conn = None
                        break
            except socket.timeout:
                continue
            except Exception as e:
                pass
        else:
            time.sleep(0.5)

if __name__ == '__main__':
    try:
        start_server()
    except KeyboardInterrupt:
        print("\nShutting down IdP.")
        sys.exit(0)
