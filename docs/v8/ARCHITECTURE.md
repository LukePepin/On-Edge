# V8 system: architecture and what changed

A short explanation to own and re-tell. Code: [`v8/`](../../v8/), firmware:
[`firmware/trust_monitor_v8/`](../../firmware/trust_monitor_v8/trust_monitor_v8.ino).

## Four machines, three kinds of path

```
 Windows lunchbox                     Raspberry Pi (acquisition host)                 Arduino Nano 33 BLE
 ┌──────────────────────┐   SSH       ┌──────────────────────────────────┐   USB      ┌────────────────────┐
 │ browser dashboard    │  tunnel     │ onedge_v8 daemon (one process)    │  serial    │ trust_monitor_v8   │
 │ dashboard server     │◄──────────► │  DeviceLink  ── only serial owner │◄─────────► │ workload → EWMA →  │
 │  · live proxy        │  127.0.0.1  │  Runner      ── campaign states   │            │ threshold → D12    │
 │  · replay of copies  │   :8765     │  Recorder    ── append-only files │            └─────────┬──────────┘
 │  · exclusions, sync  │             │  RobotMonitor── joint/safety data │                      │ D12 (3.3 V)
 └──────────────────────┘             │  HTTP + event stream (read/ctl)   │               optocoupler (documented)
                                      └──────────────┬───────────────────┘                      │
                                                     │ ROS 2 (UR driver): /joint_states,        ▼
                                                     │ safety mode, program state, trajectory  UR5 safeguard
                                                     ▼                                          inputs SI0/SI1
                                                   UR5 controller  (Ethernet; dashboard server :29999)
```

* **Control path:** operator → dashboard → (tunnel) → daemon → runner → DeviceLink → serial → firmware.
  The robot trajectory goes runner → ROS action → controller.
* **Data path:** firmware records → DeviceLink → Recorder (disk, first) → event bus → dashboard (display).
  Robot telemetry: driver → RobotMonitor → Recorder → bus.
* **Safety path:** firmware D12 → optocoupler → controller safeguard inputs. No software here is part of it.

## Design rules (each one answers a known historical weakness)

| Historical behaviour | V8 behaviour |
| --- | --- |
| Logger flushed the serial input buffer before each read and dropped partial lines | One reader thread; bytes accumulate across reads; complete lines are parsed; **nothing is flushed**; every raw byte is saved (base64) with host receipt time |
| Trust stored as "latest value"; repeated CSV rows looked fresh | Every record has a sequence number; gaps, duplicates, resets are detected and recorded; freshness is explicit (fresh / stale / missing / invalid / unavailable) |
| No device timestamps | Device `micros()` on every record, unwrapped per boot; events: configuration applied, ATTACK/RECOVER processed, trust update, first D12-low command |
| Stale joint feedback became six zero velocities | Missing telemetry stays missing; joints mapped by **name**; standstill only from a declared criterion on fresh samples, otherwise "undetermined" |
| Attack flag set before the injection thread even ran | Host records request, write start and write end of each command; device records when it processed it |
| Attack fired 0.5 s after sending the sweep, whether or not the arm moved | Injection only after motion is confirmed on fresh telemetry, else `failed_precondition` and no injection |
| Campaign discarded and reshuffled trials until they "worked"; auto-unlocked protective stops and pressed play | Every attempt is kept; nothing is rerun automatically; faults put the campaign in HOLD for an operator decision (retry/skip/abort, recorded with a reason); protective stops are never unlocked automatically |
| `sudo`, `pkill -f`, iptables, tshark, `chrt` in the trial wrapper | None. The daemon refuses to open the port if another process holds it (and says which PID) |

## The six events kept separate

| # | Event | Observed by | Clock | Record |
| --- | --- | --- | --- | --- |
| 1 | Host command request / sent | daemon | host monotonic | `serial_tx.jsonl` |
| 2 | Device processed ATTACK / RECOVER | firmware | device µs | `cmd` record |
| 3 | Trust update below 30 | firmware | device µs | first `upd` with `below=1` |
| 4 | Firmware commanded D12 low | firmware | device µs | `out` record (level 0) |
| 5 | Electrical D12 transition | **not measured by this software** (oscilloscope needed) | — | — |
| 6 | Robot motion / standstill | UR driver telemetry + declared criterion | ROS stamp → host monotonic | `joint_states.csv` → summary |

Also recorded: the controller's reported safety mode (host receipt time), trajectory goal events.

## Clocks and intervals

* Intervals are computed on **one clock**: device-clock intervals (2→3, 2→4, 3→4) are the primary V8
  measures; host-clock intervals (1→receipt of 3) include transport and scheduling.
* Device time and host time are related only through a fitted line (minimum-delay fit: a record cannot
  arrive before it was sent). Cross-clock results carry a range because the minimum transport delay is not
  measured (assumed ≤ 2 ms). Code enforces this: `clocks.interval_ms` refuses mixed clocks.
* Dashboard plots use host receipt time for display only; they are never used as event timestamps.

## Firmware: what changed and what did not

Unchanged (verified bit-for-bit on a host emulation against the template): workloads, DWT timing, EWMA
recurrence, observation and penalty rules, strict `< 30` threshold, D12 behaviour (low on every
below-threshold update, raised only at boot and by configuration), command semantics, `delay(10)`.
Added: one JSON record per event with `seq` and `t_us`, formatted into one buffer and written once per
record; each update reports how long the previous report write took (`pw_us`) so reporting overhead is
measured, not assumed. See [FIRMWARE_V8.md](FIRMWARE_V8.md).

## Campaigns

A campaign JSON declares factor levels (each with a purpose), design, repetitions, ordering with a seed, and
the trial procedure. The runner expands it into an explicit plan (saved with its SHA-256); the operator
must start with the hash of the plan they previewed. Changing a config without bumping `config_version`
is refused once data exist for that version.

Attempt = one execution of one planned trial. Statuses: completed, failed_setup, failed_precondition,
failed_procedure, failed_acquisition, fault_robot, aborted_operator, interrupted. A completed trial without
a crossing is valid data. Acquisition-quality warnings (sequence gaps, malformed records, resets, telemetry
gaps, penalty observations, operator commands during an attempt) pause the campaign for review but never
exclude data. Manual exclusions live in a separate, append-only file and can be restored.

## Failure handling

* Serial disconnect or device reset during an attempt → `failed_acquisition` → HOLD. Reconnection uses
  backoff (a flapping port cannot flood the disk).
* Robot protective stop / E-stop / unexpected safeguard stop / trajectory fault → `fault_robot` → HOLD.
* Recorder write error or backlog → HOLD.
* Dashboard disconnect → the current attempt finishes on its own timing; the next trial does not start
  (heartbeat timeout 10 s). Acquisition and recording do not depend on the dashboard.
* Daemon crash → partial files remain; on restart, unfinished attempts are marked `interrupted` in new files.
* Abort → trajectory cancel request, no further ATTACK/RECOVER, no reconfiguration (which would raise D12).
  **Not an emergency stop.**

## Historical observation made while building this

The first V6 CSV rows match the Pick pose only after rotating the six joint columns by one position
(error 0.0001 rad vs 2.8 rad as labelled); sampled V7 files fit the same rotation. The historical logger
copied the driver's message order (which appears to start with shoulder_lift) under canonical labels.
Per-joint labels in V6/V7 CSVs are therefore probably shifted; metrics using the maximum over all joints
are unaffected. V8 maps joints by name and stores the original order.
