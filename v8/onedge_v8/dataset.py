"""Reading recorded V8 data, recovering interrupted records, and file manifests.

Readers are tolerant: a truncated final JSONL line (process killed mid-write) or a malformed
line is reported as an issue and skipped; everything else is returned. Recovery writes NEW
files (attempt_recovered.json, session_recovered.json) and never modifies recorded data.
"""
from __future__ import annotations

import csv
import hashlib
import json
import os

from . import DATASET_SCHEMA


def read_jsonl(path: str) -> tuple:
    """Return (records, issues). Missing file -> ([], [])."""
    records, issues = [], []
    if not os.path.exists(path):
        return records, issues
    with open(path, "rb") as f:
        data = f.read()
    lines = data.split(b"\n")
    trailing_partial = bool(lines) and lines[-1] != b""
    for i, raw in enumerate(lines, start=1):
        if not raw.strip():
            continue
        try:
            records.append(json.loads(raw.decode("utf-8")))
        except (ValueError, UnicodeDecodeError) as exc:
            last = i == len(lines) and trailing_partial
            issues.append({"file": os.path.basename(path), "line": i,
                           "issue": "truncated_final_line" if last else "malformed_line", "detail": str(exc)[:200]})
    return records, issues


def read_json(path: str):
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def read_joint_csv(path: str) -> tuple:
    """Return (rows, issues); each row is a dict with typed values (None where empty)."""
    rows, issues = [], []
    if not os.path.exists(path):
        return rows, issues
    with open(path, "r", encoding="utf-8", newline="") as f:
        reader = csv.reader(f)
        try:
            header = next(reader)
        except StopIteration:
            return rows, issues
        for i, r in enumerate(reader, start=2):
            if len(r) != len(header):
                issues.append({"file": os.path.basename(path), "line": i, "issue": "truncated_or_malformed_row"})
                continue
            d = dict(zip(header, r))
            try:
                row = {"rx_mono_ns": int(d["rx_mono_ns"]), "rx_wall_ns": int(d["rx_wall_ns"]),
                       "stamp_ns": int(d["stamp_ns"]) if d["stamp_ns"] else None,
                       "valid": d["valid"] == "1", "problem": d["problem"] or None,
                       "order": [int(x) for x in d["msg_order"].split()] if d["msg_order"] else None}
                row["pos"] = [float(d[h]) if d[h] != "" else None for h in header if h.startswith("pos_")]
                row["vel"] = [float(d[h]) if d[h] != "" else None for h in header if h.startswith("vel_")]
            except (ValueError, KeyError) as exc:
                issues.append({"file": os.path.basename(path), "line": i, "issue": "bad_value", "detail": str(exc)})
                continue
            rows.append(row)
    return rows, issues


def joint_samples_from_rows(rows):
    """Rebuild JointSample objects for analysis."""
    from .telemetry import JointSample
    out = []
    for r in rows:
        pos = tuple(r["pos"]) if r["valid"] and None not in r["pos"] else None
        vel = tuple(r["vel"]) if r["valid"] and None not in r["vel"] else None
        out.append(JointSample(r["rx_mono_ns"], r["rx_wall_ns"], r["stamp_ns"], pos, vel,
                               tuple(r["order"]) if r["order"] else None, bool(r["valid"] and vel is not None),
                               r["problem"]))
    return out


def load_attempt(attempt_dir: str) -> dict:
    out = {"attempt_dir": attempt_dir, "attempt_id": os.path.basename(attempt_dir), "issues": []}
    out["start"] = read_json(os.path.join(attempt_dir, "attempt_start.json"))
    out["end"] = read_json(os.path.join(attempt_dir, "attempt_end.json"))
    out["recovered"] = read_json(os.path.join(attempt_dir, "attempt_recovered.json"))
    out["summary"] = read_json(os.path.join(attempt_dir, "summary.json"))
    for key, name in (("device", "device_msgs.jsonl"), ("tx", "serial_tx.jsonl"),
                      ("host", "host_events.jsonl"), ("robot", "robot_state.jsonl")):
        recs, issues = read_jsonl(os.path.join(attempt_dir, name))
        out[key] = recs
        out["issues"] += issues
    rows, issues = read_joint_csv(os.path.join(attempt_dir, "joint_states.csv"))
    out["joints"] = rows
    out["issues"] += issues
    out["status"] = attempt_status(out)
    return out


def attempt_status(a: dict) -> str:
    if a.get("end"):
        return a["end"].get("status", "unknown")
    if a.get("recovered"):
        return a["recovered"].get("status", "interrupted")
    return "unfinalized"


def list_sessions(data_root: str) -> list:
    base = os.path.join(data_root, "sessions")
    if not os.path.isdir(base):
        return []
    out = []
    for sid in sorted(os.listdir(base), reverse=True):
        sdir = os.path.join(base, sid)
        if not os.path.isdir(sdir):
            continue
        meta = read_json(os.path.join(sdir, "session.json")) or {}
        end = read_json(os.path.join(sdir, "session_end.json"))
        rec = read_json(os.path.join(sdir, "session_recovered.json"))
        adir = os.path.join(sdir, "attempts")
        attempts = sorted(os.listdir(adir)) if os.path.isdir(adir) else []
        out.append({"session_id": sid, "campaign_id": meta.get("campaign_id"), "kind": meta.get("kind"),
                    "procedure": meta.get("procedure"), "simulated": meta.get("simulated"),
                    "data_origin": meta.get("data_origin"), "title": meta.get("title"),
                    "started_wall": meta.get("started_wall"), "n_attempts": len(attempts),
                    "state": (end or {}).get("final_state") or ("recovered" if rec else "open_or_interrupted")})
    return out


def session_overview(session_dir: str) -> dict:
    meta = read_json(os.path.join(session_dir, "session.json")) or {}
    plan = read_json(os.path.join(session_dir, "plan.json"))
    end = read_json(os.path.join(session_dir, "session_end.json"))
    attempts = []
    adir = os.path.join(session_dir, "attempts")
    for aid in sorted(os.listdir(adir)) if os.path.isdir(adir) else []:
        d = os.path.join(adir, aid)
        start = read_json(os.path.join(d, "attempt_start.json")) or {}
        endm = read_json(os.path.join(d, "attempt_end.json"))
        recov = read_json(os.path.join(d, "attempt_recovered.json"))
        summ = read_json(os.path.join(d, "summary.json"))
        a = {"attempt_id": aid, "trial_id": start.get("trial_id"), "trial_index": start.get("trial_index"),
             "attempt": start.get("attempt"), "condition_id": start.get("condition_id"),
             "workload": start.get("workload"), "alpha": start.get("alpha"), "failure_ms": start.get("failure_ms"),
             "repetition": start.get("repetition"), "manual": start.get("manual", False)}
        a["status"] = attempt_status({"end": endm, "recovered": recov})
        a["reason"] = (endm or recov or {}).get("reason")
        a["departures"] = (endm or {}).get("departures", [])
        if summ:
            a["quality_warnings"] = summ.get("quality_warnings", [])
            a["outcome"] = summ.get("outcome")
            a["key_intervals"] = summ.get("key_intervals")
        attempts.append(a)
    return {"session_id": os.path.basename(session_dir), "meta": meta, "plan": plan, "end": end,
            "attempts": attempts,
            "recovered": read_json(os.path.join(session_dir, "session_recovered.json"))}


def recover_session(session_dir: str, active: bool = False) -> list:
    """Mark attempts (and the session) that never received their end record.

    ``active`` must be True when the session is still being recorded by a live process, in
    which case nothing is marked. Returns the list of attempt ids that were marked.
    """
    if active:
        return []
    marked = []
    adir = os.path.join(session_dir, "attempts")
    for aid in sorted(os.listdir(adir)) if os.path.isdir(adir) else []:
        d = os.path.join(adir, aid)
        if os.path.exists(os.path.join(d, "attempt_end.json")) or os.path.exists(
                os.path.join(d, "attempt_recovered.json")):
            continue
        counts = {}
        last_ns = None
        for name in ("device_msgs.jsonl", "host_events.jsonl", "serial_tx.jsonl"):
            recs, issues = read_jsonl(os.path.join(d, name))
            counts[name] = {"records": len(recs), "issues": len(issues)}
            for r in recs:
                t = r.get("rx_mono_ns") or r.get("t_mono_ns") or r.get("t_write_end_mono_ns")
                if isinstance(t, int):
                    last_ns = t if last_ns is None else max(last_ns, t)
        rows, _ = read_joint_csv(os.path.join(d, "joint_states.csv"))
        counts["joint_states.csv"] = {"rows": len(rows)}
        _write_new(os.path.join(d, "attempt_recovered.json"), {
            "schema": DATASET_SCHEMA, "status": "interrupted",
            "reason": "no attempt_end.json: the recording process stopped before the attempt was finalized; "
                      "recorded data are preserved up to the last flushed record",
            "last_record_mono_ns": last_ns, "file_counts": counts})
        marked.append(aid)
    if not os.path.exists(os.path.join(session_dir, "session_end.json")) and not os.path.exists(
            os.path.join(session_dir, "session_recovered.json")):
        _write_new(os.path.join(session_dir, "session_recovered.json"), {
            "schema": DATASET_SCHEMA, "final_state": "interrupted",
            "reason": "no session_end.json: the recording process stopped before the session closed",
            "interrupted_attempts": marked})
    return marked


def _write_new(path: str, obj: dict):
    with open(path, "x", encoding="utf-8") as f:
        json.dump(obj, f, indent=2)
        f.write("\n")


def sha256_file(path: str) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(directory: str) -> dict:
    files = []
    for root, _dirs, names in os.walk(directory):
        for n in sorted(names):
            if n == "manifest.json":
                continue
            p = os.path.join(root, n)
            files.append({"path": os.path.relpath(p, directory).replace(os.sep, "/"),
                          "bytes": os.path.getsize(p), "sha256": sha256_file(p)})
    files.sort(key=lambda x: x["path"])
    return {"schema": DATASET_SCHEMA, "files": files}


def safe_join(base: str, relpath: str) -> str:
    """Resolve relpath under base; raise ValueError on traversal outside base."""
    base_abs = os.path.abspath(base)
    p = os.path.abspath(os.path.join(base_abs, relpath.replace("/", os.sep)))
    if os.path.commonpath([base_abs, p]) != base_abs:
        raise ValueError("path escapes the data directory")
    return p
