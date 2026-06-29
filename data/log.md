# Data Log

This folder tracks raw CSV and evaluation datasets used for the thesis graphing and metrics mapping.

## `latency_baseline.csv`
- **Origin:** Generated during Phase 1.5 (Synthetic Network Degradation).
- **Purpose:** Tracks the baseline round-trip latency of the wired/wireless network topology before and after injecting 15% artificial packet loss using Linux `tc` and `scapy`.

## `timeseries_evaluation.csv`
- **Origin:** Generated during Phase 2.4 (Selective Disclosure Sweeps).
- **Purpose:** Maps the precise CPU clock cycles (via DWT_CYCCNT on the Nano 33 BLE) against escalating cryptographic payload sizes (1 to 256 bytes) to determine the integer threshold boundaries for the Trust Monitor EWMA score.
