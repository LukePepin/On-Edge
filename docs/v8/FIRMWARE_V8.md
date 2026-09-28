# trust_monitor_v8 firmware: changes, flashing, verification

Source: [`firmware/trust_monitor_v8/trust_monitor_v8.ino`](../../firmware/trust_monitor_v8/trust_monitor_v8.ino).
The historical [`unified_trust_monitor_template.ino`](../../firmware/unified_trust_monitor_template/unified_trust_monitor_template.ino)
is **unchanged** (it documents what ran for V6/V7).

## What is identical to the template

Workload calls, DWT timing and `/ 64000.0` conversion, observation rule (ATTACK → 0; otherwise
100 − (exec − 150 or 400 ms) when over the threshold), EWMA line
`trust_score = (ewma_alpha * current_trust) + ((1.0 - ewma_alpha) * trust_score);`, strict `< 30` test,
`digitalWrite(12, LOW)` on every below-threshold update, D12 HIGH at boot and on configuration only,
ATTACK/RECOVER/config semantics, the quirk that an unknown `algo` keeps the previous workload, 115200 baud,
`delay(10)` per cycle. The penalty thresholds are now named constants with the same double values.

Evidence (software only): `v8/tests/test_firmware_host.py` compiles **both** sketches for the PC with a
virtual clock and mocked Serial/GPIO/uECC and runs 12 scripted scenarios (three alphas, both workloads,
command times near cycle boundaries, repeated ATTACK at 20 Hz, reconfiguration, ±0.4 ms workload jitter).
Trust (bit-exact float), cycle, attack flag and every `digitalWrite` are identical at identical virtual
times. The only source change for that build redirects the three DWT register addresses to variables.

## What is added

* One JSON record per event, each with `ev`, `seq` (per-boot counter) and `t_us` (`micros()`), emitted in
  device-time order and written with a **single** `Serial.write()` (the template issued seven prints per
  report). See [DATASET_SCHEMA.md](DATASET_SCHEMA.md) for fields.
* `pw_us` in each update: how long the previous update's write took on the device, so reporting overhead is
  measured on the device clock.
* `boot` once when the port opens; `hello` every 1 s while waiting for configuration; `idle` heartbeat when
  no workload is selected; `err` for malformed/unknown/oversized input (previously ignored silently).
* No `"status": "READY"` and no `trust_score` key: the historical logger fails its handshake loudly instead
  of logging a stale trust value. The V8 host can still read the historical protocol (degraded) if the old
  firmware must be used.

Compile check on the lunchbox (Arduino CLI, `arduino:mbed_nano:nano33ble`, core 4.6.0, ArduinoJson 7.4.3):
V8 102,264 B flash / 44,952 B RAM vs template 100,672 / 44,664. `uECC.h` is **not a separate library**: the
mbed_nano core puts micro-ecc (pre-1.0 API, `uECC_BYTES`, secp256r1) from the Cordio BLE stack on the include
path (`…/FEATURE_BLE/libraries/TARGET_CORDIO_LL/stack/thirdparty/uecc`). The link map shows `uECC_make_key`
resolved from the core (2026-09-28). The template presumably built against the same code, but that is not
verified; compare workload times on the bench (B3).

## Flashing (Luke, physically; approval B1)

1. On the lunchbox (Arduino IDE, core Arduino Mbed OS Nano Boards 4.6.0, ArduinoJson 7.4.3; uECC comes with
   the core): open `firmware/trust_monitor_v8/trust_monitor_v8.ino`.
2. Board "Arduino Nano 33 BLE". Record in the session notes: IDE version, core version, ArduinoJson version,
   the machine used, and the `build` string from the boot record.
3. Upload. Close the Serial Monitor afterwards (the V8 daemon must be the only port owner).
4. Rollback: re-flash `unified_trust_monitor_template.ino` (historical behaviour), and run the V8 daemon
   anyway — it reads the legacy protocol, with missing-update detection from `cycle` but no device times.

## Verify after flashing (bench, approval B2)

Start the daemon (`pi_bench.json`) and check on the dashboard's quality panel, or with
`python3 v8/scripts/ctl.py status`:
* Firmware shows `trust_monitor_v8 8.0.0 (<build date/time>)`; protocol `v8`; the build string matches the
  upload you just did.
* Records arrive; missing (sequence) = 0; malformed = 0 (the first line after connect may be a partial line,
  flagged `first_after_connect`).
* Run `v8-demo-bench`; in replay, check the model check agrees (2 updates at α 0.5, 4 at α 0.3, 12 at α 0.1),
  `device_cross_to_out_low` is a few µs, and D12 stays commanded LOW after RECOVER until the next configuration.

## Instrumentation overhead assessment

Per attempt, `summary.json` → `updates.loop_period_ms` (device clock, consecutive cycles only),
`updates.exec_ms` (DWT) and `updates.report_write_us` (`pw_us`). Report:
* loop period − exec − 10 ms delay = command handling + report cost per cycle (device clock);
* `pw_us` distribution = cost of the single report write;
* comparison with the historical host-observed report intervals (120.4 / 232.1 ms) as a between-instrument
  comparison only.
If the V8 loop period exceeds the historical summaries by more than the measured write cost, investigate
before interpreting timing results (e.g. a slow host reader stalling USB writes).

## Safety note to review with the lab

Inherited behaviour, unchanged: D12 is driven HIGH at boot (`setup()`), before configuration or any trust
evaluation. A Nano reset or re-plug therefore closes the safeguard loop. The robot program is paused after a
safeguard stop and needs Play, but this is a property of the robot configuration, not of the monitor.
