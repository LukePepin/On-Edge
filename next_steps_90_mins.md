# Deep Work Session: Next 90 Minutes

**Primary Goal**: Kickstart "Phase 1: Baseline Hardware Instrumentation" by laying the foundational software and firmware structure.

## Time Block Breakdown

### Block 1: Edge Firmware Boilerplate (30 mins)
* **Goal**: Establish the base Arduino environment for the Edge Compute Nodes.
* **Actions**:
  * On your **Windows PC**, navigate to `src/edge_firmware/`.
  * Set up a basic PlatformIO or Arduino IDE project for the **Arduino Nano 33 BLE (Cortex-M4)**.
  * Write a skeleton script that initializes the serial interface and basic hardware registers (specifically preparing the `DWT_CYCCNT` register for cycle counting).
  * Flash the skeleton to at least one Arduino from your Windows PC (you will later connect this to the Pi).

### Block 2: Supervisor Node Setup (40 mins)
* **Goal**: Prepare the Raspberry Pi 4 to act as the Supervisor node.
* **Actions**:
  * Flash Ubuntu 22.04 LTS to the Raspberry Pi's MicroSD card if not already done.
  * Boot the Pi and run initial system updates (`sudo apt update && sudo apt upgrade`).
  * Install **ROS 2 Humble Hawksbill** (barebones or desktop depending on headless preference).
  * Copy `config/cyclonedds_local.xml` to the Pi and set the `CYCLONEDDS_URI` environment variable to ensure the middleware uses the correct configuration.

### Block 3: Verification & Network Handshake (20 mins)
* **Goal**: Prove basic connectivity between the Supervisor and the Edge Node.
* **Actions**:
  * Create a minimal ROS 2 Publisher node in `src/sentry_logic/` on the Pi (or your dev machine) that broadcasts a "heartbeat".
  * Verify that the DDS network is active and the middleware can route packets locally.

## Definition of Done (DoD) for this session:
- [ ] 1x Arduino Nano flashed with boilerplate code.
- [ ] 1x Raspberry Pi running Ubuntu 22.04 and ROS 2 Humble.
- [ ] CycloneDDS configuration applied and ready for next steps.
