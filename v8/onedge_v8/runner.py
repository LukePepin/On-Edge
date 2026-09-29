"""Campaign runner: executes a saved trial plan; never reruns or discards on its own.

States
  IDLE                  no session
  RUNNING               executing trials (an attempt may be active)
  AWAITING_CONFIRMATION robot procedures: waiting for the operator to confirm the next trial
  PAUSED                operator pause (takes effect between trials) or operator disconnect
  HOLD                  an attempt failed or needs review; waiting for an operator decision
  COMPLETED / ABORTED   session closed

Attempt statuses
  completed            procedure executed as planned (a trial without crossing is still data)
  failed_setup         configuration not acknowledged / robot not ready
  failed_precondition  e.g. arm not confirmed moving before injection (no injection sent)
  failed_procedure     e.g. ATTACK not acknowledged by the monitor
  failed_acquisition   serial disconnect, device reset, recorder error
  fault_robot          protective stop, emergency stop, unexpected safeguard stop, trajectory fault
  aborted_operator     controlled abort requested by the operator
  interrupted          (set later by dataset.recover_session when the process died)

Abort is a software sequence stop, NOT an emergency stop: it cancels the trajectory goal if
one is active, sends no further ATTACK/RECOVER, and does not reconfigure the monitor
(configuration would raise D12). Use the teach-pendant emergency stop for safety.
"""
from __future__ import annotations

import collections
import json
import os
import queue
import threading
import time
import traceback

from . import DATASET_SCHEMA, SOFTWARE_NAME, SOFTWARE_VERSION
from . import analysis, campaign, dataset, motion
from .device_link import LinkError, config_command
from .recorder import utc_stamp
from .telemetry import Freshness, FreshnessMonitor, MotionCriteria, classify_motion_now, confirm_moving, find_standstill

FAULT_SAFETY = {"PROTECTIVE_STOP", "SYSTEM_EMERGENCY_STOP", "ROBOT_EMERGENCY_STOP", "VIOLATION", "FAULT"}
SAFEGUARD = {"SAFEGUARD_STOP", "AUTOMATIC_MODE_SAFEGUARD_STOP"}
HOLD_WARNING_CODES = {"sequence_gap", "malformed_records", "device_reset_during_attempt", "attack_not_acknowledged",
                      "recover_not_acknowledged", "joint_telemetry_gap", "joint_telemetry_missing",
                      "robot_fault_safety_mode", "execution_time_penalty_observed", "operator_commands_during_attempt"}


class RunnerError(RuntimeError):
    pass


class TrialAbort(Exception):
    def __init__(self, status: str, reason: str):
        super().__init__(reason)
        self.status, self.reason = status, reason


class RobotMonitor:
    """Live robot observations: recent joint samples, freshness, safety/program state, events."""

    def __init__(self, recorder, bus, capabilities: dict, joint_stale_ms: float = 100.0, display_hz: float = 25.0):
        self.recorder, self.bus = recorder, bus
        self.caps = capabilities
        self.joints = collections.deque(maxlen=5000)
        self.fresh = FreshnessMonitor("joint_states", joint_stale_ms, configured=capabilities.get("joint_telemetry"))
        self.safety = None          # (value, name, rx_mono_ns)
        self.program = None         # (bool, rx_mono_ns)
        self.events = collections.deque(maxlen=500)
        self._lock = threading.Lock()
        self._display_period = int(1e9 / display_hz)
        self._next_display = 0
        self._win_max = None
        self._win_min = None
        self.samples = 0

    def on_joint(self, s):
        self.recorder.record_joint(s)
        self.fresh.note(s.rx_mono_ns, s.valid)
        self.samples += 1
        with self._lock:
            self.joints.append(s)
        v = s.max_abs_vel
        if v is not None:
            self._win_max = v if self._win_max is None else max(self._win_max, v)
            self._win_min = v if self._win_min is None else min(self._win_min, v)
        if s.rx_mono_ns >= self._next_display:          # display decimation (recording is full-rate)
            self._next_display = s.rx_mono_ns + self._display_period
            self.bus.publish("joint", {"rx_mono_ns": s.rx_mono_ns, "t_mono_ns": s.t_mono_ns, "valid": s.valid,
                                       "problem": s.problem, "vmax": v, "vmax_hi": self._win_max,
                                       "vmax_lo": self._win_min,
                                       "vel": list(s.velocity) if s.velocity else None})
            self._win_max = self._win_min = None

    def on_state(self, source: str, value: int, name: str):
        t_mono, t_wall = time.monotonic_ns(), time.time_ns()
        rec = {"rx_mono_ns": t_mono, "rx_wall_ns": t_wall, "source": source, "value": value, "name": name}
        with self._lock:
            if source == "safety_mode":
                self.safety = (value, name, t_mono)
            elif source == "program_running":
                self.program = (bool(value), t_mono)
        self.recorder.record("robot", rec)
        self.bus.publish("robot", rec)

    def on_event(self, ev: dict):
        rec = {"t_mono_ns": time.monotonic_ns(), "t_wall_ns": time.time_ns(), **ev}
        with self._lock:
            self.events.append(rec)
        self.recorder.record("host", rec)
        self.bus.publish("host", rec)

    def recent(self, since_ns: int) -> list:
        with self._lock:
            return [s for s in self.joints if s.rx_mono_ns >= since_ns]

    def latest(self):
        with self._lock:
            return self.joints[-1] if self.joints else None

    def safety_name(self):
        with self._lock:
            return self.safety[1] if self.safety else None

    def status(self, criteria: MotionCriteria) -> dict:
        now = time.monotonic_ns()
        st, age = self.fresh.state(now)
        recent = self.recent(now - int(1e9))
        motion_state = classify_motion_now(recent, now, st, criteria)
        latest = self.latest()
        return {"capabilities": self.caps, "joint_freshness": st.value, "joint_age_ms": age,
                "joint_samples": self.samples, "motion_state": motion_state,
                "latest_vmax": latest.max_abs_vel if latest and st == Freshness.FRESH else None,
                "safety_mode": self.safety_name(),
                "program_running": self.program[0] if self.program else None}


class CampaignRunner:
    def __init__(self, link, robot, robot_monitor: RobotMonitor, recorder, bus, campaign_dir: str, mode: str,
                 software: dict, operator_timeout_s: float = 10.0):
        self.link, self.robot, self.rm = link, robot, robot_monitor
        self.recorder, self.bus = recorder, bus
        self.campaign_dir = campaign_dir
        self.mode = mode                    # "hardware" or "simulated"
        self.software = software
        self.operator_timeout_s = operator_timeout_s
        self._lock = threading.RLock()
        self.state = "IDLE"
        self.state_reason = ""
        self.session = None
        self.plan = None
        self.cfg = None
        self.next_index = 0
        self.trials: dict = {}
        self.current = None
        self.hold = None
        self.last_attempt = None
        self._abort = threading.Event()
        self._confirm = threading.Event()
        self._pause_requested = None
        self._stop = False
        self._heartbeats: dict = {}
        self._departures: list = []
        self._thread = threading.Thread(target=self._run, name="runner", daemon=True)
        self._thread.start()

    # ================================================================== operator API
    def list_campaigns(self) -> list:
        return campaign.list_campaigns(self.campaign_dir)

    def _config_path(self, name: str) -> str:
        if os.sep in name or "/" in name or not name.endswith(".json"):
            raise RunnerError("campaign must be a .json file name in the campaign directory")
        path = os.path.join(self.campaign_dir, name)
        if not os.path.exists(path):
            raise RunnerError(f"campaign file not found: {name}")
        return path

    def preview(self, name: str) -> dict:
        cfg = campaign.load_config(self._config_path(name))
        try:
            plan = campaign.build_plan(cfg)
        except campaign.ConfigError as exc:
            return {"valid": False, "problems": exc.problems, "file": name}
        return {"valid": True, "file": name, "plan": plan, "preview_text": campaign.preview_text(plan),
                "warnings": self._start_warnings(plan)}

    def _start_warnings(self, plan: dict) -> list:
        w = []
        if self.mode == "simulated":
            w.append("SIMULATED MODE: data will be stored as software simulation, not hardware evidence")
        if plan["status"] != "approved" and plan["kind"] == "research":
            w.append("campaign status is 'proposed': the scientific matrix has not been approved for collection")
        if plan["kind"] == "demonstration":
            w.append("DEMONSTRATION preset: not a complete experimental campaign")
        if plan["procedure"] == "robot" and not self.rm.caps.get("trajectory"):
            w.append("robot procedure selected but no trajectory interface is available")
        return w

    def start(self, name: str, plan_sha256: str, operator: str, acknowledgements: list | None = None) -> dict:
        with self._lock:
            if self.state not in ("IDLE", "COMPLETED", "ABORTED"):
                raise RunnerError(f"cannot start: runner is {self.state}")
            path = self._config_path(name)
            with open(path, "r", encoding="utf-8") as f:
                config_text = f.read()
            cfg = json.loads(config_text)
            plan = campaign.build_plan(cfg)
            if plan["plan_sha256"] != plan_sha256:
                raise RunnerError("plan hash mismatch: preview the campaign again before starting")
            if not self.link.connected:
                raise RunnerError("trust-monitor link is not connected")
            if plan["procedure"] == "robot":
                caps = self.rm.caps
                missing = [k for k in ("joint_telemetry", "trajectory") if not caps.get(k)]
                if missing:
                    raise RunnerError(f"robot procedure needs {missing}")
                if "robot_motion_authorized" not in (acknowledgements or []):
                    raise RunnerError("robot procedure requires the operator acknowledgement 'robot_motion_authorized'")
            self._check_version_reuse(plan)
            sid = base = f"{utc_stamp()}_{plan['campaign_id']}_v{plan['config_version']}"
            k = 2
            while os.path.exists(os.path.join(self.recorder.data_root, "sessions", sid)):
                sid, k = f"{base}-{k}", k + 1
            simulated = self.mode == "simulated" or self.link.simulated or getattr(self.robot, "simulated", False)
            meta = {"schema": DATASET_SCHEMA, "session_id": sid, "campaign_id": plan["campaign_id"],
                    "config_version": plan["config_version"], "config_file": name, "title": plan["title"],
                    "kind": plan["kind"], "procedure": plan["procedure"], "campaign_status": plan["status"],
                    "simulated": simulated,
                    "data_origin": "software_simulation" if simulated else "hardware",
                    "started_wall": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                    "started_mono_ns": time.monotonic_ns(), "started_wall_ns": time.time_ns(),
                    "operator": operator, "acknowledgements": acknowledgements or [],
                    "plan_sha256": plan["plan_sha256"], "config_sha256": plan["config_sha256"],
                    "software": self.software, "device": self.link.status(),
                    "robot_capabilities": self.rm.caps, "clock_domains": _clock_doc(),
                    "units": {"device time": "us", "host times": "ns", "trust": "0-100", "exec_ms": "ms",
                              "joint position": "rad", "joint velocity": "rad/s"}}
            self.recorder.open_session(sid, meta, plan=plan, config_text=config_text)
            self.session, self.plan, self.cfg = meta, plan, plan["normalized_config"]
            self.trials = {t["trial_id"]: {"attempts": [], "final": None, "reason": None} for t in plan["trials"]}
            self.next_index = 0
            self.hold = None
            self.last_attempt = None
            self._abort.clear()
            self._confirm.clear()
            self._pause_requested = None
            self._set_state("RUNNING", "campaign started")
            self._session_event("session_started", operator=operator, plan_sha256=plan["plan_sha256"])
            return {"session_id": sid}

    def _check_version_reuse(self, plan):
        """A campaign id + version must always mean the same config text."""
        for s in dataset.list_sessions(self.recorder.data_root):
            if s.get("campaign_id") != plan["campaign_id"]:
                continue
            meta = dataset.read_json(os.path.join(self.recorder.data_root, "sessions", s["session_id"], "session.json")) or {}
            if meta.get("config_version") == plan["config_version"] and meta.get("config_sha256") != plan["config_sha256"]:
                raise RunnerError(f"{plan['campaign_id']} v{plan['config_version']} was already run with different "
                                  "content: bump config_version when editing a campaign")

    def pause(self, reason: str, operator: str = "operator") -> dict:
        with self._lock:
            if self.state == "RUNNING":
                self._pause_requested = reason or "operator pause"
                self._session_event("pause_requested", reason=reason, operator=operator)
                return {"ok": True, "note": "pause takes effect after the current attempt"}
            if self.state == "AWAITING_CONFIRMATION":
                self._set_state("PAUSED", reason or "operator pause")
                return {"ok": True}
            raise RunnerError(f"cannot pause in state {self.state}")

    def resume(self, operator: str = "operator") -> dict:
        with self._lock:
            if self.state != "PAUSED":
                raise RunnerError(f"cannot resume in state {self.state}")
            self._pause_requested = None
            self._set_state("RUNNING", f"resumed by {operator}")
            return {"ok": True}

    def abort(self, reason: str, operator: str = "operator") -> dict:
        with self._lock:
            if self.state in ("IDLE", "COMPLETED", "ABORTED"):
                raise RunnerError("no active campaign")
            self._abort.set()
            self._session_event("abort_requested", reason=reason, operator=operator)
            return {"ok": True, "note": "controlled software abort; NOT an emergency stop"}

    def confirm_next(self, operator: str, checks: list | None = None) -> dict:
        with self._lock:
            if self.state != "AWAITING_CONFIRMATION":
                raise RunnerError(f"nothing to confirm in state {self.state}")
            self._session_event("trial_confirmed", operator=operator, checks=checks or [],
                                trial_id=self._next_trial()["trial_id"])
            self._confirm.set()
            return {"ok": True}

    def decide(self, decision: str, reason: str, operator: str) -> dict:
        with self._lock:
            if self.state != "HOLD" or not self.hold:
                raise RunnerError("no decision pending")
            if decision not in self.hold["allowed"]:
                raise RunnerError(f"decision must be one of {self.hold['allowed']}")
            reason = _reason(reason)
            trial = self._next_trial()
            self._session_event("operator_decision", decision=decision, reason=reason, operator=operator,
                                trial_id=trial["trial_id"], attempt_id=self.hold.get("attempt_id"))
            self.hold = None
            if decision == "abort":
                self._abort.set()
                self._set_state("RUNNING", "abort decided")
            elif decision == "skip":
                self.trials[trial["trial_id"]].update(final="skipped", reason=reason)
                self.next_index += 1
                self._set_state("RUNNING", "trial skipped")
            elif decision == "continue":
                self.next_index += 1
                self._set_state("RUNNING", "continued after review")
            elif decision == "retry":
                self._set_state("RUNNING", "retry requested (new attempt)")
            return {"ok": True}

    def manual_command(self, cmd: str, reason: str, operator: str, confirm_departure: bool = False,
                       workload: str | None = None, alpha: float | None = None) -> dict:
        """Operator ATTACK / RECOVER / CONFIG. Always recorded; flagged as a procedure departure."""
        reason = _reason(reason)
        with self._lock:
            active = self.current is not None
            if active and not confirm_departure:
                raise RunnerError("an attempt is running: manual commands depart from the procedure; "
                                  "confirm the departure explicitly")
            if cmd == "CONFIG":
                try:
                    text = config_command(workload, alpha)
                except (LinkError, TypeError, ValueError) as exc:
                    raise RunnerError(f"invalid manual configuration: {exc}")
            elif cmd in ("ATTACK", "RECOVER"):
                text = cmd
            else:
                raise RunnerError("manual command must be ATTACK, RECOVER or CONFIG")
            context = "during_attempt" if active else ("between_trials" if self.session else "no_session")
            note = f"manual {cmd} by {operator} ({context}): {reason}"
            if active:
                self._departures.append({"t_mono_ns": time.monotonic_ns(), "cmd": cmd, "operator": operator,
                                         "reason": reason})
        try:
            rec = self.link.send(text, purpose=f"manual_{cmd.lower()}", source="operator", note=note)
        except LinkError as exc:
            raise RunnerError(str(exc))
        self._session_event("manual_command", cmd=cmd, context=context, operator=operator, reason=reason,
                            departure=context != "no_session")
        return {"ok": True, "context": context, "tx": rec}

    def robot_dashboard(self, cmd: str, reason: str, operator: str) -> dict:
        from .robot import READ_ONLY_DASHBOARD, STATE_CHANGING_DASHBOARD
        cmd = cmd.strip()
        if cmd in STATE_CHANGING_DASHBOARD:
            with self._lock:
                if self.current is not None:
                    raise RunnerError("state-changing robot commands are not allowed during an attempt")
            reason = _reason(reason)
        elif cmd not in READ_ONLY_DASHBOARD:
            raise RunnerError("command not allowed")
        res = self.robot.dashboard(cmd)
        self._session_event("robot_dashboard", cmd=cmd, reason=reason, operator=operator, result=res)
        return res

    def note(self, text: str, operator: str) -> dict:
        self._session_event("operator_note", text=text[:2000], operator=operator)
        return {"ok": True}

    def heartbeat(self, client_id: str):
        with self._lock:
            self._heartbeats[client_id] = time.monotonic()

    def operator_present(self) -> bool:
        now = time.monotonic()
        with self._lock:
            return any(now - t <= self.operator_timeout_s for t in self._heartbeats.values())

    def shutdown(self, reason: str = "daemon shutdown", timeout_s: float = 30.0):
        if self.state not in ("IDLE", "COMPLETED", "ABORTED"):
            self._abort.set()
            self._session_event("abort_requested", reason=reason, operator="daemon")
            deadline = time.monotonic() + timeout_s
            while self.state not in ("IDLE", "COMPLETED", "ABORTED") and time.monotonic() < deadline:
                time.sleep(0.1)
        self._stop = True
        self._thread.join(timeout=5)

    # ================================================================== status
    def status(self) -> dict:
        with self._lock:
            plan = self.plan
            done = sum(1 for t in self.trials.values() if t["final"] == "completed")
            skipped = sum(1 for t in self.trials.values() if t["final"] == "skipped")
            attempts = sum(len(t["attempts"]) for t in self.trials.values())
            nxt = self._next_trial() if plan and self.next_index < len(plan["trials"]) else None
            return {"state": self.state, "state_reason": self.state_reason, "mode": self.mode,
                    "session": None if not self.session else {
                        k: self.session[k] for k in ("session_id", "campaign_id", "config_version", "title", "kind",
                                                     "procedure", "simulated", "data_origin", "campaign_status")},
                    "progress": None if not plan else {"n_trials": plan["n_trials"], "completed": done,
                                                       "skipped": skipped, "attempts": attempts,
                                                       "next_index": self.next_index},
                    "next_trial": nxt, "current": self.current, "hold": self.hold,
                    "last_attempt": self.last_attempt, "pause_requested": self._pause_requested,
                    "operator_present": self.operator_present(),
                    "procedure": plan["procedure"] if plan else None,
                    "telemetry_criteria": self.cfg["telemetry"] if self.cfg else None}

    # ================================================================== internals
    def _set_state(self, state: str, reason: str = ""):
        self.state, self.state_reason = state, reason
        rec = {"t_mono_ns": time.monotonic_ns(), "t_wall_ns": time.time_ns(), "event": "runner_state",
               "state": state, "reason": reason}
        self.recorder.record_event(rec)
        self.bus.publish("runner", rec)

    def _session_event(self, event: str, **detail):
        rec = {"t_mono_ns": time.monotonic_ns(), "t_wall_ns": time.time_ns(), "event": event, **detail}
        self.recorder.record_event(rec)
        self.bus.publish("session", rec)

    def _next_trial(self):
        return self.plan["trials"][self.next_index]

    def _run(self):
        while not self._stop:
            try:
                self._tick()
            except Exception as exc:          # never let the runner thread die silently
                self._session_event("runner_error", error=str(exc), trace=traceback.format_exc()[-3000:])
                with self._lock:
                    if self.session and self.state not in ("COMPLETED", "ABORTED"):
                        self.hold = {"reason": f"internal runner error: {exc}", "allowed": ["retry", "skip", "abort"],
                                     "attempt_id": None}
                        self._set_state("HOLD", "internal error")
            time.sleep(0.02)

    def _tick(self):
        with self._lock:
            state = self.state
            if state in ("IDLE", "COMPLETED", "ABORTED"):
                return
            if self._abort.is_set() and self.current is None:
                self._close_session("ABORTED", "operator abort")
                return
            if state != "RUNNING" and state != "AWAITING_CONFIRMATION":
                return
            if self._pause_requested:
                self._set_state("PAUSED", self._pause_requested)
                self._pause_requested = None
                return
            if self.cfg["progression"]["pause_on_operator_disconnect"] and not self.operator_present():
                self._set_state("PAUSED", "operator connection lost (no dashboard heartbeat)")
                return
            if self.next_index >= len(self.plan["trials"]):
                self._close_session("COMPLETED", "all planned trials resolved")
                return
            trial = self._next_trial()
            if self.cfg["progression"]["mode"] == "operator_confirm_each_trial" and not self._confirm.is_set():
                if state != "AWAITING_CONFIRMATION":
                    self._set_state("AWAITING_CONFIRMATION", f"confirm {trial['trial_id']} to start it")
                return
            self._confirm.clear()
            n = len(self.trials[trial["trial_id"]]["attempts"]) + 1
            attempt_id = f"{trial['trial_id']}_A{n}"
            if state != "RUNNING":
                self._set_state("RUNNING", f"starting {attempt_id}")
        result = self._run_attempt(trial, n, attempt_id)
        with self._lock:
            self.trials[trial["trial_id"]]["attempts"].append({"attempt_id": attempt_id, "status": result["status"],
                                                                "reason": result["reason"]})
            self.last_attempt = {"attempt_id": attempt_id, "trial_id": trial["trial_id"], **result}
            if result["status"] == "aborted_operator" or self._abort.is_set():
                self._close_session("ABORTED", result["reason"] or "operator abort")
                return
            if result.get("recorder_unhealthy"):
                self.hold = {"reason": f"recorder unhealthy after {attempt_id}: {result['recorder_unhealthy']}",
                             "allowed": ["retry", "skip", "abort"], "attempt_id": attempt_id}
                self._set_state("HOLD", "recording problem: check disk and data before continuing")
                return
            if result["status"] == "completed":
                self.trials[trial["trial_id"]]["final"] = "completed"
                review = [w for w in result.get("warnings", []) if w.get("code") in HOLD_WARNING_CODES]
                if review:
                    self.hold = {"reason": "completed with acquisition-quality warnings: "
                                           + ", ".join(sorted({w["code"] for w in review})),
                                 "allowed": ["continue", "retry", "abort"], "attempt_id": attempt_id,
                                 "warnings": review}
                    self._set_state("HOLD", "review warnings before continuing")
                    return
                self.next_index += 1
            else:
                self.hold = {"reason": f"{result['status']}: {result['reason']}", "allowed": ["retry", "skip", "abort"],
                             "attempt_id": attempt_id}
                self._set_state("HOLD", "attempt did not complete")
                return
        self._interruptible_sleep(self.cfg["trial"]["inter_trial_ms"] / 1000.0)

    def _close_session(self, final: str, reason: str):
        summary = {tid: t for tid, t in self.trials.items()}
        end = {"schema": DATASET_SCHEMA, "final_state": final, "reason": reason, "ended_wall_ns": time.time_ns(),
               "ended_mono_ns": time.monotonic_ns(), "trials": summary,
               "counts": {"planned": len(self.trials),
                          "completed": sum(1 for t in summary.values() if t["final"] == "completed"),
                          "skipped": sum(1 for t in summary.values() if t["final"] == "skipped"),
                          "unresolved": sum(1 for t in summary.values() if t["final"] is None),
                          "attempts": sum(len(t["attempts"]) for t in summary.values())}}
        self._session_event("session_closed", final_state=final, reason=reason)
        self.recorder.close_session(end, manifest_fn=dataset.build_manifest)
        self.session = None
        self.hold = None
        self._abort.clear()
        self._set_state(final, reason)

    def _interruptible_sleep(self, seconds: float):
        end = time.monotonic() + seconds
        while time.monotonic() < end and not self._abort.is_set():
            time.sleep(min(0.02, max(0.0, end - time.monotonic())))

    # ================================================================== attempt execution
    def _run_attempt(self, trial: dict, n: int, attempt_id: str) -> dict:
        cfg = self.cfg
        t_start_mono, t_start_wall = time.monotonic_ns(), time.time_ns()
        start_meta = {"schema": DATASET_SCHEMA, "attempt_id": attempt_id, "attempt": n, **trial,
                      "session_id": self.session["session_id"], "procedure": cfg["procedure"],
                      "trial_config": cfg["trial"], "telemetry_config": cfg["telemetry"],
                      "t_mono_ns": t_start_mono, "t_wall_ns": t_start_wall, "device": self.link.status(),
                      "robot": self.rm.status(MotionCriteria.from_dict(cfg["telemetry"])),
                      "simulated": self.session["simulated"], "manual": False}
        adir = self.recorder.begin_attempt(attempt_id, start_meta)
        with self._lock:
            self.current = {"attempt_id": attempt_id, "trial_id": trial["trial_id"], "phase": "starting",
                            "condition_id": trial["condition_id"], "workload": trial["workload"],
                            "alpha": trial["alpha"], "failure_ms": trial["failure_ms"],
                            "repetition": trial["repetition"], "attempt": n, "t_start_mono_ns": t_start_mono}
            self._departures = []
        ctx = {"trial": trial, "attempt_id": attempt_id, "start_mono": t_start_mono,
               "resets0": self.link.cont.resets, "disc0": self.link.disconnects, "out_low": None,
               "attack_sent": False, "recover_sent": False, "phase": "starting"}
        status, reason = "completed", ""
        try:
            if cfg["procedure"] == "robot":
                self._attempt_robot(ctx)
            else:
                self._attempt_bench(ctx)
        except TrialAbort as ta:
            status, reason = ta.status, ta.reason
        except Exception as exc:
            status, reason = "failed_procedure", f"internal error: {exc}"
            self._host_event("attempt_internal_error", error=traceback.format_exc()[-3000:])
        if status == "aborted_operator":
            self._on_abort_cleanup(ctx)
        with self._lock:
            departures = list(self._departures)
        end_meta = {"schema": DATASET_SCHEMA, "attempt_id": attempt_id, "status": status, "reason": reason,
                    "phase_reached": ctx["phase"], "attack_sent": ctx["attack_sent"],
                    "recover_sent": ctx["recover_sent"], "departures": departures,
                    "t_mono_ns": time.monotonic_ns(), "t_wall_ns": time.time_ns(),
                    "device_continuity": self.link.cont.summary(), "recorder": self.recorder.status()}
        self.recorder.end_attempt(end_meta)
        warnings = []
        if not self.recorder.healthy:
            with self._lock:
                self.current = None
            return {"status": status, "reason": reason, "warnings": [], "departures": departures,
                    "recorder_unhealthy": self.recorder.errors[-1:] or ["write backlog"]}
        try:
            summary = analysis.summarize_attempt_dir(adir)
            summary["generated_by"] = f"{SOFTWARE_NAME} {SOFTWARE_VERSION}"
            self.recorder.write_derived(adir, "summary.json", summary)
            self.recorder.sync()
            warnings = summary.get("quality_warnings", [])
        except Exception as exc:
            self._host_event("summary_failed", error=str(exc))
        with self._lock:
            self.current = None
        return {"status": status, "reason": reason, "warnings": warnings, "departures": departures}

    # ---- checks and helpers ----------------------------------------------------------------
    def _phase(self, ctx, phase: str, **detail):
        ctx["phase"] = phase
        with self._lock:
            if self.current:
                self.current["phase"] = phase
        self._host_event("phase", phase=phase, **detail)

    def _host_event(self, event: str, **detail):
        rec = {"t_mono_ns": time.monotonic_ns(), "t_wall_ns": time.time_ns(), "event": event, **detail}
        self.recorder.record("host", rec)
        self.bus.publish("host", rec)

    def _check(self, ctx, allow_safeguard: bool = False):
        if self._abort.is_set():
            raise TrialAbort("aborted_operator", "operator abort requested")
        if not self.link.connected or self.link.disconnects > ctx["disc0"]:
            raise TrialAbort("failed_acquisition", "trust-monitor serial link disconnected")
        if self.link.cont.resets > ctx["resets0"]:
            raise TrialAbort("failed_acquisition", "trust-monitor reset detected (device epoch changed)")
        if not self.recorder.healthy:
            raise TrialAbort("failed_acquisition", f"recorder error: {self.recorder.errors[-1]}")
        if self.cfg["procedure"] == "robot":
            name = self.rm.safety_name()
            if name in FAULT_SAFETY:
                raise TrialAbort("fault_robot", f"robot safety mode {name}")
            if name in SAFEGUARD and not allow_safeguard:
                raise TrialAbort("fault_robot", f"unexpected {name} before the monitor commanded D12 low")

    def _wait(self, ctx, seconds: float, allow_safeguard: bool = False, until=None):
        end = time.monotonic() + seconds
        while True:
            self._check(ctx, allow_safeguard)
            if until is not None:
                r = until()
                if r:
                    return r
            left = end - time.monotonic()
            if left <= 0:
                return None
            time.sleep(min(0.005, left))

    def _configure(self, ctx, allow_safeguard: bool = False):
        """Send the trial configuration (resets trust/cycle/attack and raises D12) and wait for the ack.

        allow_safeguard: in robot trials the previous trial usually left D12 low, so the robot is
        in the expected, latched safeguard stop until this configuration raises D12 again."""
        trial, t = ctx["trial"], self.cfg["trial"]
        text = config_command(trial["workload"], trial["alpha"])
        for k in range(1, t["config_attempts"] + 1):
            self._check(ctx, allow_safeguard)
            try:
                tx = self.link.send(text, purpose="trial_config")
            except LinkError as exc:
                raise TrialAbort("failed_acquisition", f"configuration not sent: {exc}")
            after = tx["t_write_end_mono_ns"]

            def ok(rec):
                f = rec.get("f") or {}
                if rec["status"] != "ok":
                    return False
                if rec["kind"] == "cfg":
                    return (f.get("wl") == trial["workload"] and abs(f.get("alpha", -1) - trial["alpha"]) < 5e-5
                            and f.get("trust") == 100.0 and f.get("cycle") == 0 and f.get("d12") == 1)
                return rec["kind"] == "legacy_ready"
            rec = self.link.wait_for(ok, t["config_ack_timeout_ms"] / 1000.0, after_rx_ns=after)
            if rec is not None:
                self._host_event("configuration_acknowledged", attempt=k, protocol=rec["proto"])
                ctx["protocol"] = rec["proto"]
                return rec
            self._host_event("configuration_not_acknowledged", attempt=k)
        raise TrialAbort("failed_setup", "the monitor did not acknowledge the configuration")

    def _inject(self, ctx, allow_safeguard_after_out_low: bool = False):
        trial, t = ctx["trial"], self.cfg["trial"]
        legacy = ctx.get("protocol") == "legacy"
        self._phase(ctx, "inject", failure_ms=trial["failure_ms"])
        try:
            tx = self.link.send("ATTACK", purpose="trial_attack")
        except LinkError as exc:
            raise TrialAbort("failed_acquisition", f"ATTACK not sent: {exc}")
        ctx["attack_sent"] = True
        t_attack = tx["t_write_end_mono_ns"]
        if not legacy:
            ack = self.link.wait_for(lambda r: r["status"] == "ok" and r["kind"] == "cmd"
                                     and r["f"]["cmd"] == "ATTACK" and r["f"]["prev"] == 0,
                                     t["attack_ack_timeout_ms"] / 1000.0, after_rx_ns=t_attack)
            if ack is None:
                try:
                    self.link.send("RECOVER", purpose="trial_recover_after_unacknowledged_attack")
                except LinkError:
                    pass
                raise TrialAbort("failed_procedure", "ATTACK was not acknowledged by the monitor")
        self._phase(ctx, "failure_window")
        resend = t["attack_resend_interval_ms"] / 1000.0
        next_resend = time.monotonic() + resend if resend else None
        end = t_attack / 1e9 + trial["failure_ms"] / 1000.0
        while True:
            self._check(ctx, allow_safeguard=self._out_low_seen(ctx) or allow_safeguard_after_out_low)
            now = time.monotonic()
            if now >= end:
                break
            if next_resend and now >= next_resend:
                try:
                    self.link.send("ATTACK", purpose="trial_attack_resend")
                except LinkError as exc:
                    raise TrialAbort("failed_acquisition", f"ATTACK resend failed: {exc}")
                next_resend += resend
            time.sleep(min(0.002, max(0.0, end - now)))
        try:
            tx2 = self.link.send("RECOVER", purpose="trial_recover")
        except LinkError as exc:
            raise TrialAbort("failed_acquisition", f"RECOVER not sent: {exc}")
        ctx["recover_sent"] = True
        if not legacy:
            ack = self.link.wait_for(lambda r: r["status"] == "ok" and r["kind"] == "cmd"
                                     and r["f"]["cmd"] == "RECOVER", t["recover_ack_timeout_ms"] / 1000.0,
                                     after_rx_ns=tx2["t_write_end_mono_ns"])
            if ack is None:
                self._host_event("recover_not_acknowledged")

    def _out_low_seen(self, ctx) -> bool:
        if ctx.get("out_low"):
            return True
        rec = self.link.wait_for(lambda r: r["status"] == "ok" and r["kind"] == "out" and r["f"]["level"] == 0,
                                 0.0, after_rx_ns=ctx["start_mono"])
        if rec is not None:
            ctx["out_low"] = rec
            return True
        return False

    def _on_abort_cleanup(self, ctx):
        """Abort: stop motion requests only. No ATTACK/RECOVER, no reconfiguration (would raise D12)."""
        try:
            self.robot.cancel_trajectory()
        except Exception:
            pass
        self._host_event("abort_cleanup", note="trajectory cancel requested if active; monitor state left unchanged")

    # ---- procedures ----------------------------------------------------------------------------
    def _attempt_bench(self, ctx):
        trial, t = ctx["trial"], self.cfg["trial"]
        self._phase(ctx, "configure")
        self._configure(ctx)
        self._phase(ctx, "baseline", ms=t["baseline_ms"] + trial["injection_jitter_ms"])
        self._wait(ctx, (t["baseline_ms"] + trial["injection_jitter_ms"]) / 1000.0)
        if trial["failure_ms"] > 0:
            self._inject(ctx)
        else:
            self._phase(ctx, "no_injection_control")
            self._wait(ctx, 0.0)
        self._phase(ctx, "observe", ms=t["post_recover_ms"])
        self._wait(ctx, t["post_recover_ms"] / 1000.0)
        self._phase(ctx, "complete")

    def _attempt_robot(self, ctx):
        trial, t = ctx["trial"], self.cfg["trial"]
        m = t["motion"]
        scale = float(m.get("time_scale", 1.0))
        crit = MotionCriteria.from_dict(self.cfg["telemetry"])
        self._phase(ctx, "robot_preconditions")
        st, _ = self.rm.fresh.state(time.monotonic_ns())
        if st != Freshness.FRESH:
            raise TrialAbort("failed_setup", f"joint telemetry is {st.value}; fresh telemetry is required")
        name = self.rm.safety_name()
        if name in FAULT_SAFETY:
            raise TrialAbort("fault_robot", f"robot safety mode {name}: resolve at the teach pendant")
        if self.robot.trajectory_active():
            # never raise D12 while a goal is active: the real UR5 resumes a paused goal when the loop closes
            self._host_event("stale_trajectory_cancel",
                             note="a trajectory goal from an earlier attempt is still active; cancelling before re-arming")
            self.robot.cancel_trajectory()
            if not self._wait(ctx, 5.0, allow_safeguard=True, until=lambda: not self.robot.trajectory_active()):
                raise TrialAbort("fault_robot", "an earlier trajectory goal is still active: stop the External Control "
                                                "program at the teach pendant (Stop, not Pause) before retrying")
        self._phase(ctx, "configure")
        self._configure(ctx, allow_safeguard=True)   # raises D12 -> safeguard loop closes
        if self.rm.caps.get("safety_mode"):
            ok = self._wait(ctx, 5.0, allow_safeguard=True, until=lambda: self.rm.safety_name() == "NORMAL")
            if not ok:
                raise TrialAbort("failed_setup", f"safety mode did not return to NORMAL after re-arming "
                                                 f"(now {self.rm.safety_name()}); a safeguard reset may be required")
        if self.rm.caps.get("program_state"):
            prog = self.rm.program[0] if self.rm.program else None
            if not prog:
                if m.get("resume_program") == "dashboard_play":
                    res = self.robot.dashboard("play")
                    self._host_event("dashboard_play", result=res)
                self._phase(ctx, "waiting_for_program", note="press Play on the teach pendant if the program is paused")
                ok = self._wait(ctx, float(m.get("program_wait_s", 60.0)),
                                until=lambda: bool(self.rm.program and self.rm.program[0]))
                if not ok:
                    raise TrialAbort("failed_setup", "robot program not running")
        if m.get("switch_controller_each_trial", True):
            ok, text = self.robot.activate_trajectory_controller()
            self._host_event("controller_switch", ok=ok, detail=text)
            if not ok:
                raise TrialAbort("failed_setup", f"could not activate the trajectory controller: {text}")
        ok, text = self.robot.controller_ok()
        self._host_event("controller_check", ok=ok, detail=text)
        if not ok:
            raise TrialAbort("failed_setup", f"trajectory controller not ready: {text}")
        # phase 1: approach
        self._phase(ctx, "approach")
        cur = self.rm.latest()
        if cur is None or not cur.valid:
            raise TrialAbort("failed_setup", "no valid joint sample for the start pose")
        n_ev = len(self.rm.events)
        self.robot.send_trajectory(1, motion.JOINT_NAMES, motion.phase1_points(list(cur.position), m["approach_s"], scale))
        self._await_traj(ctx, 1, n_ev, "accepted", 5.0)
        res = self._await_traj(ctx, 1, n_ev, ("succeeded", "aborted", "canceled", "rejected", "finished"),
                               m["approach_s"] * scale + 10.0)
        if res.get("status") not in ("succeeded", "finished"):
            raise TrialAbort("fault_robot", f"approach trajectory {res.get('status')}: {res.get('reason', '')}")
        self._phase(ctx, "settle")
        t0 = time.monotonic_ns()
        ok = self._wait(ctx, m["settle_timeout_ms"] / 1000.0,
                        until=lambda: find_standstill(self.rm.recent(t0), t0, crit).status == "reached")
        if not ok:
            raise TrialAbort("failed_precondition", "arm did not settle at the start pose")
        # phase 2: sweep, confirm motion, then inject
        self._phase(ctx, "sweep")
        cur = self.rm.latest()
        n_ev = len(self.rm.events)
        self.robot.send_trajectory(2, motion.JOINT_NAMES, motion.phase2_points(list(cur.position), scale))
        acc = self._await_traj(ctx, 2, n_ev, "accepted", 5.0)
        t_acc = acc["t_mono_ns"]
        self._phase(ctx, "confirm_moving")
        mv = self._wait(ctx, m["moving_timeout_ms"] / 1000.0,
                        until=lambda: (lambda r: r if r.status == "reached" else None)(
                            confirm_moving(self.rm.recent(t_acc), t_acc, crit)))
        if not mv:
            if m["require_moving"]:
                self.robot.cancel_trajectory()
                raise TrialAbort("failed_precondition", "arm not confirmed moving on fresh telemetry; no injection sent")
            self._host_event("moving_not_confirmed", note="require_moving is false; injecting anyway")
        else:
            self._host_event("moving_confirmed", t_window_start_mono_ns=mv.t_mono_ns)
        wait_s = (m["inject_after_moving_ms"] + trial["injection_jitter_ms"]) / 1000.0
        self._phase(ctx, "pre_injection", ms=wait_s * 1000)
        self._wait(ctx, wait_s)
        if trial["failure_ms"] > 0:
            self._inject(ctx)
        self._phase(ctx, "observe", ms=t["post_recover_ms"])
        self._wait(ctx, t["post_recover_ms"] / 1000.0, allow_safeguard=self._out_low_seen(ctx))
        if self._out_low_seen(ctx):
            self._end_stopped_sweep(ctx, n_ev, crit, m)
            return
        self._phase(ctx, "await_trajectory_end")
        res = self._await_traj(ctx, 2, n_ev, ("succeeded", "aborted", "canceled", "rejected", "finished"),
                               float(m["trajectory_timeout_s"]), allow_safeguard=True)
        if res.get("status") in ("aborted", "canceled") and not self._out_low_seen(ctx):
            raise TrialAbort("fault_robot", f"sweep trajectory {res.get('status')} without the monitor commanding D12 low")
        self._phase(ctx, "complete", trajectory=res.get("status"))

    def _end_stopped_sweep(self, ctx, n_ev: int, crit, m):
        """The monitor commanded D12 low. The real UR5 pauses the sweep goal in the safeguard stop (no
        result) and resumes it when the loop closes (URI, 2026-09-29), so waiting for the result only
        times out. Record the held stop, then cancel the goal while D12 is still low."""
        t_low = ctx["out_low"]["rx_mono_ns"]
        ended = lambda: self._traj_event(n_ev, 2, ("succeeded", "aborted", "canceled", "finished"))
        self._phase(ctx, "await_standstill")
        self._wait(ctx, float(m["trajectory_timeout_s"]), allow_safeguard=True,
                   until=lambda: ended() or find_standstill(self.rm.recent(t_low), t_low, crit).status == "reached")
        self._wait(ctx, 1.0, allow_safeguard=True)           # keep recording the held stop briefly
        res = ended()
        if res is None:
            self._phase(ctx, "cancel_trajectory")
            self.robot.cancel_trajectory()
            res = self._wait(ctx, 5.0, allow_safeguard=True, until=ended)
            if not res:
                raise TrialAbort("fault_robot", "sweep goal still active after cancel: stop the External Control "
                                                "program at the teach pendant (Stop, not Pause) before continuing")
        self._phase(ctx, "complete", trajectory=res.get("status"), stop="commanded by the monitor")

    def _traj_event(self, n_ev: int, phase: int, statuses):
        for e in list(self.rm.events)[n_ev:]:
            if e.get("event") == "trajectory" and e.get("phase") in (phase, None) and e.get("status") in statuses:
                return e
        return None

    def _await_traj(self, ctx, phase: int, n_ev: int, statuses, timeout_s: float, allow_safeguard: bool = False) -> dict:
        wanted = (statuses,) if isinstance(statuses, str) else tuple(statuses)

        def find():
            evs = list(self.rm.events)[n_ev:]
            for e in evs:
                if e.get("event") == "trajectory" and e.get("phase") in (phase, None):
                    if e.get("status") == "rejected" and "rejected" not in wanted:
                        raise TrialAbort("fault_robot", f"phase-{phase} trajectory rejected: {e.get('reason', '')}")
                    if e.get("status") in wanted:
                        return e
            return None
        allow = allow_safeguard or self._out_low_seen(ctx)
        r = self._wait(ctx, timeout_s, allow_safeguard=allow, until=find)
        if r is None:
            raise TrialAbort("fault_robot", f"timeout waiting for phase-{phase} trajectory {wanted}")
        return r


def _reason(reason) -> str:
    """Operator reasons are optional (Luke, 2026-09-29); an empty one is recorded explicitly."""
    return reason.strip() if isinstance(reason, str) and reason.strip() else "(no reason given)"


def _clock_doc() -> dict:
    return {"device_us": "Nano micros(); 32-bit on the wire, unwrapped per device epoch; comparable only "
                         "within one epoch",
            "host_mono_ns": "time.monotonic_ns() on the recording host; used for host intervals",
            "host_wall_ns": "time.time_ns() on the recording host; reference only",
            "ros_stamp_ns": "ROS header.stamp from the UR driver (Pi system clock); converted to host_mono_ns "
                            "per sample using the wall-monotonic offset at receipt",
            "cross_clock": "device<->host only via onedge_v8.clocks.ClockFit (min-delay fit) with an assumed "
                           "minimum-latency bound"}
