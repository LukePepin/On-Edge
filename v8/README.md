# On-Edge V8 experiment system

Acquisition daemon (Raspberry Pi), campaign runner, recorder, and dashboard (Windows) for the trust-monitor
timing experiment, plus the instrumented firmware in `../firmware/trust_monitor_v8/`.

* Operating instructions: [`docs/v8/EXECUTION_GUIDE.md`](../docs/v8/EXECUTION_GUIDE.md)
* Architecture (what changed and why): [`docs/v8/ARCHITECTURE.md`](../docs/v8/ARCHITECTURE.md)
* Data format: [`docs/v8/DATASET_SCHEMA.md`](../docs/v8/DATASET_SCHEMA.md)
* Proposed V8 matrix: [`docs/v8/V8_MATRIX_PROPOSAL.md`](../docs/v8/V8_MATRIX_PROPOSAL.md)
* Approvals and unverified behaviour: [`docs/v8/PENDING_APPROVALS.md`](../docs/v8/PENDING_APPROVALS.md)
* Test record: [`docs/v8/VERIFICATION.md`](../docs/v8/VERIFICATION.md)

## Quick start

```
# any PC, no hardware (software simulation, data -> data/v8_sim)
powershell -ExecutionPolicy Bypass -File v8\scripts\start_sim_demo.ps1

# Pi (bench): acquisition daemon (in tmux)
python3 v8/scripts/daemon.py --config v8/config/daemon/pi_bench.json

# Windows lunchbox: SSH tunnel + dashboard on http://127.0.0.1:8080
powershell -ExecutionPolicy Bypass -File v8\scripts\start_dashboard.ps1

# tests (simulated only)
python -m unittest discover -s v8/tests
node --test v8/tests/js/modes.test.mjs
```

Standard library only, plus `pyserial` on the Pi and `rclpy` (from ROS 2) for robot mode.

## Layout

| Path | Contents |
| --- | --- |
| `onedge_v8/protocol.py` | framing, parsing, sequence/reset/clock continuity |
| `onedge_v8/clocks.py` | clock domains, same-clock intervals, device→host fit with ranges |
| `onedge_v8/telemetry.py` | freshness, joint samples by name, moving/standstill criteria |
| `onedge_v8/campaign.py` | config validation, seeded plan, model expectations (MODEL) |
| `onedge_v8/device_link.py` | the only serial owner (reader thread, validated commands) |
| `onedge_v8/runner.py` | campaign state machine, trial procedures, robot monitor |
| `onedge_v8/recorder.py`, `dataset.py` | append-only recording, tolerant readers, recovery, manifests |
| `onedge_v8/analysis.py` | per-attempt events, intervals, outcome, quality warnings |
| `onedge_v8/exclusions.py` | manual, reversible exclusions |
| `onedge_v8/robot.py`, `motion.py` | ROS 2 interface, UR dashboard client, pick-place program |
| `onedge_v8/sim.py` | software models of the monitor, serial link and robot (tests, rehearsal) |
| `onedge_v8/daemon.py`, `httpbase.py`, `replay.py`, `bus.py` | daemon, HTTP/SSE, replay payloads, display bus |
| `dashboard/` | Windows dashboard server and browser UI |
| `config/daemon/`, `config/campaigns/` | daemon modes, versioned campaign configurations |
| `scripts/` | start scripts, read-only Pi preflight, CLI fallback (`ctl.py`) |
| `tests/` | unit, end-to-end (simulated), firmware host emulation, dashboard, JS |
