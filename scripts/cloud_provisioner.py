#!/usr/bin/env python3
import serial
import json
import time
import threading
import sys

# Configure this based on what the Arduino enumerates as on your OS
# Windows is usually COM3, COM4, etc. Pi is /dev/ttyACM0
SERIAL_PORT = 'COM3'  
BAUD_RATE = 115200

# Global network state
throttle_attack_active = False

def input_listener():
    """Listens for terminal input to trigger network attacks."""
    global throttle_attack_active
    while True:
        try:
            cmd = input().strip().lower()
            if cmd == "throttle":
                throttle_attack_active = True
                print("\n[!] ATTACK INJECTED: Network throttled to 600ms latency!")
            elif cmd == "heal":
                throttle_attack_active = False
                print("\n[+] NETWORK HEALED: Resuming normal 300ms latency.")
            elif cmd == "exit" or cmd == "quit":
                print("Exiting...")
                sys.exit(0)
            else:
                print("Unknown command. Type 'throttle' to attack, 'heal' to restore.")
        except (EOFError, KeyboardInterrupt):
            sys.exit(0)

def main():
    try:
        ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=1)
        print(f"Connected to Cryptographic Edge Node on {SERIAL_PORT}")
    except serial.SerialException as e:
        print(f"Failed to connect to Arduino on {SERIAL_PORT}: {e}")
        print("Please update the SERIAL_PORT variable in this script.")
        return

    # Start the CLI listener thread
    print("\n========================================================")
    print("Cloud Provisioner Active. Streaming auth tokens...")
    print("Commands:")
    print("  'throttle' -> Simulates network DoS attack (600ms lag)")
    print("  'heal'     -> Restores normal network flow (300ms)")
    print("========================================================\n")
    
    cli_thread = threading.Thread(target=input_listener)
    cli_thread.daemon = True
    cli_thread.start()

    cycle = 0
    try:
        while True:
            # Send an authentication token
            payload = json.dumps({"auth": "valid", "cycle": cycle}) + "\n"
            ser.write(payload.encode('utf-8'))
            
            # Print any response from the Arduino (the Trust Score JSON)
            while ser.in_waiting > 0:
                response = ser.readline().decode('utf-8', errors='ignore').strip()
                if response:
                    print(f"Node Status: {response}")
            
            cycle += 1
            
            # Apply network delay based on attack state
            if throttle_attack_active:
                time.sleep(0.6)  # 600ms - triggers eviction
            else:
                time.sleep(0.3)  # 300ms - keeps Trust Score high
                
    except KeyboardInterrupt:
        print("Shutting down Cloud Provisioner.")
    finally:
        ser.close()

if __name__ == '__main__':
    main()
