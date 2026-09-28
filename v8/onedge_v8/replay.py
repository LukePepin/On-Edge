"""Normalize recorded attempts for display and comparison (read-only).

Display rules:
* All series use seconds relative to the attempt start on the host monotonic clock, i.e. when
  the host received/sent something. Device-clock values are included separately.
* Joint telemetry is reduced for display with a min/max envelope per bucket (peaks kept).
  Gaps longer than the declared limit become explicit gap segments; nothing is interpolated
  or filled with zeros.
* Every payload carries its origin labels (hardware / software simulation, research /
  demonstration) so the UI can label it.
"""
from __future__ import annotations

import os

from . import analysis, dataset


def _rel(ns, t0):
    return None if ns is None else (ns - t0) / 1e9


def attempt_payload(attempt_dir: str, max_joint_buckets: int = 1500) -> dict:
    att = dataset.load_attempt(attempt_dir)
    start = att.get("start") or {}
    t0 = start.get("t_mono_ns")
    if t0 is None:
        cands = [r.get("rx_mono_ns") for r in att["device"] if r.get("rx_mono_ns")]
        t0 = min(cands) if cands else 0
    summary = att.get("summary")
    computed = False
    if summary is None:
        summary = analysis.summarize(att)
        computed = True
    upd, events, gaps, bad = [], [], [], []
    dev_t0 = None
    for r in att["device"]:
        t = _rel(r.get("rx_mono_ns"), t0)
        for c in r.get("cont") or []:
            gaps.append({"t": t, **c})
        if r.get("status") != "ok":
            bad.append({"t": t, "status": r.get("status"), "raw": (r.get("raw") or "")[:160]})
            continue
        f = r.get("f") or {}
        if r.get("kind") in ("upd", "legacy_upd"):
            if dev_t0 is None and "t_dev_us" in r:
                dev_t0 = r["t_dev_us"]
            upd.append({"t": t, "t_dev_us": r.get("t_dev_us"), "epoch": r.get("epoch"),
                        "t_dev_s": (r["t_dev_us"] - dev_t0) / 1e6 if "t_dev_us" in r and dev_t0 is not None else None,
                        "trust": f.get("trust"), "obs": f.get("obs"), "exec_ms": f.get("exec_ms"),
                        "attack": f.get("attack"), "below": f.get("below"), "d12": f.get("d12"),
                        "cycle": f.get("cycle"), "seq": f.get("seq"), "pw_us": f.get("pw_us")})
        elif r.get("kind") in ("cfg", "cmd", "out", "err", "boot", "hello", "legacy_ready"):
            events.append({"t": t, "kind": r["kind"], "t_dev_us": r.get("t_dev_us"), "f": f})
    tx = [{"t": _rel(x.get("t_write_end_mono_ns") or x.get("t_request_mono_ns"), t0), "cmd": x.get("cmd"),
           "purpose": x.get("purpose"), "source": x.get("source"), "ok": x.get("ok"), "note": x.get("note")}
          for x in att["tx"]]
    host = [{"t": _rel(h.get("t_mono_ns"), t0), **{k: v for k, v in h.items() if k not in ("t_mono_ns", "t_wall_ns")}}
            for h in att["host"]]
    robot = [{"t": _rel(r.get("rx_mono_ns"), t0), "source": r.get("source"), "value": r.get("value"),
              "name": r.get("name")} for r in att["robot"]]
    joints = _joint_envelope(att["joints"], t0, start, max_joint_buckets)
    return {"attempt_id": att["attempt_id"], "status": att["status"], "start": start, "end": att.get("end"),
            "recovered": att.get("recovered"), "summary": summary, "summary_computed_on_read": computed,
            "series": {"updates": upd, "device_events": events, "continuity": gaps, "invalid_records": bad,
                       "commands": tx, "host_events": host, "robot_state": robot, "joints": joints},
            "file_issues": att["issues"]}


def _joint_envelope(rows, t0, start, max_buckets):
    tel = (start.get("telemetry_config") or {}).get("standstill") or {}
    max_gap_s = float(tel.get("max_gap_ms", 40)) / 1000.0
    pts = []
    invalid = 0
    for r in rows:
        stamp = r.get("stamp_ns")
        t_mono = (stamp - (r["rx_wall_ns"] - r["rx_mono_ns"])) if stamp else r["rx_mono_ns"]
        if not r["valid"] or any(v is None for v in r["vel"]):
            invalid += 1
            pts.append((_rel(t_mono, t0), None))
            continue
        pts.append((_rel(t_mono, t0), max(abs(v) for v in r["vel"])))
    pts.sort(key=lambda p: p[0])
    gaps = []
    for (ta, _), (tb, _) in zip(pts, pts[1:]):
        if tb - ta > max_gap_s:
            gaps.append({"from": ta, "to": tb, "ms": (tb - ta) * 1000})
    valid = [(t, v) for t, v in pts if v is not None]
    buckets = []
    if valid:
        span = max(1e-6, valid[-1][0] - valid[0][0])
        width = max(span / max_buckets, 0.0)
        cur = None
        for t, v in valid:
            k = int((t - valid[0][0]) / width) if width > 0 else 0
            if cur is None or cur["k"] != k:
                if cur:
                    buckets.append(cur)
                cur = {"k": k, "t": t, "lo": v, "hi": v, "n": 1}
            else:
                cur["lo"], cur["hi"], cur["n"] = min(cur["lo"], v), max(cur["hi"], v), cur["n"] + 1
        if cur:
            buckets.append(cur)
    return {"envelope": [{"t": b["t"], "lo": b["lo"], "hi": b["hi"], "n": b["n"]} for b in buckets],
            "gaps": gaps, "samples": len(rows), "invalid": invalid, "max_gap_limit_ms": max_gap_s * 1000,
            "decimated": len(buckets) < len(valid)}


def session_payload(data_root: str, session_id: str, registry=None) -> dict:
    sdir = dataset.safe_join(os.path.join(data_root, "sessions"), session_id)
    ov = dataset.session_overview(sdir)
    if registry is not None:
        state = registry.state()
        for a in ov["attempts"]:
            a["exclusions"] = sorted(state.get(f"{session_id}/{a['attempt_id']}", {}).keys())
        ids = [a["attempt_id"] for a in ov["attempts"]]
        ov["exclusion_counts"] = registry.counts(session_id, ids)
    return ov
