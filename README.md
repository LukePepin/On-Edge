# On-Edge: Decentralized ZKP Authorization Meshes

This repository contains the source code, simulation scripts, and data analysis pipelines for the Master's thesis: **Decentralized ZKP Authorization Meshes for Industrial Robotics in DIL Environments**.

## Abstract
Modern automated logistics and Manufacturing Execution Systems (MES) operating within Department of Defense (DoD) Contested Logistics environments face catastrophic drops in Overall Equipment Effectiveness (OEE) when cloud-dependent authentication fails under high-density signal jamming. This research investigates the exact network-failure threshold (p*) where decentralized Edge-First Mobile Ad hoc Network (MANET) authentication utilizing Zero-Knowledge Proofs (ZKPs) maintains operational continuity.

## Workspace Structure
This repository is configured as a ROS 2 `colcon` workspace.
- `src/`: ROS 2 packages and hardware firmware.
- `requirements.txt`: Python dependencies for data analysis and network disruption.
- `architecture.md`: Details of the cluster topology.
- `todo.md`: Schedule and phases of the project.
- `laundrylist.md`: Hardware requirements and Bill of Materials.

## Setup Instructions
1. Install ROS 2 Humble Hawksbill on Ubuntu 22.04 LTS.
2. Install Python dependencies: `pip install -r requirements.txt`
3. Build the colcon workspace:
   ```bash
   colcon build --symlink-install
   ```
4. Source the setup script:
   ```bash
   source install/setup.bash
   ```

## Accessing the Supervisor (Raspberry Pi)
The Raspberry Pi is configured with mDNS for dynamic network access without needing a static IP. You can SSH into it from any computer on the local network using:
```bash
ssh seeker@on-edge-pi.local
```
