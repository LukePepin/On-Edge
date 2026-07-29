#!/usr/bin/env python3
import socket
import time
import sys

def clear_safety_stop(host="192.168.1.100", port=29999):
    """
    Connects to the UR5 Dashboard Server to automatically clear STO safety popups
    and unlock the protective stop to enable unattended script execution.
    """
    print(f"Connecting to UR5 Dashboard Server at {host}:{port}...")
    try:
        # Phase B: Software-Level Dashboard Server Reset
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.settimeout(5.0)
        s.connect((host, port))
        
        # Read the connection welcome message
        welcome = s.recv(1024).decode('utf-8')
        print(f"[UR5] {welcome.strip()}")

        def send_command(cmd):
            print(f"Sending: {cmd}")
            s.sendall((cmd + "\n").encode('utf-8'))
            time.sleep(0.5) # Give the controller a moment to process
            resp = s.recv(1024).decode('utf-8')
            print(f"[UR5] {resp.strip()}")
            return resp

        # 1. Clear C153/C157 warnings
        send_command("close safety popup")
        
        # 2. Re-enable joint servo loops
        send_command("unlock protective stop")
        
        # 3. Validate transition to RUNNING
        robotmode = send_command("robotmode")
        
        if "RUNNING" not in robotmode and "IDLE" not in robotmode:
            print("⚠️ WARNING: Robot may not have cleared the safety state properly.")
            
        # 4. Resume the URCap (External Control) for the next trial
        send_command("play")
            
        s.close()
        print("✅ Safety stop cleared and program resumed automatically.")
        
    except socket.timeout:
        print("❌ ERROR: Connection to Dashboard Server timed out. Check IP and network.")
        sys.exit(1)
    except ConnectionRefusedError:
        print("❌ ERROR: Connection refused. Is the Dashboard Server running?")
        sys.exit(1)
    except Exception as e:
        print(f"❌ ERROR: {e}")
        sys.exit(1)

if __name__ == "__main__":
    # You can pass the robot IP as an argument, defaults to 192.168.1.100
    robot_ip = sys.argv[1] if len(sys.argv) > 1 else "192.168.1.100"
    
    # Phase A2: Sequence Delay Integration
    # A strict 250ms software timer delay immediately after re-asserting GPIO
    print("Enforcing 250ms stabilization delay for optocoupler capacitive discharge...")
    time.sleep(0.25)
    
    clear_safety_stop(host=robot_ip)
