#!/usr/bin/env python3
import serial
import time

def main():
    try:
        # Open serial port at correct baud rate
        ser = serial.Serial('/dev/ttyACM0', 115200, timeout=1)
        time.sleep(1) # Allow connection to settle
        
        print("Sending cryptographic attack payloads (10-second extended burst)...")
        for i in range(100):
            if i % 10 == 0:
                print(f"[{i+1}/100] Injecting continuous payload: ATTACK")
            ser.write(b"ATTACK\n")
            ser.flush()
            time.sleep(0.1) # Wait for execution spike
            
        print("10-second Attack sequence complete! Hardware should auto-recover now.")
        ser.close()
    except Exception as e:
        print(f"Failed to connect to Arduino: {e}")

if __name__ == '__main__':
    main()
