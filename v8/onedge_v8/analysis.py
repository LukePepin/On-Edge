"""Per-attempt derived summary: event extraction, same-clock intervals, outcome, quality.

Everything here is DERIVED from recorded files and can be regenerated offline
(``python -m onedge_v8.analysis <attempt_dir>``). Event definitions (definitions/1):

Device clock (device_us, one epoch; from firmware/trust_monitor_v8 records)
  D_CFG        the configuration record acknowledging this attempt's configuration
  D_ATTACK     first 'cmd' ATTACK record with prev=0 after D_CFG   (device processed ATTACK)
  D_CROSS      first 'upd' record with below=1 after D_CFG         (trust update < 30)
  D_OUT_LOW    first 'out' record with level=0 after D_CFG         (firmware commanded D12 low)
  D_RECOVER    first 'cmd' RECOVER record with prev=1 after D_ATTACK
Host clock (host_mono_ns, the Pi)
  H_CFG_SENT / H_ATTACK_SENT / H_RECOVER_SENT   serial write returned (bytes handed to the OS)
  H_RX_CROSS / H_RX_OUT_LOW                      host receipt of the D_CROSS / D_OUT_LOW record
  H_RX_SAFEGUARD   host receipt of the controller's safety-mode report SAFEGUARD_STOP
  H_MOVING         start of the moving-criterion window before injection (joint stamps)
  H_STANDSTILL     start of the first standstill-criterion window after D_OUT_LOW (joint stamps)
Not observable by this software: the electrical D12 transition (needs an oscilloscope or a
separately wired input) and physical standstill beyond the declared telemetry criterion.
"""
from __future__ import annotations

import os
import statistics
import sys

from . import ANALYSIS_DEFINITIONS, SOFTWARE_NAME, SOFTWARE_VERSION
from .campaign import attacked_updates_to_cross
from .clocks import DEVICE_US, HOST_MONO_NS, ClockFit, Stamp, aligned_interval_ms, interval_ms
from .dataset import joint_samples_from_rows, load_attempt, read_jsonl
from .telemetry import MotionCriteria, confirm_moving, find_standstill

SAFEGUARD_STOP_NAMES = {"SAFEGUARD_STOP", "AUTOMATIC_MODE_SAFEGUARD_STOP"}
FAULT_SAFETY_NAMES = {"PROTECTIVE_STOP", "SYSTEM_EMERGENCY_STOP", "ROBOT_EMERGENCY_STOP", "VIOLATION", "FAULT"}


def _stats(values) -> dict | None:
    v = [x for x in values if x is not None]
    if not v:
        return None
    s = sorted(v)
    return {"n": len(s), "mean": statistics.fmean(s), "median": statistics.median(s),
            "min": s[0], "max": s[-1], "stdev": statistics.stdev(s) if len(s) > 1 else 0.0,
            "p95": s[min(len(s) - 1, int(round(0.95 * (len(s) - 1))))]}


def _first(items, pred):
    return next((x for x in items if pred(x)), None)


def _dstamp(rec) -> Stamp:
    return Stamp(DEVICE_US, rec["t_dev_us"], rec.get("epoch", 0))


def _hstamp(ns) -> Stamp:
    return Stamp(HOST_MONO_NS, int(ns))


CONTEXT_WINDOW_US = 60_000_000      # neighbouring records used for the clock rate: +-60 s (device clock)
CONTEXT_NEIGHBOURS = 3               # attempts on each side (by directory order) plus the session idle file


def summarize(att: dict, context: list | None = None) -> dict:
    """context: device records from the same session (other attempts, idle periods), used only for
    the device clock rate when this attempt is too short to estimate it."""
    start = att.get("start") or {}
    trial_cfg = start.get("trial_config") or {}
    tel_cfg = start.get("telemetry_config") or {}
    procedure = start.get("procedure", "bench")
    failure_ms = start.get("failure_ms")
    alpha = start.get("alpha")
    warnings: list = []
    notes: list = []

    dev_all = att.get("device") or []
    dev_ok = [m for m in dev_all if m.get("status") == "ok" and m.get("proto") == "v8"]
    legacy = [m for m in dev_all if m.get("proto") == "legacy"]
    bad = [m for m in dev_all if m.get("status") != "ok"]
    if bad:
        warnings.append({"code": "malformed_records", "count": len(bad),
                         "statuses": sorted({m.get("status") for m in bad})})
    if legacy and not dev_ok:
        notes.append("legacy firmware protocol: no device timestamps; device-clock intervals unavailable")

    # ---- device events -------------------------------------------------------------
    cfgs = [m for m in dev_ok if m["kind"] == "cfg"]
    tx = att.get("tx") or []
    tx_cfg = [t for t in tx if t.get("purpose") == "trial_config" and t.get("ok")]
    tx_attack = _first(tx, lambda t: t.get("purpose") == "trial_attack" and t.get("ok"))
    tx_recover = _first(tx, lambda t: t.get("purpose") == "trial_recover" and t.get("ok"))
    manual_tx = [t for t in tx if t.get("source") == "operator"]
    if manual_tx:
        warnings.append({"code": "operator_commands_during_attempt", "count": len(manual_tx),
                         "commands": [t.get("cmd") for t in manual_tx]})

    d_cfg = None
    if cfgs:
        if tx_attack:
            before = [m for m in cfgs if m["rx_mono_ns"] <= tx_attack["t_write_end_mono_ns"]]
            d_cfg = before[-1] if before else cfgs[-1]
        else:
            d_cfg = cfgs[-1]
    epoch = d_cfg.get("epoch", 0) if d_cfg else (dev_ok[0].get("epoch", 0) if dev_ok else 0)
    same = [m for m in dev_ok if m.get("epoch", 0) == epoch]
    after_cfg = [m for m in same if d_cfg is None or m["t_dev_us"] >= d_cfg["t_dev_us"]]
    d_attack = _first(after_cfg, lambda m: m["kind"] == "cmd" and m["f"]["cmd"] == "ATTACK" and m["f"]["prev"] == 0)
    d_cross = _first(after_cfg, lambda m: m["kind"] == "upd" and m["f"]["below"] == 1)
    d_out = _first(after_cfg, lambda m: m["kind"] == "out" and m["f"]["level"] == 0)
    d_recover = None
    if d_attack:
        d_recover = _first(after_cfg, lambda m: m["kind"] == "cmd" and m["f"]["cmd"] == "RECOVER"
                           and m["f"]["prev"] == 1 and m["t_dev_us"] > d_attack["t_dev_us"])
    resets = [c for m in dev_all for c in (m.get("cont") or []) if c.get("kind") == "reset"]
    if resets:
        warnings.append({"code": "device_reset_during_attempt", "count": len(resets), "detail": resets[:3]})
    gaps = [c for m in dev_all for c in (m.get("cont") or []) if c.get("kind") in ("gap", "legacy_cycle_gap")]
    missing = sum(c.get("missing", 0) for c in gaps)
    critical_gap = False
    if gaps:
        lo = d_attack["t_dev_us"] if d_attack else None
        hi = d_cross["t_dev_us"] if d_cross else None
        for m in dev_all:
            if any(c.get("kind") == "gap" for c in (m.get("cont") or [])) and lo is not None and "t_dev_us" in m:
                if m["t_dev_us"] >= lo and (hi is None or m["t_dev_us"] <= hi):
                    critical_gap = True
        warnings.append({"code": "sequence_gap", "gap_events": len(gaps), "missing_records": missing,
                         "in_attack_to_crossing_window": critical_gap})

    # ---- update statistics -----------------------------------------------------------
    upds = [m for m in after_cfg if m["kind"] == "upd"]
    periods = []
    for a, b in zip(upds, upds[1:]):
        if b["f"]["cycle"] == a["f"]["cycle"] + 1:
            periods.append((b["t0_dev_us"] - a["t0_dev_us"]) / 1000.0)
    exec_ms = [m["f"]["exec_ms"] for m in upds]
    pw_us = [m["f"].get("pw_us") for m in upds if isinstance(m["f"].get("pw_us"), int) and m["f"]["pw_us"] >= 0]
    penalty = [m for m in upds if m["f"]["attack"] == 0 and m["f"]["obs"] < 100.0]
    if penalty:
        warnings.append({"code": "execution_time_penalty_observed", "count": len(penalty),
                         "note": "obs < 100 without ATTACK: the firmware's execution-time penalty branch was active"})

    # ---- host events -----------------------------------------------------------------
    rx_cross = d_cross["rx_mono_ns"] if d_cross else None
    rx_out = d_out["rx_mono_ns"] if d_out else None
    h_attack = tx_attack["t_write_end_mono_ns"] if tx_attack else None
    h_recover = tx_recover["t_write_end_mono_ns"] if tx_recover else None
    robot = att.get("robot") or []
    h_safeguard = None
    if h_attack is not None:
        rec = _first(robot, lambda r: r.get("source") == "safety_mode" and r.get("name") in SAFEGUARD_STOP_NAMES
                     and r["rx_mono_ns"] >= h_attack)
        h_safeguard = rec["rx_mono_ns"] if rec else None
    faults = [r for r in robot if r.get("source") == "safety_mode" and r.get("name") in FAULT_SAFETY_NAMES]
    if faults:
        warnings.append({"code": "robot_fault_safety_mode", "modes": sorted({r["name"] for r in faults})})

    if failure_ms and failure_ms > 0:
        if tx_attack is None:
            warnings.append({"code": "attack_not_sent"})
        elif d_attack is None and dev_ok:
            warnings.append({"code": "attack_not_acknowledged",
                             "note": "no device record shows ATTACK processing"})
        if tx_recover is None:
            warnings.append({"code": "recover_not_sent"})
        elif d_recover is None and dev_ok:
            warnings.append({"code": "recover_not_acknowledged"})

    # ---- clock relationship ------------------------------------------------------------
    own_pairs = [(m["t_dev_us"], m["rx_mono_ns"]) for m in same]
    fit = ClockFit.estimate(own_pairs, epoch=epoch)
    if fit is not None and not fit.slope_estimated and context and same:
        lo, hi = same[0]["t_dev_us"] - CONTEXT_WINDOW_US, same[-1]["t_dev_us"] + CONTEXT_WINDOW_US
        ctx_pairs = {(m["t_dev_us"], m["rx_mono_ns"]) for m in context
                     if m.get("status") == "ok" and m.get("epoch", 0) == epoch and m.get("t_dev_us") is not None
                     and m.get("rx_mono_ns") is not None and lo <= m["t_dev_us"] <= hi}
        ctx = ClockFit.estimate(ctx_pairs | set(own_pairs), epoch=epoch)
        if ctx is not None and ctx.slope_estimated:
            fit = ClockFit.estimate(own_pairs, epoch=epoch, slope=ctx.slope_ns_per_us,
                                    slope_note=f"session records within +-60 s (n={ctx.n_points}, "
                                               f"span {ctx.span_s:.0f} s)")
    if fit is not None and not fit.slope_estimated:
        # informational: over a few seconds a nominal slope differs from the true drift by
        # ~ppm x span (tens of microseconds); cross-clock ranges already carry larger bounds
        notes.append(f"clock fit used the nominal slope ({fit.note})")
    elif fit is not None and fit.note:
        notes.append(f"clock fit: {fit.note}")
    # host ns per device us, only when estimated from this attempt's data
    rate = fit.slope_ns_per_us / 1000.0 if fit is not None and fit.slope_estimated else None

    # ---- intervals -------------------------------------------------------------------
    iv: dict = {}

    def dev_iv(name, a, b, definition):
        if a and b:
            v = interval_ms(_dstamp(a), _dstamp(b))
            iv[name] = {"clock": DEVICE_US, "value_ms": v, "definition": definition,
                        "value_ms_rate_corrected": v * rate if rate is not None else None}

    def host_iv(name, a, b, definition):
        if a is not None and b is not None:
            iv[name] = {"clock": HOST_MONO_NS, "value_ms": interval_ms(_hstamp(a), _hstamp(b)),
                        "definition": definition}

    def aligned_iv(name, host_ns, dev_rec, host_first, definition):
        if fit is None or host_ns is None or dev_rec is None:
            return
        if host_first:
            r = aligned_interval_ms(_hstamp(host_ns), _dstamp(dev_rec), fit)
        else:
            r = aligned_interval_ms(_dstamp(dev_rec), _hstamp(host_ns), fit)
        iv[name] = {"clock": "aligned device_us->host_mono_ns", **r.to_dict(), "definition": definition}

    dev_iv("device_attack_to_cross", d_attack, d_cross, "D_CROSS - D_ATTACK")
    dev_iv("device_attack_to_out_low", d_attack, d_out, "D_OUT_LOW - D_ATTACK")
    dev_iv("device_cross_to_out_low", d_cross, d_out, "D_OUT_LOW - D_CROSS (same cycle; ordering check)")
    dev_iv("device_failure_window", d_attack, d_recover, "D_RECOVER - D_ATTACK (device-side attack mode)")
    host_iv("host_attack_sent_to_rx_cross", h_attack, rx_cross, "H_RX_CROSS - H_ATTACK_SENT")
    host_iv("host_attack_sent_to_rx_out_low", h_attack, rx_out, "H_RX_OUT_LOW - H_ATTACK_SENT")
    host_iv("host_failure_window", h_attack, h_recover, "H_RECOVER_SENT - H_ATTACK_SENT")
    host_iv("host_attack_sent_to_rx_safeguard", h_attack, h_safeguard, "H_RX_SAFEGUARD - H_ATTACK_SENT")
    aligned_iv("aligned_attack_sent_to_device_processed", h_attack, d_attack, True, "D_ATTACK - H_ATTACK_SENT")
    aligned_iv("aligned_out_low_to_rx_safeguard", h_safeguard, d_out, False, "H_RX_SAFEGUARD - D_OUT_LOW")

    n_attacked = None
    if d_cross and d_attack:
        first_att = _first(upds, lambda m: m["f"]["attack"] == 1 and m["t_dev_us"] >= d_attack["t_dev_us"])
        if first_att and d_cross["f"]["cycle"] >= first_att["f"]["cycle"]:
            n_attacked = d_cross["f"]["cycle"] - first_att["f"]["cycle"] + 1

    # ---- motion (robot procedure) ------------------------------------------------------
    motion = {"applicable": procedure == "robot"}
    crit = MotionCriteria.from_dict(tel_cfg)
    samples = joint_samples_from_rows(att.get("joints") or [])
    if samples:
        valid = [s for s in samples if s.valid]
        times = sorted(s.t_mono_ns for s in valid)
        dts = [(b - a) / 1e6 for a, b in zip(times, times[1:])]
        motion["telemetry"] = {"samples": len(samples), "valid": len(valid), "invalid": len(samples) - len(valid),
                               "rate_hz": (len(times) - 1) / ((times[-1] - times[0]) / 1e9)
                               if len(times) > 1 and times[-1] > times[0] else None,
                               "max_gap_ms": max(dts) if dts else None,
                               "gaps_over_limit": sum(1 for d in dts if d > crit.max_gap_ms)}
        if motion["telemetry"]["invalid"]:
            warnings.append({"code": "joint_invalid_samples", "count": motion["telemetry"]["invalid"]})
        if motion["telemetry"]["gaps_over_limit"]:
            warnings.append({"code": "joint_telemetry_gap", "count": motion["telemetry"]["gaps_over_limit"],
                             "max_gap_ms": motion["telemetry"]["max_gap_ms"], "limit_ms": crit.max_gap_ms})
    elif procedure == "robot":
        warnings.append({"code": "joint_telemetry_missing"})
    if procedure == "robot":
        host = att.get("host") or []
        goal = _first(host, lambda e: e.get("event") == "trajectory" and e.get("phase") == 2
                      and e.get("status") == "accepted")
        if samples and goal and h_attack is not None:
            mv = confirm_moving(samples, goal["t_mono_ns"], crit, before_ns=h_attack)
            motion["moving_before_injection"] = mv.to_dict()
            if mv.status != "reached":
                warnings.append({"code": "not_confirmed_moving_at_injection", "status": mv.status})
        if samples and d_out is not None and fit is not None:
            after = int(fit.dev_to_host_ns(d_out["t_dev_us"]) - fit.d_min_bound_ms * 1e6)
            end_ns = max(s.t_mono_ns for s in samples)
            ss = find_standstill(samples, after, crit, before_ns=end_ns)
            motion["standstill_after_out_low"] = ss.to_dict()
            if ss.status == "reached":
                host_iv("host_attack_sent_to_standstill", h_attack, ss.t_mono_ns,
                        "H_STANDSTILL - H_ATTACK_SENT (standstill criterion on joint stamps)")
                aligned_iv("aligned_out_low_to_standstill", ss.t_mono_ns, d_out, False,
                           "H_STANDSTILL - D_OUT_LOW (criterion window start; sample-period resolution)")
                if ss.preceding_gap_ms and ss.preceding_gap_ms > crit.max_gap_ms:
                    notes.append("standstill window began after a telemetry gap: onset is an upper bound")
        motion["criteria"] = crit.to_dict()
        motion["controller_safeguard_reported"] = (h_safeguard is not None) if robot else None

    # ---- outcome ----------------------------------------------------------------------
    complete = not gaps and not bad and not resets
    if not failure_ms:
        injection = "not_planned"
    elif tx_attack is None:
        injection = "not_sent"
    elif d_attack is not None:
        injection = "processed"
    elif dev_ok:
        injection = "not_observed"
    else:
        injection = "unknown_no_device_timestamps"
    if d_cross is not None:
        crossing = "crossed_while_attack_active" if d_cross["f"]["attack"] == 1 else "crossed_without_attack"
    elif legacy:
        crossing = "undetermined_legacy_protocol"
    elif complete and upds:
        crossing = "no_crossing_in_complete_record"
    else:
        crossing = "no_crossing_observed_record_incomplete"
    rel = None
    if d_cross and d_recover:
        rel = "before_recover_processed" if d_cross["t_dev_us"] < d_recover["t_dev_us"] else "after_recover_processed"
    elif d_cross and d_attack and not d_recover:
        rel = "no_recover_processed_before_crossing"
    rx_after_recover_sent = (rx_cross is not None and h_recover is not None and rx_cross > h_recover)
    if rx_after_recover_sent:
        notes.append("the crossing report was received after RECOVER was sent (host clock)")
    model = None
    if alpha:
        exp = attacked_updates_to_cross(alpha)
        model = {"label": "MODEL", "attacked_updates_to_cross_expected": exp, "observed": n_attacked,
                 "agrees": (n_attacked == exp) if n_attacked is not None else None,
                 "assumption": "trust 100 at ATTACK, zero observations, no penalty; float32 recurrence"}

    outcome = {"injection": injection, "crossing": crossing, "crossing_relative_to_recover": rel,
               "out_low_commanded": d_out is not None,
               "rx_cross_after_host_recover_sent": rx_after_recover_sent}

    key = {k: v for k, v in iv.items()}
    return {
        "definitions": ANALYSIS_DEFINITIONS,
        "attempt_id": att.get("attempt_id"), "trial_id": start.get("trial_id"),
        "condition_id": start.get("condition_id"), "workload": start.get("workload"), "alpha": alpha,
        "failure_ms": failure_ms, "procedure": procedure, "status": att.get("status"),
        "device_protocol": "v8" if dev_ok else ("legacy" if legacy else None),
        "device_epoch": epoch,
        "events": {
            "D_CFG": _ev(d_cfg), "D_ATTACK": _ev(d_attack), "D_CROSS": _ev(d_cross), "D_OUT_LOW": _ev(d_out),
            "D_RECOVER": _ev(d_recover),
            "H_ATTACK_SENT": h_attack, "H_RECOVER_SENT": h_recover, "H_RX_CROSS": rx_cross,
            "H_RX_OUT_LOW": rx_out, "H_RX_SAFEGUARD": h_safeguard,
            "H_CFG_SENT": tx_cfg[-1]["t_write_end_mono_ns"] if tx_cfg else None,
        },
        "attacked_updates_to_cross": n_attacked,
        "model_check": model,
        "key_intervals": key,
        "updates": {"count": len(upds), "loop_period_ms": _stats(periods), "exec_ms": _stats(exec_ms),
                    "report_write_us": _stats(pw_us), "min_trust": min((m["f"]["trust"] for m in upds), default=None),
                    "penalty_updates": len(penalty)},
        "records": {"device_total": len(dev_all), "device_ok_v8": len(dev_ok), "legacy": len(legacy),
                    "not_ok": len(bad), "missing_by_sequence": missing, "complete": complete},
        "clock_fit": fit.to_dict() if fit else None,
        "device_clock_rate": {"host_ns_per_device_us": fit.slope_ns_per_us if rate is not None else None,
                              "ppm": fit.ppm if rate is not None else None,
                              "note": "device_us intervals x (host_ns_per_device_us / 1000) = host-clock duration; "
                                      "value_ms_rate_corrected applies this per attempt"},
        "motion": motion,
        "outcome": outcome,
        "quality_warnings": warnings,
        "notes": notes,
        "not_measured_by_this_software": ["electrical D12 transition (requires oscilloscope or wired input)",
                                          "physical standstill beyond the declared telemetry criterion"],
        "file_issues": att.get("issues", []),
    }


def _ev(m):
    if not m:
        return None
    out = {"t_dev_us": m["t_dev_us"], "epoch": m.get("epoch", 0), "rx_mono_ns": m["rx_mono_ns"],
           "seq": m["f"].get("seq")}
    for k in ("cycle", "trust", "attack", "cmd", "level"):
        if k in m["f"]:
            out[k] = m["f"][k]
    return out


def session_context(attempt_dir: str) -> list:
    """Device records near an attempt in the same session: the session idle file and up to
    CONTEXT_NEIGHBOURS attempts on each side. Empty outside a session layout."""
    parent = os.path.dirname(attempt_dir)
    if os.path.basename(parent) != "attempts":
        return []
    session = os.path.dirname(parent)
    names = sorted(n for n in os.listdir(parent) if os.path.isdir(os.path.join(parent, n)))
    me = os.path.basename(attempt_dir)
    i = names.index(me) if me in names else 0
    files = [os.path.join(session, "device_msgs_idle.jsonl")]
    files += [os.path.join(parent, n, "device_msgs.jsonl")
              for n in names[max(0, i - CONTEXT_NEIGHBOURS): i + CONTEXT_NEIGHBOURS + 1] if n != me]
    recs = []
    for f in files:
        recs += read_jsonl(f)[0]
    return recs


def summarize_attempt_dir(attempt_dir: str) -> dict:
    return summarize(load_attempt(attempt_dir), context=session_context(attempt_dir))


def regenerate_summary(attempt_dir: str) -> str:
    """Rewrite summary.json with the current analysis; the previous file is kept, renamed."""
    import json
    import time
    path = os.path.join(attempt_dir, "summary.json")
    summary = summarize_attempt_dir(attempt_dir)
    summary["generated_by"] = f"{SOFTWARE_NAME} {SOFTWARE_VERSION}"
    if os.path.exists(path):
        with open(path, "r", encoding="utf-8") as f:
            summary["supersedes"] = json.load(f).get("generated_by")
        os.replace(path, os.path.join(attempt_dir, f"summary.superseded_{time.strftime('%Y%m%dT%H%M%S')}.json"))
    tmp = path + ".tmp"
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2, default=str)
    os.replace(tmp, path)
    return path


def main(argv=None):
    import json
    argv = list(argv or sys.argv[1:])
    write = "--write" in argv
    argv = [a for a in argv if a != "--write"]
    if not argv:
        print("usage: python -m onedge_v8.analysis [--write] <attempt_dir> [...]\n"
              "  --write  regenerate summary.json in place (previous file kept as summary.superseded_*.json)")
        return 2
    for d in argv:
        if write:
            print(regenerate_summary(os.path.abspath(d)))
        else:
            print(json.dumps(summarize_attempt_dir(os.path.abspath(d)), indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
