# Physical Workspace & Network Topology Guide

This document outlines the ideal physical layout and network configuration for the "On-Edge" thesis project. To ensure deterministic data collection and avoid interference, the workspace is divided into specific functional zones.

## 1. The Physical Layout

### 1.1 The Operator Station
*   **Hardware:** Dedicated Laptop/PC.
*   **Purpose:** This is your control center. You will use this station to write code, deploy to the edge nodes, monitor telemetry, and inject network degradation via Scapy.
*   **Placement:** Should be positioned comfortably away from the physical robotic movements but with a clear line of sight to the UR5 and the Arduino nodes.

### 1.2 The Edge Compute & Robotics Zone
*   **Hardware:** 1x Universal Robots UR5 Manipulator, 9x Arduino Nano 33 BLEs, 1x Wrist-mounted 9-axis IMU. *(Note: Switched to UR5 to utilize native ROS 2 drivers, avoiding a custom ROS bridge).*
*   **Purpose:** The physical execution layer. The Arduinos act as distributed edge nodes, while the UR5 performs the physical tasks.
*   **Placement:** 
    *   The UR5 should be securely bolted to a stable workbench.
    *   The Arduinos can be mounted on a non-conductive breadboard or custom 3D-printed rack nearby. Ensure they are close enough for the Wi-Fi/BLE signals to reach the Raspberry Pi supervisor without passing through heavy metal obstructions.
    *   The IMU must be securely strapped to the wrist of the UR5.

### 1.3 The Supervisor & Networking Hub
*   **Hardware:** 1x Raspberry Pi 4 (Supervisor), 1x Gigabit Network Switch, Localized Wi-Fi Router (if not using the Pi's built-in ad-hoc networking).
*   **Purpose:** The brains of the operation and the routing backbone. 
*   **Placement:** Keep the Raspberry Pi and the Network Switch close to each other to minimize Ethernet cable runs. 

---

## 2. Network Topology & The Gigabit Switch

The most critical part of this workspace is isolating the **experimental traffic** from the **management traffic**. 

> [!IMPORTANT]
> Never mix your telemetry/SSH data with your ROS 2 node data. Doing so will create artificial congestion and corrupt your packet-loss experiments.

### 2.1 The Management Network (Wired Ethernet)
This is your "Out-of-Band" backend. It uses the Gigabit Network Switch to ensure rock-solid, high-bandwidth data collection.

**Connections to the Gigabit Switch:**
1.  **Port 1:** Dedicated Laptop/PC (Cat6 cable).
2.  **Port 2:** Raspberry Pi 4 Supervisor (Cat6 cable).
3.  **Port 3:** UR5 (Cat6 cable) - *Highly recommended for reliable command streaming directly to the UR5 control box via its native ROS 2 driver.*
4.  **Port 4 (Optional Uplink):** Connection to your home/university internet router. 
    *   *Note: Only connect this when you need to download packages via `apt` or `pip`. Disconnect the uplink during actual experiments to prevent background OS updates or broadcast storms from skewing network traffic.*

**Functionality:** 
You will SSH from your Laptop into the Raspberry Pi over this wired connection. When running `tshark` or `tcpdump` to collect your logs, the heavy log files will be transferred over this wire, leaving the Wi-Fi completely free for the Arduinos.

### 2.2 The Experimental Network (Wireless 802.11 / UDP)
This is the localized ad-hoc network where the actual thesis experiment takes place.

**Connections:**
*   Raspberry Pi 4 acts as the central hub (or ad-hoc participant) using its `wlan0` interface.
*   9x Arduino Nano 33 BLEs communicate over the air via Micro XRCE-DDS to the Raspberry Pi.

**Functionality:**
This network handles pure ROS 2 Publisher/Subscriber traffic. In Phase 1.5, when you run your Scapy/Linux Traffic Control (`tc`) scripts from the wired laptop, they will target the Raspberry Pi's routing tables to artificially drop packets *only* on this wireless interface.

---

## 3. Power Management Checklist

> [!WARNING]
> Insufficient power will cause CPU throttling on the Pi or unexpected reboots on the Arduinos, ruining deterministic timing.

*   **Raspberry Pi:** Ensure you are using an official 15W (5V/3A) USB-C power supply. 
*   **Network Switch:** Standard wall power.
*   **UR5:** Dedicated control box and power supply. Ensure the emergency stop button on the teach pendant is positioned within arm's reach of the Operator Station.
*   **Arduinos:** It is highly recommended to use a **Powered USB Hub** connected directly to the wall (not to the Pi or Laptop) to power the 9x Arduinos. Drawing power for 9 Arduinos directly from the Pi's USB ports will likely cause power brownouts and USB bus resets.
