# Hardware Requirements & Resource Laundry List

Based on the thesis proposal, here is the complete bill of materials and resources required to execute the study.

## 1. Computing & Edge Hardware
- [ ] **1x Raspberry Pi 4 (8GB RAM)**: Cortex-A architecture, acts as supervisor/arbiter node.
- [ ] **9x Arduino Nano 33 BLE**: ARM Cortex-M4 architecture, acts as resource-constrained edge compute nodes.
- [ ] **1x MicroSD Card (64GB+)**: For the Raspberry Pi 4 operating system (Ubuntu 22.04 LTS).
- [ ] **Power Supplies**: 
  - 1x USB-C power supply for Raspberry Pi 4.
  - USB cables (Micro-USB/USB-C depending on exact headers) to power/program the Arduino nodes.
  - Powered USB hubs if deploying all Arduinos from a central logging station.

## 2. Robotic Hardware
- [ ] **1x Niryo Ned2**: 6-axis collaborative industrial manipulator.
- [ ] **1x Wrist-mounted 9-axis IMU**: (e.g., MPU-9250, BNO085, or similar breakout board) to record acceleration and deceleration curves. Needs wiring/mount to attach to the Niryo Ned2 wrist.

## 3. Network Infrastructure
- [ ] **Wireless Routing Hardware**: Localized IEEE 802.11 ad-hoc capable wireless routers or dedicated mesh nodes.
- [ ] **Network Switch (Gigabit)**: Dedicated wired backend for out-of-band telemetry collection and synthetic packet-loss injection.
- [ ] **Ethernet Cables (Cat6)**: Multiple cables to connect the Raspberry Pi, Niryo Ned2 (if wired), and the out-of-band telemetry laptop/switch.
- [ ] **Dedicated Laptop/PC**: For running NS-3 simulations, out-of-band network injection (Scapy scripts), and large-scale data analysis.

## 4. Software Stack & Licenses
- [ ] Ubuntu 22.04 LTS (Host OS for Supervisor and Dev PC)
- [ ] ROS2 Humble Hawksbill
- [ ] Eclipse CycloneDDS
- [ ] NS-3 discrete-event network simulator
- [ ] Arduino IDE / PlatformIO for flashing Cortex-M4 nodes
