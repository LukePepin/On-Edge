#!/usr/bin/env python3
import serial
import time

def main():
    try:
        # Open serial port at correct baud rate
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
        time.sleep(1) # Allow connection to settle
        
        print("Sending cryptographic attack payloads...")
        for i in range(5):
            print(f"[{i+1}/5] Injecting payload: ATTACK")
            ser.write(b"ATTACK\n")
            ser.flush()
            time.sleep(0.1) # Wait for execution spike
            
        print("Attack sequence complete!")
        ser.close()
    except Exception as e:
        print(f"Failed to connect to Arduino: {e}")

if __name__ == '__main__':
    main()
