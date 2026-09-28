"""V8 acquisition daemon (runs on the Raspberry Pi; runs on any PC in simulated mode).

  python3 -m onedge_v8.daemon --config v8/config/daemon/pi_hardware.json
  python  -m onedge_v8.daemon --config v8/config/daemon/sim_local.json

The daemon owns the trust-monitor serial port, subscribes to robot telemetry, runs campaigns,
records everything, and serves a local HTTP API (default 127.0.0.1:8765; reach it from the
Windows dashboard through an SSH tunnel). Acquisition never depends on a connected client.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import platform
import signal
import socket
import subprocess
import sys
import threading
import time

from . import DAEMON_CONFIG_SCHEMA, DATASET_SCHEMA, SOFTWARE_NAME, SOFTWARE_VERSION
from . import dataset, replay
from .bus import EventBus
from .device_link import DeviceLink
from .exclusions import ExclusionError, ExclusionRegistry
from .httpbase import HttpError, RawFile, Router, SSE, Server, require
from .recorder import Recorder
from .robot import NullRobot, RosRobot
from .runner import CampaignRunner, RobotMonitor, RunnerError
from .telemetry import MotionCriteria
from .transport import SerialTransport

PKG_DIR = os.path.dirname(os.path.abspath(__file__))
V8_DIR = os.path.dirname(PKG_DIR)
REPO_ROOT = os.path.dirname(V8_DIR)


def _sha256(path: str) -> str | None:
    try:
        with open(path, "rb") as f:
            return hashlib.sha256(f.read()).hexdigest()
    except OSError:
        return None


def software_provenance() -> dict:
    def git(*args):
        try:
            r = subprocess.run(["git", "-C", REPO_ROOT, *args], capture_output=True, text=True, timeout=5)
            return r.stdout.strip() if r.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            return None
    porcelain = git("status", "--porcelain")
    files = {os.path.relpath(os.path.join(PKG_DIR, n), REPO_ROOT).replace(os.sep, "/"): _sha256(os.path.join(PKG_DIR, n))
             for n in sorted(os.listdir(PKG_DIR)) if n.endswith(".py")}
    fw = os.path.join(REPO_ROOT, "firmware", "trust_monitor_v8", "trust_monitor_v8.ino")
    return {"name": SOFTWARE_NAME, "version": SOFTWARE_VERSION, "dataset_schema": DATASET_SCHEMA,
            "git_commit": git("rev-parse", "HEAD"), "git_branch": git("rev-parse", "--abbrev-ref", "HEAD"),
            "git_dirty": bool(porcelain) if porcelain is not None else None,
            "git_modified": porcelain.splitlines()[:50] if porcelain else [],
            "source_sha256": files, "firmware_source_sha256": _sha256(fw),
            "firmware_note": "source hash identifies the repository file, not the binary flashed on the Nano; "
                             "the device reports its own build stamp in boot/hello records",
            "python": sys.version.split()[0], "platform": platform.platform(), "hostname": socket.gethostname()}


def load_daemon_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        cfg = json.load(f)
    if cfg.get("schema") != DAEMON_CONFIG_SCHEMA:
        raise SystemExit(f"{path}: schema must be {DAEMON_CONFIG_SCHEMA}")
    if cfg.get("mode") not in ("hardware", "simulated"):
        raise SystemExit(f"{path}: mode must be 'hardware' or 'simulated'")
    return cfg


def _resolve(p: str) -> str:
    return p if os.path.isabs(p) else os.path.join(REPO_ROOT, p)


class Daemon:
    def __init__(self, cfg: dict, config_path: str | None = None):
        self.cfg = cfg
        self.mode = cfg["mode"]
        self.simulated = self.mode == "simulated"
        default_root = "data/v8_sim" if self.simulated else "data/v8"
        self.data_root = _resolve(cfg.get("data_root", default_root))
        if self.simulated and os.path.abspath(self.data_root) == os.path.abspath(_resolve("data/v8")):
            raise SystemExit("simulated mode must not write into the hardware data root data/v8")
        self.campaign_dir = _resolve(cfg.get("campaign_dir", "v8/config/campaigns"))
        self.software = software_provenance()
        self.rt = self._try_realtime(cfg.get("realtime") or {})
        run_meta = {"schema": DATASET_SCHEMA, "daemon_config": cfg, "config_path": config_path,
                    "software": self.software, "mode": self.mode, "simulated": self.simulated,
                    "data_origin": "software_simulation" if self.simulated else "hardware", "realtime": self.rt,
                    "started_wall_ns": time.time_ns(), "started_mono_ns": time.monotonic_ns()}
        os.makedirs(self.data_root, exist_ok=True)
        self.recovered = self._recover_previous()
        self.recorder = Recorder(self.data_root, run_meta=run_meta)
        self.bus = EventBus()
        self.monitor = None
        if self.simulated:
            from .sim import SimFaults, SimMonitor, SimRobot, SimRobotFaults, SimTransport
            scfg = cfg.get("sim") or {}
            mon_cfg = dict(scfg.get("monitor") or {})
            faults = SimFaults(**(mon_cfg.pop("faults", {}) or {}))
            self.monitor = SimMonitor(faults=faults, **mon_cfg)
            self.monitor.start()
            factory = lambda: SimTransport(self.monitor)  # noqa: E731
        else:
            scfg = cfg.get("serial") or {}
            factory = lambda: SerialTransport(port=scfg.get("port", "auto"), baud=int(scfg.get("baud", 115200)),  # noqa: E731
                                              by_id_pattern=scfg.get("by_id_pattern", "*Arduino*Nano_33_BLE*"))
        tel = cfg.get("telemetry") or {}
        self.link = DeviceLink(factory, self.recorder, self.bus, device_stale_ms=float(tel.get("device_stale_ms", 1000)))
        rcfg = cfg.get("robot") or {"interface": "none"}
        iface = rcfg.get("interface", "none")
        if iface == "sim":
            from .sim import SimRobot, SimRobotFaults
            self.robot = SimRobot(self.monitor, faults=SimRobotFaults(**(rcfg.get("faults") or {})),
                                  **{k: v for k, v in rcfg.items() if k in ("rate_hz", "controller_delay_ms", "decel_ms")})
        elif iface == "ros":
            self.robot = RosRobot(rcfg)
        else:
            self.robot = NullRobot()
        self.rm = RobotMonitor(self.recorder, self.bus, self.robot.capabilities(),
                               joint_stale_ms=float(tel.get("joint_stale_ms", 100)))
        self.robot.start(self.rm.on_joint, self.rm.on_state, self.rm.on_event)
        self.rm.caps = self.robot.capabilities()
        self.rm.fresh.configured = bool(self.rm.caps.get("joint_telemetry"))
        if getattr(self.robot, "import_errors", None):
            self.recorder.record_event({"t_mono_ns": time.monotonic_ns(), "event": "robot_interface_limits",
                                        "errors": self.robot.import_errors})
        self.criteria = MotionCriteria.from_dict(tel)
        op = cfg.get("operator") or {}
        self.runner = CampaignRunner(self.link, self.robot, self.rm, self.recorder, self.bus, self.campaign_dir,
                                     self.mode, self.software, operator_timeout_s=float(op.get("heartbeat_timeout_s", 10)))
        self.exclusions = ExclusionRegistry(self.data_root)
        self.link.start()
        api = cfg.get("api") or {}
        self.server = Server(self._router(), api.get("bind", "127.0.0.1"), int(api.get("port", 8765)),
                             static_dir=_resolve("v8/dashboard/static") if api.get("serve_dashboard", True) else None)
        self.server.start()
        self.recorder.record_event({"t_mono_ns": time.monotonic_ns(), "t_wall_ns": time.time_ns(),
                                    "event": "daemon_started", "api_port": self.server.port,
                                    "recovered_sessions": self.recovered})

    # ------------------------------------------------------------------ helpers
    def _try_realtime(self, rt: dict) -> dict:
        if not rt.get("try_sched_fifo"):
            return {"requested": False}
        try:
            os.sched_setscheduler(0, os.SCHED_FIFO, os.sched_param(int(rt.get("priority", 50))))
            return {"requested": True, "applied": True, "priority": int(rt.get("priority", 50))}
        except (AttributeError, PermissionError, OSError) as exc:
            return {"requested": True, "applied": False, "error": str(exc)}

    def _recover_previous(self) -> list:
        out = []
        for s in dataset.list_sessions(self.data_root):
            sdir = os.path.join(self.data_root, "sessions", s["session_id"])
            if s["state"] == "open_or_interrupted":
                marked = dataset.recover_session(sdir)
                out.append({"session_id": s["session_id"], "interrupted_attempts": marked})
        return out

    def info(self) -> dict:
        return {"service": "onedge_v8 acquisition daemon", "mode": self.mode, "simulated": self.simulated,
                "data_origin": "software_simulation" if self.simulated else "hardware", "software": self.software,
                "data_root": self.data_root, "campaign_dir": self.campaign_dir, "run_id": self.recorder.run_id,
                "realtime": self.rt, "robot_interface": self.robot.kind, "recovered_sessions": self.recovered}

    def status(self) -> dict:
        return {"t_mono_ns": time.monotonic_ns(), "t_wall_ns": time.time_ns(), "mode": self.mode,
                "simulated": self.simulated, "link": self.link.status(), "robot": self.rm.status(self.criteria),
                "recorder": self.recorder.status(), "runner": self.runner.status(), "bus": self.bus.stats()}

    def shutdown(self):
        self.runner.shutdown()
        self.server.stop()
        self.link.stop()
        try:
            self.robot.stop()
        except Exception:
            pass
        if self.monitor:
            self.monitor.stop()
        self.recorder.record_event({"t_mono_ns": time.monotonic_ns(), "t_wall_ns": time.time_ns(),
                                    "event": "daemon_stopped"})
        self.recorder.stop()

    # ------------------------------------------------------------------ API
    def _router(self) -> Router:
        r = Router()
        run = self.runner

        def wrap(fn):
            def inner(h, params, query, body):
                try:
                    return fn(params, query, body)
                except RunnerError as exc:
                    raise HttpError(409, str(exc))
                except ExclusionError as exc:
                    raise HttpError(400, str(exc))
                except (KeyError, ValueError, TypeError) as exc:
                    raise HttpError(400, f"bad request: {exc}")
            return inner

        def op(body):
            return (body.get("operator") or "operator").strip()[:64]

        r.add("GET", "/api/info", wrap(lambda p, q, b: self.info()))
        r.add("GET", "/api/status", wrap(lambda p, q, b: self.status()))
        r.add("GET", "/api/stream", lambda h, params, query, body: SSE(self._stream(h, query)))
        r.add("GET", "/api/campaigns", wrap(lambda p, q, b: {"campaigns": run.list_campaigns()}))
        r.add("GET", r"/api/campaigns/(?P<name>[A-Za-z0-9_.\-]+\.json)", wrap(lambda p, q, b: run.preview(p["name"])))

        def start(p, q, b):
            require(b, "file", "plan_sha256", "operator")
            return run.start(b["file"], b["plan_sha256"], op(b), b.get("acknowledgements") or [])
        r.add("POST", "/api/campaign/start", wrap(start))
        r.add("POST", "/api/campaign/pause", wrap(lambda p, q, b: run.pause(b.get("reason") or "operator pause", op(b))))
        r.add("POST", "/api/campaign/resume", wrap(lambda p, q, b: run.resume(op(b))))

        def abort(p, q, b):
            require(b, "reason")
            return run.abort(b["reason"], op(b))
        r.add("POST", "/api/campaign/abort", wrap(abort))
        r.add("POST", "/api/campaign/confirm", wrap(lambda p, q, b: run.confirm_next(op(b), b.get("checks") or [])))

        def decide(p, q, b):
            require(b, "decision", "reason")
            return run.decide(b["decision"], b["reason"], op(b))
        r.add("POST", "/api/campaign/decision", wrap(decide))

        def manual(p, q, b):
            require(b, "cmd", "reason")
            return run.manual_command(b["cmd"], b["reason"], op(b), bool(b.get("confirm_departure")),
                                      b.get("workload"), b.get("alpha"))
        r.add("POST", "/api/manual", wrap(manual))

        def dash(p, q, b):
            require(b, "cmd")
            return run.robot_dashboard(b["cmd"], b.get("reason") or "", op(b))
        r.add("POST", "/api/robot/dashboard", wrap(dash))

        def note(p, q, b):
            require(b, "text")
            return run.note(b["text"], op(b))
        r.add("POST", "/api/note", wrap(note))

        def hb(p, q, b):
            run.heartbeat(str(b.get("client_id") or "unknown")[:64])
            return {"ok": True, "t_mono_ns": time.monotonic_ns()}
        r.add("POST", "/api/heartbeat", wrap(hb))

        # recorded data (read-only): replay and verified copying to the dashboard host
        r.add("GET", "/api/sessions", wrap(lambda p, q, b: {"data_root": self.data_root, "simulated": self.simulated,
                                                             "sessions": dataset.list_sessions(self.data_root)}))
        r.add("GET", r"/api/sessions/(?P<sid>[A-Za-z0-9_.\-]+)",
              wrap(lambda p, q, b: replay.session_payload(self.data_root, p["sid"], self.exclusions)))
        r.add("GET", r"/api/sessions/(?P<sid>[A-Za-z0-9_.\-]+)/attempts/(?P<aid>[A-Za-z0-9_.\-]+)",
              wrap(lambda p, q, b: replay.attempt_payload(self._attempt_dir(p["sid"], p["aid"]))))
        r.add("GET", r"/api/sessions/(?P<sid>[A-Za-z0-9_.\-]+)/manifest",
              wrap(lambda p, q, b: dataset.build_manifest(self._session_dir(p["sid"]))))

        def file(h, params, query, body):
            sdir = self._session_dir(params["sid"])
            try:
                return RawFile(dataset.safe_join(sdir, query.get("path", "")))
            except ValueError as exc:
                raise HttpError(403, str(exc))
        r.add("GET", r"/api/sessions/(?P<sid>[A-Za-z0-9_.\-]+)/file", file)
        return r

    def _session_dir(self, sid: str) -> str:
        d = dataset.safe_join(os.path.join(self.data_root, "sessions"), sid)
        if not os.path.isdir(d):
            raise HttpError(404, "session not found")
        return d

    def _attempt_dir(self, sid: str, aid: str) -> str:
        d = dataset.safe_join(os.path.join(self._session_dir(sid), "attempts"), aid)
        if not os.path.isdir(d):
            raise HttpError(404, "attempt not found")
        return d

    def _stream(self, handler, query):
        last = handler.headers.get("Last-Event-ID") or query.get("last_id")
        sub = self.bus.subscribe(int(last) if last and str(last).isdigit() else None)
        try:
            yield ("hello", None, self.info())
            next_status = 0.0
            while not self.server.stopping.is_set():
                now = time.monotonic()
                if now >= next_status:
                    yield ("status", None, self.status())
                    next_status = now + 1.0
                ev = sub.get(timeout=0.25)
                if ev is None:
                    continue
                yield (ev["kind"], ev["id"], ev)
        finally:
            sub.close()


def main(argv=None):
    ap = argparse.ArgumentParser(description="On-Edge V8 acquisition daemon")
    ap.add_argument("--config", required=True, help="daemon config JSON (v8/config/daemon/*.json)")
    ap.add_argument("--port", type=int, help="override API port")
    args = ap.parse_args(argv)
    cfg = load_daemon_config(args.config)
    if args.port:
        cfg.setdefault("api", {})["port"] = args.port
    d = Daemon(cfg, os.path.abspath(args.config))
    stop = threading.Event()

    def handler(signum, frame):
        stop.set()
    signal.signal(signal.SIGINT, handler)
    if hasattr(signal, "SIGTERM"):
        signal.signal(signal.SIGTERM, handler)
    label = "SIMULATED (software model; not hardware data)" if d.simulated else "HARDWARE"
    print(f"[onedge_v8] {label} daemon on http://{cfg.get('api', {}).get('bind', '127.0.0.1')}:{d.server.port}  "
          f"data -> {d.data_root}", flush=True)
    try:
        while not stop.is_set():
            stop.wait(0.5)
    finally:
        print("[onedge_v8] shutting down (active attempt, if any, is aborted and finalized)", flush=True)
        d.shutdown()


if __name__ == "__main__":
    main()
