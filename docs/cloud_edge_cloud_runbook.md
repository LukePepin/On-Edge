# Cloud-Edge-Cloud Rejoin Test Runbook

This guide contains the exact terminal commands and UI steps required to execute the Cloud-Edge-Cloud failback proof.

> [!CAUTION]
> **DO NOT** execute these commands until the current 120-run randomized campaign has completely finished. Running them concurrently will corrupt the ANOVA dataset and crash the ROS 2 kinematic stream.

## Step 1: Flash the Edge Worker Firmware

The failback test requires the Arduino Nano 33 BLE to act as the "Edge Authority" while the cloud is down.

1. Open the `firmware/cloud_edge_cloud_failback/cloud_edge_cloud_failback.ino` folder in VS Code.
2. In the bottom toolbar, click the **PlatformIO Home** button (the alien icon).
3. Connect your Arduino Nano 33 BLE via USB.
4. Click the **PlatformIO: Upload** button (the right arrow `→` icon in the bottom blue toolbar) to compile and flash the firmware.
5. Click the **PlatformIO: Serial Monitor** button (the plug icon) to view the telemetry. You will see:
   `[SentryC2 Edge Auth] Cloud IdP Unreachable (Simulated Jamming).`

## Step 2: Configure the Ping Target

By default, the Cloud script is hardcoded to ping `192.168.0.150` to check if the edge mesh has stabilized.
1. Determine the IP address of your secondary Raspberry Pi or Arduino on the local network.
2. Open `scripts/run_cloud_failback_test.py`.
3. Change Line 14: `SECONDARY_PI_IP = "192.168.0.150"` to match your actual edge node's IP.

## Step 3: Execute the Failback Simulation

Once the IP is configured and the Arduino is flashed, execute the mock Cloud IdP.

1. Open a new terminal on your main Raspberry Pi (Supervisor).
2. Run the following command:
```bash
python3 scripts/run_cloud_failback_test.py
```

## Step 4: Capture the Proof

1. The script will immediately begin issuing `1.0s` OAuth Leases and pinging the secondary node.
2. If the secondary node is online and responding to pings, the script will simulate the EW jamming subsiding.
3. Wait exactly **60 seconds** (the `FAILBACK_THRESHOLD_SECONDS` is set to 60s for demo purposes to save you time, though the thesis dictates 5 minutes).
4. The terminal will explode with the following output:
```
=======================================================
[Failback Monitor] 60 SECONDS OF CONTINUOUS STABILITY ACHIEVED.
[Failback Monitor] INITIATING CLOUD-EDGE-CLOUD REJOIN...
[Failback Monitor] Re-asserting centralized Cloud Auth Authority.
=======================================================
```
5. **Take a screenshot of this terminal output!** This is the exact qualitative proof you need for Chapter 5 to demonstrate that the decentralized edge meshes can gracefully surrender authority back to the Cloud IdP once a network partition is resolved.
