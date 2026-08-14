# On-Edge: Edge-Local Trust Monitoring for Industrial Robots

Source code, orchestration scripts, firmware, and data for the Master's thesis project **On-Edge** (Luke Pepin, University of Rhode Island).

## Overview

Industrial robots draw authorization from a cloud identity provider: sever the network and the lease expires and the robot halts. That involuntary halt is a kill switch. On-Edge moves the authorization decision onto edge hardware beside the robot so it keeps operating through the outage. Because there is no longer an external authority that can revoke permission, the edge node must be able to stop the robot **itself**: it runs an EWMA trust score that decays when local verification degrades, and below 30 it drops a 24 V line through an optocoupler into a UR5's safeguard inputs and the arm halts — the final step is hardware, with no software in the loop.

The measured contribution is a **latency model** that predicts, from two numbers (verification cycle time and the EWMA weight α), how fast that stop happens — validated across **335 physical trials**.

## System at a Glance

| Component | Role |
|---|---|
| Raspberry Pi 4 | Supervisor/orchestrator — runs campaign scripts, probes cloud viability, logs telemetry |
| Arduino Nano 33 BLE ×2 (Cortex-M4) | **Crypto node** — verification workload, EWMA trust score, safety pin. **Sentry node** — cloud-viability state machine (CLOUD → ZKP → ECC → rejoin) |
| Dual-channel 24 V PNP optocoupler | Hardware safety intercept into the UR5's SI0/SI1 safeguard inputs (Category 2 stop; active-high, fail-safe on power loss) |
| Universal Robots UR5 | Industrial manipulator under test |

Communication is a **USB-serial star** (Pi ↔ Arduinos). An earlier wireless MANET / "ZKP authorization mesh" design was abandoned — see `docs/project_truth.md` §6.

## Repository Structure

- `docs/` — project documentation. **Start with `docs/ground_truth.md` and `docs/project_truth.md`** — the authoritative record of verified results and withdrawn claims; they supersede every other document where they conflict. Superseded material lives in `docs/archive/`.
- `firmware/` — bare-metal Arduino sketches: unified trust monitor, sentry node, real-ZKP profiler, cloud failback.
- `scripts/` — campaign orchestration and analysis (Python/bash), run on the Pi supervisor (`run_campaign.py`, `run_test.sh`, `analyze_*.py`, …).
- `src/` — ROS 2 packages (`sentry_logic`) for UR5 integration and telemetry logging.
- `data/` — CSV and PCAP trial data.
- `requirements.txt` — Python dependencies for data analysis and network disruption.

## Getting Started

On the Raspberry Pi supervisor:

1. Install Python dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Build the workspace (needed for the `sentry_logic` package and UR5 driver integration):
   ```bash
   colcon build --symlink-install
   ```
3. Source the setup script:
   ```bash
   source install/setup.bash
   ```

Arduino firmware in `firmware/` is flashed separately (Arduino IDE / PlatformIO); it is not built by `colcon`.

## Accessing the Supervisor (Raspberry Pi)

The Pi is configured with mDNS, so no static IP is needed:

```bash
ssh seeker@on-edge-pi.local
```

## Documentation Map

| Document | Contents |
|---|---|
| `docs/ground_truth.md` | The verified-numbers ledger — every retained figure traced to a file; withdrawn claims marked |
| `docs/project_truth.md` | The prose spine — what the project is, all retained and withdrawn claims |
| `docs/conclusion.md`, `docs/empirical_conclusions.md` | Corrected results narratives |
| `docs/system_architecture.md` | As-built topology and data flow |
| `docs/experimental_pivots.md` | Engineering-evolution history (micro-ROS → serial star, Ned2 → UR5, software stop → hardware intercept, …) |
| `docs/gaps.md` | Open vulnerabilities and future work (incl. the unbounded hold-down denial-of-safety gap) |
| `docs/decontamination_report.md` | Record of the 2026-08 documentation audit and cleanup |
