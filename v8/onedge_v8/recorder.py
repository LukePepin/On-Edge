"""Append-only, crash-tolerant recording of daemon runs, sessions and attempts.

Layout (see docs/v8/DATASET_SCHEMA.md):

  <data_root>/daemon_runs/<run_id>/       one per daemon start; ALWAYS recording
      run.json                  daemon configuration and software versions
      serial_rx_raw.jsonl       every byte read from the monitor while the daemon ran
      daemon_events.jsonl       link/robot/operator events outside a session
      *_nosession.jsonl         parsed records that arrived while no session was open

  <data_root>/sessions/<session_id>/      one per campaign execution
      session.json              created once at session start (never rewritten)
      campaign_config.json      verbatim copy of the campaign config file text
      plan.json                 the exact ordered plan that was executed
      session_events.jsonl      campaign / operator / runner events
      serial_rx_raw.jsonl       every byte read from the monitor during the session
      *_idle.jsonl              parsed records that arrived between attempts
      attempts.jsonl            one line when an attempt starts and one when it ends
      attempts/<attempt_id>/
          attempt_start.json    created once when the attempt begins
          device_msgs.jsonl     parsed monitor records (status, fields, host receipt times)
          serial_tx.jsonl       host commands: request, write start, write end
          host_events.jsonl     runner phases, trajectory events, dashboard queries
          robot_state.jsonl     controller safety/robot mode observations
          joint_states.csv      every joint_states message (no fill, invalid rows flagged)
          attempt_end.json      created once when the attempt is finalized
          summary.json          DERIVED metrics (regenerable), written after attempt_end
      session_end.json          created once when the session closes
      manifest.json             file sizes and SHA-256 at close

A missing attempt_end.json means the attempt was interrupted; dataset.recover_session()
records that fact in a separate file without touching the recorded data.

One writer thread performs all file I/O. Producers call record*(); the destination file is
chosen at call time, so records produced before end_attempt() always land in that attempt.
"""
from __future__ import annotations

import base64
import csv
import io
import json
import os
import queue
import shutil
import threading
import time

from .telemetry import CANONICAL_JOINTS

ATTEMPT_STREAMS = {"device": "device_msgs.jsonl", "tx": "serial_tx.jsonl", "host": "host_events.jsonl",
                   "robot": "robot_state.jsonl"}
IDLE_STREAMS = {k: v.replace(".jsonl", "_idle.jsonl") for k, v in ATTEMPT_STREAMS.items()}
NOSESSION_STREAMS = {k: v.replace(".jsonl", "_nosession.jsonl") for k, v in ATTEMPT_STREAMS.items()}
JOINT_HEADER = (["rx_mono_ns", "rx_wall_ns", "stamp_ns", "valid", "problem", "msg_order"]
                + [f"pos_{j}" for j in CANONICAL_JOINTS] + [f"vel_{j}" for j in CANONICAL_JOINTS])


def dumps(obj) -> str:
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def now_ns() -> tuple:
    return time.monotonic_ns(), time.time_ns()


def utc_stamp(t_wall_ns: int | None = None) -> str:
    t = (t_wall_ns if t_wall_ns is not None else time.time_ns()) / 1e9
    return time.strftime("%Y%m%dT%H%M%SZ", time.gmtime(t))


class RecorderError(RuntimeError):
    pass


def _csv_line(row) -> str:
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerow(row)
    return buf.getvalue()


class Recorder:
    def __init__(self, data_root: str, run_meta: dict | None = None, fsync_interval_s: float = 1.0,
                 run_id: str | None = None, backlog_limit: int = 50_000):
        self.data_root = os.path.abspath(data_root)
        self.fsync_interval_s = fsync_interval_s
        self.backlog_limit = backlog_limit
        self._q: queue.Queue = queue.Queue()
        self._lock = threading.Lock()
        self._files: dict = {}
        self._stop = False
        self.run_id = run_id or f"{utc_stamp()}_pid{os.getpid()}_{os.urandom(3).hex()}"
        self.run_dir = os.path.join(self.data_root, "daemon_runs", self.run_id)
        os.makedirs(os.path.dirname(self.run_dir), exist_ok=True)
        os.mkdir(self.run_dir)
        self.session_dir: str | None = None
        self.session_id: str | None = None
        self.attempt_dir: str | None = None
        self.attempt_id: str | None = None
        self.records_written = 0
        self.bytes_written = 0
        self.records_lost = 0
        self.max_queue = 0
        self.errors: list = []
        self.last_fsync_mono: int | None = None
        self._thread = threading.Thread(target=self._run, name="recorder", daemon=True)
        self._thread.start()
        self._write_once(os.path.join(self.run_dir, "run.json"), run_meta or {})

    # ------------------------------------------------------------------ status
    @property
    def healthy(self) -> bool:
        """False after any write error, or while the write queue is backlogged."""
        return not self.errors and self._q.qsize() < self.backlog_limit

    def status(self) -> dict:
        try:
            free = shutil.disk_usage(self.data_root).free
        except OSError:
            free = None
        return {"data_root": self.data_root, "run_id": self.run_id, "session_id": self.session_id,
                "attempt_id": self.attempt_id, "records_written": self.records_written,
                "bytes_written": self.bytes_written, "records_lost": self.records_lost,
                "queue_depth": self._q.qsize(), "max_queue": self.max_queue, "healthy": self.healthy,
                "errors": self.errors[-5:], "disk_free_bytes": free, "last_fsync_mono_ns": self.last_fsync_mono}

    # ------------------------------------------------------------------ lifecycle
    def open_session(self, session_id: str, session_meta: dict, plan: dict | None = None,
                     config_text: str | None = None) -> str:
        with self._lock:
            if self.session_dir is not None:
                raise RecorderError("a session is already open")
            sdir = os.path.join(self.data_root, "sessions", session_id)
            os.makedirs(os.path.dirname(sdir), exist_ok=True)
            os.mkdir(sdir)                      # fails if the session id already exists
            os.mkdir(os.path.join(sdir, "attempts"))
            self.session_dir, self.session_id = sdir, session_id
        self._write_once(os.path.join(sdir, "session.json"), session_meta)
        if config_text is not None:
            self._put(("once_text", os.path.join(sdir, "campaign_config.json"), config_text))
        if plan is not None:
            self._write_once(os.path.join(sdir, "plan.json"), plan)
        return sdir

    def close_session(self, end_meta: dict, manifest_fn=None) -> str | None:
        with self._lock:
            if self.attempt_id is not None:
                raise RecorderError("end the active attempt before closing the session")
            sdir = self.session_dir
        if sdir is None:
            return None
        self._write_once(os.path.join(sdir, "session_end.json"), end_meta)
        self._put(("close_prefix", sdir))
        with self._lock:
            self.session_dir, self.session_id = None, None
        self.sync()
        if manifest_fn is not None:
            try:
                self._write_once(os.path.join(sdir, "manifest.json"), manifest_fn(sdir))
                self.sync()
            except Exception as exc:  # the manifest is a convenience; data are already safe
                self.errors.append(f"manifest: {exc}")
        return sdir

    def begin_attempt(self, attempt_id: str, start_meta: dict) -> str:
        with self._lock:
            if self.session_dir is None:
                raise RecorderError("no session open")
            if self.attempt_id is not None:
                raise RecorderError(f"attempt {self.attempt_id} is still active")
            adir = os.path.join(self.session_dir, "attempts", attempt_id)
            os.mkdir(adir)                      # never reuse an attempt directory
            self.attempt_dir, self.attempt_id = adir, attempt_id
            index = os.path.join(self.session_dir, "attempts.jsonl")
        self._write_once(os.path.join(adir, "attempt_start.json"), start_meta)
        self._append(index, {"event": "attempt_started", "attempt_id": attempt_id, **_brief(start_meta)})
        return adir

    def end_attempt(self, end_meta: dict) -> str:
        with self._lock:
            adir, aid = self.attempt_dir, self.attempt_id
            if adir is None:
                raise RecorderError("no active attempt")
            self.attempt_dir, self.attempt_id = None, None
            index = os.path.join(self.session_dir, "attempts.jsonl")
        self._put(("close_prefix", adir))
        self._write_once(os.path.join(adir, "attempt_end.json"), end_meta)
        self._append(index, {"event": "attempt_ended", "attempt_id": aid, **_brief(end_meta)})
        if not self.sync(timeout=30.0):
            self.errors.append(f"attempt {aid}: end record not flushed within 30 s "
                               f"(write backlog {self._q.qsize()} items)")
        return adir

    def write_derived(self, directory: str, name: str, obj: dict):
        """Derived files (e.g. summary.json) are created once; regenerate offline if needed."""
        self._write_once(os.path.join(directory, name), obj)

    def stop(self):
        self.sync()
        self._stop = True
        self._put(("close_all",))
        self._thread.join(timeout=5)

    def sync(self, timeout: float = 10.0) -> bool:
        """Block until everything queued so far is written and flushed."""
        ev = threading.Event()
        self._put(("barrier", ev))
        return ev.wait(timeout)

    # ------------------------------------------------------------------ data
    def record(self, stream: str, rec: dict):
        """Parsed device records, host commands, host events, robot-state observations."""
        with self._lock:
            if self.attempt_dir is not None:
                path = os.path.join(self.attempt_dir, ATTEMPT_STREAMS[stream])
            elif self.session_dir is not None:
                path = os.path.join(self.session_dir, IDLE_STREAMS[stream])
            else:
                path = os.path.join(self.run_dir, NOSESSION_STREAMS[stream])
        self._append(path, rec)

    def record_event(self, rec: dict):
        """Campaign, operator and runner events (session file, or the daemon-run log)."""
        with self._lock:
            if self.session_dir is not None:
                path = os.path.join(self.session_dir, "session_events.jsonl")
            else:
                path = os.path.join(self.run_dir, "daemon_events.jsonl")
        self._append(path, rec)

    def record_raw_serial(self, data: bytes, t_mono_ns: int, t_wall_ns: int):
        with self._lock:
            paths = [os.path.join(self.run_dir, "serial_rx_raw.jsonl")]
            if self.session_dir is not None:
                paths.append(os.path.join(self.session_dir, "serial_rx_raw.jsonl"))
            aid = self.attempt_id
        rec = {"t_mono_ns": t_mono_ns, "t_wall_ns": t_wall_ns, "attempt_id": aid, "n": len(data),
               "b64": base64.b64encode(data).decode("ascii")}
        for p in paths:
            self._append(p, rec)

    def record_joint(self, sample) -> bool:
        """Joint samples are recorded at full rate during attempts only."""
        with self._lock:
            if self.attempt_dir is None:
                return False
            path = os.path.join(self.attempt_dir, "joint_states.csv")
        row = [sample.rx_mono_ns, sample.rx_wall_ns, sample.stamp_ns if sample.stamp_ns else "",
               1 if sample.valid else 0, sample.problem or "",
               "" if sample.order is None else " ".join(map(str, sample.order))]
        row += list(sample.position) if sample.position else [""] * 6
        row += list(sample.velocity) if sample.velocity else [""] * 6
        self._put(("csv", path, _csv_line(row)))
        return True

    # ------------------------------------------------------------------ internals
    def _append(self, path: str, rec: dict):
        try:
            line = dumps(rec) + "\n"
        except (TypeError, ValueError) as exc:
            line = dumps({"_unserializable": repr(rec)[:2000], "_error": str(exc)}) + "\n"
        self._put(("line", path, line))

    def _write_once(self, path: str, obj: dict):
        self._put(("once", path, json.dumps(obj, indent=2, ensure_ascii=False, allow_nan=False, default=str)))

    def _put(self, item):
        self._q.put(item)
        d = self._q.qsize()
        if d > self.max_queue:
            self.max_queue = d

    def _file(self, path: str):
        f = self._files.get(path)
        if f is None:
            f = open(path, "a", encoding="utf-8", newline="")
            self._files[path] = f
        return f

    def _close(self, predicate):
        for path in [p for p in self._files if predicate(p)]:
            f = self._files.pop(path)
            try:
                f.flush()
                os.fsync(f.fileno())
            except OSError as exc:
                self.errors.append(f"fsync {path}: {exc}")
            f.close()

    def _fsync_all(self):
        for path, f in list(self._files.items()):
            try:
                f.flush()
                os.fsync(f.fileno())
            except OSError as exc:
                self.errors.append(f"fsync {path}: {exc}")
        self.last_fsync_mono = time.monotonic_ns()

    def _run(self):
        next_fsync = time.monotonic() + self.fsync_interval_s
        while True:
            try:
                item = self._q.get(timeout=0.1)
            except queue.Empty:
                item = None
            if item is not None:
                self._handle(item)
            if time.monotonic() >= next_fsync:
                self._fsync_all()
                next_fsync = time.monotonic() + self.fsync_interval_s
            if self._stop and self._q.empty():
                self._close(lambda p: True)
                return

    def _handle(self, item):
        kind = item[0]
        try:
            if kind in ("line", "csv"):
                _, path, text = item
                new_csv = kind == "csv" and path not in self._files and not os.path.exists(path)
                f = self._file(path)
                if new_csv:
                    f.write(_csv_line(JOINT_HEADER))
                f.write(text)
                f.flush()
                self.records_written += 1
                self.bytes_written += len(text)
            elif kind in ("once", "once_text"):
                _, path, text = item
                with open(path, "x", encoding="utf-8", newline="\n") as f:   # never overwrite
                    f.write(text if text.endswith("\n") else text + "\n")
                    f.flush()
                    os.fsync(f.fileno())
            elif kind == "close_prefix":
                prefix = item[1]
                self._close(lambda p: p.startswith(prefix + os.sep))
            elif kind == "close_all":
                self._close(lambda p: True)
            elif kind == "barrier":
                for f in self._files.values():
                    f.flush()
                item[1].set()
        except (OSError, ValueError) as exc:
            if kind in ("line", "csv"):
                self.records_lost += 1
            self.errors.append(f"{kind} {item[1] if len(item) > 1 and isinstance(item[1], str) else ''}: {exc}")
            if kind == "barrier":
                item[1].set()


def _brief(meta: dict) -> dict:
    keep = ("trial_id", "trial_index", "attempt", "condition_id", "status", "reason", "t_wall_ns", "t_mono_ns")
    return {k: meta[k] for k in keep if k in meta}
