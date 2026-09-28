# V8 software verification record

Date: 2026-09-28. Platform: Windows 11, Python 3.13.14, Node 22.20.0, g++ 15.2 (MSYS2), Arduino CLI with
`arduino:mbed_nano` 4.6.0. **Scope: software only.** No test touched the Pi, the Nano, the UR5, or a serial
port. Bench-tested: nothing yet. Robot-tested: nothing yet.

## Results

| Suite | Command (repo root) | Result |
| --- | --- | --- |
| Python unit + end-to-end (simulated) | `python -m unittest discover -s v8/tests` | **81 tests OK** (68 s; includes serial port auto-selection) |
| Dashboard gating (JS) | `node --test v8/tests/js/modes.test.mjs` | **8 tests OK** |
| Firmware compile | `arduino-cli compile --fqbn arduino:mbed_nano:nano33ble firmware/trust_monitor_v8` (uECC from the mbed_nano 4.6.0 core; linked, per map file) | both sketches compile; V8 102,264 B flash / 44,952 B RAM (+1.6 KB, +288 B vs template) |
| Python 3.10 syntax scan | 3.10 grammar parse + nested-f-string-quote check | no newer constructs in 30 files (static only) |
| Manual end-to-end via the dashboard (simulated) | `sim-smoke` (12 attempts), `sim-robot-demo` (3 attempts, operator confirmations) | all attempts completed and replayed |

## Coverage against the requested checks

| Requirement | Tests |
| --- | --- |
| Partial / multiple / malformed serial messages | `test_protocol.FramerTests` (partial across reads, several per read, CRLF, overflow, unterminated at disconnect); `ParseTests` (malformed JSON, `nan`, wrong types, out-of-range trust, invalid UTF-8, unknown types, legacy protocol); runner with 1–7-byte random chunks and all raw bytes accounted for |
| Missing sequence records, resets, clock wrap | `ContinuityTests` (gap count, duplicate, boot → new epoch, regression, 32-bit wrap, large backstep = reset, small backstep ≠ reset, legacy cycle gaps); runner with 25 % dropped lines → HOLD for review; firmware host test with the Nano clock starting 3 s before the 32-bit wrap |
| Stale / absent joint telemetry | `FreshnessTests`; `JointAndMotionTests` (name mapping in the UR ROS 2 order, invalid messages never zero-filled, gaps → undetermined, data ending early → undetermined, preceding gap exposed, stale → "unknown"); robot runner with a telemetry dropout → no injection |
| Live / replay / simulated separation | JS gating tests (replay disables every control; simulated labelled; stale stream disables controls); dashboard server tests (replay-only dashboard refuses control; replay routes read-only; unknown control endpoints refused); simulated daemon refuses the hardware data root; simulated sessions labelled `software_simulation` and synced into the simulated root only |
| Campaign config, ordering, progress, attempt accounting | `test_campaign` (validation collects all problems, robot needs operator confirmation, sweep-fit check, approval metadata, seeded reproducible orders, complete blocks, explicit sequence, plan hash); runner: full campaign accounting (planned / completed / skipped / attempts), version reuse refused, plan hash must match |
| Disconnections, interrupted runs, recovery of saved data | runner: serial disconnect mid-attempt → `failed_acquisition` → retry creates A2 and keeps A1 (< 5 disconnect events, no reconnect storm); device reset → HOLD → skip recorded; crash mid-attempt → daemon restart marks `interrupted` without modifying data (hash check); truncated final JSONL line tolerated; recorder immutability (no reused run/session/attempt ids, create-once metadata) |
| Non-destructive exclusion and restoration | registry tests (reason required, scopes, restore, history kept, raw tree hash unchanged); dashboard API round-trip with counts |
| Timing definitions and timestamps | `ClockTests` (mixed-clock subtraction refused, epoch mismatch refused, fit recovers 40 ppm drift within 3 ppm, mapping is late by the minimum delay, cross-clock ranges); firmware float32 recurrence reproduces 70, 49, 34.30, 24.01, 16.81 and 12/4/2 updates; summaries carry the clock on every interval |
| Firmware algorithm preserved | `test_firmware_host`: V8 vs the untouched template, 12 scenario/jitter combinations — identical trust bits, cycles, attack flags and D12 writes at identical virtual times; each scenario must actually process ATTACK, decrease trust and write D12 LOW |
| Firmware record semantics | `test_firmware_host`: boot/hello/cfg/cmd/upd/out/err sequence, seq continuous from 0, device time non-decreasing with a per-`micros()` cost, crossing update `below=1 d12=0`, `out` after it, RECOVER does not raise D12, err codes, `pw_us` equals the modelled write time |
| Pause, abort, operator presence | runner tests: pause takes effect after the current attempt; abort mid-failure sends no RECOVER and no configuration; no dashboard heartbeat → PAUSED; manual command during an attempt requires confirmation and is recorded as a departure |
| Robot procedure (simulated arm) | confirmation per trial, motion acknowledgement required, moving confirmed before injection, safeguard report and standstill reached in the crossing trial, protective stop → `fault_robot` |

## Defects found by testing and fixed (kept here because they matter for trusting the data)

1. **Out-of-order device timestamps.** The configuration path emitted the `out` record (D12 raised, later
   timestamp) before `cfg` (earlier timestamp). The continuity checker read the backwards step as a device
   reset. Fixed in firmware and simulator (records in device-time order); the checker now tolerates small
   backwards steps (< 100 ms) and still treats large ones as resets. Mutation check: restoring the old
   order makes the firmware test fail.
2. **Reconnect storm.** A port that opens but fails on read produced 1.7 M disconnect events in seconds and
   a 3.4 M-item write backlog, delaying `attempt_end.json`. Fixed with reconnect backoff; the recorder now
   reports backlog/flush failures as unhealthy and the runner holds.
3. Equivalence test could pass without exercising the attack path → now asserts ATTACK processing, trust
   decrease and D12 LOW in every scenario.
4. Windows served `.js` as `text/plain` (module scripts refused) → explicit content types.
5. Simulator fault state per transport handle; legacy simulator leaking V8 records; control-trial narration;
   previous session's last attempt shown in a new session; test-order and timing races in two tests.

## Not verified (hardware, environment)

See [PENDING_APPROVALS.md](PENDING_APPROVALS.md) section C. In short: the Pi environment and Python 3.10 run
of the suite; the ROS interface (`RosRobot` has never executed); the real firmware build, USB timing and
overhead; the UR5 behaviour, safety configuration and network. Passing these tests does **not** validate
the complete system.

## Reproduce

```
python -m unittest discover -s v8/tests            # from the repo root (Pi: python3)
node --test v8/tests/js/modes.test.mjs
```
Firmware host tests need g++ and the ArduinoJson headers (`ONEDGE_GXX`, `ONEDGE_ARDUINOJSON_SRC` override the
search) and are skipped otherwise.
