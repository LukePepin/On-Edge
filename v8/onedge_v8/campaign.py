"""Campaign configuration: validation, trial plan generation, preview and hashing.

A campaign config (JSON, v8/config/campaigns/) declares factor levels with a stated purpose,
the design, repetitions, ordering (with a recorded seed when randomized) and the trial
procedure. ``build_plan`` turns it into an explicit ordered trial list that is saved with
the session; execution follows the saved plan exactly.

Model expectations in the preview (update counts, expected crossing) are computed from the
firmware recurrence and historical loop-period summaries. They are labeled MODEL and are
not measurements.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
import os
import re
import struct

from . import CAMPAIGN_SCHEMA, SOFTWARE_NAME, SOFTWARE_VERSION

WORKLOADS = {
    "ECC": "ECC key generation (uECC_make_key, secp256r1)",
    "ZKP": "Two secp256r1 scalar multiplications (historical label 'ZKP'; a cost proxy, not proof verification)",
}
KINDS = ("research", "demonstration", "software_test")
PROCEDURES = ("bench", "robot")
ORDERINGS = ("randomized_complete_blocks", "randomized", "fixed_blocks", "explicit_sequence")
PROGRESSION = ("automatic", "operator_confirm_each_trial")
THRESHOLD = 30.0            # firmware EVICTION_THRESHOLD, strict "<"
INITIAL_TRUST = 100.0

# Historical host-observed bench report intervals (e2e_composition_results.csv, 10 intervals
# each; see Thesis study guide p.6). Used ONLY for rough MODEL expectations in the preview.
HISTORICAL_PERIOD_MS = {"ECC": 120.4, "ZKP": 232.1}
HISTORICAL_EXEC_MS = {"ECC": 111.54, "ZKP": 224.86}

TRIAL_DEFAULTS = {
    "baseline_ms": 2000,
    "injection_jitter_ms": 300,
    "post_recover_ms": 2500,
    "attack_resend_interval_ms": 0,
    "config_ack_timeout_ms": 1500,
    "config_attempts": 3,
    "attack_ack_timeout_ms": 1000,
    "recover_ack_timeout_ms": 1000,
    "inter_trial_ms": 1000,
}
MOTION_DEFAULTS = {
    "program": "pick_place_v1",
    "approach_s": 5.0,
    "settle_timeout_ms": 6000,
    "inject_after_moving_ms": 800,
    "moving_timeout_ms": 4000,
    "require_moving": True,
    "trajectory_timeout_s": 20.0,
    "resume_program": "operator_pendant",   # or "dashboard_play" (runner sends 'play' after re-arming)
    "program_wait_s": 60.0,
    "time_scale": 1.0,                      # < 1.0 only for software tests with the simulator
    "switch_controller_each_trial": True,   # historical wrapper re-activated passthrough after Play
}
TELEMETRY_DEFAULTS = {
    "device_stale_ms": 1000,
    "joint_stale_ms": 100,
    "standstill": {"v_still_rad_s": 0.01, "hold_ms": 250, "max_gap_ms": 40},
    "moving": {"v_move_rad_s": 0.05, "hold_ms": 100},
}


class ConfigError(ValueError):
    def __init__(self, problems):
        super().__init__("; ".join(problems))
        self.problems = list(problems)


# ---------------------------------------------------------------------------------------
# Deterministic PRNG (SplitMix64) so plans can be regenerated from the seed in any language.
# ---------------------------------------------------------------------------------------
_M64 = (1 << 64) - 1


class SplitMix64:
    def __init__(self, seed: int):
        self.state = seed & _M64

    def next_u64(self) -> int:
        self.state = (self.state + 0x9E3779B97F4A7C15) & _M64
        z = self.state
        z = ((z ^ (z >> 30)) * 0xBF58476D1CE4E5B9) & _M64
        z = ((z ^ (z >> 27)) * 0x94D049BB133111EB) & _M64
        return z ^ (z >> 31)

    def below(self, n: int) -> int:
        """Uniform integer in [0, n) without modulo bias."""
        limit = (1 << 64) - ((1 << 64) % n)
        while True:
            x = self.next_u64()
            if x < limit:
                return x % n

    def shuffle(self, items: list) -> None:
        for i in range(len(items) - 1, 0, -1):
            j = self.below(i + 1)
            items[i], items[j] = items[j], items[i]


# ---------------------------------------------------------------------------------------
# Firmware recurrence (MODEL): float32 emulation of the trust update
# ---------------------------------------------------------------------------------------

def f32(x: float) -> float:
    return struct.unpack("<f", struct.pack("<f", x))[0]


def firmware_trust_update(trust: float, alpha: float, obs: float) -> float:
    """trust = (alpha*obs) + ((1.0 - alpha)*trust), as compiled for the Nano.

    alpha, obs and trust are C floats; ``1.0`` is a double literal, so the second product and
    the sum are evaluated in double precision before the float assignment.
    """
    a = f32(alpha)
    return f32(f32(a * f32(obs)) + (1.0 - a) * f32(trust))


def attacked_updates_to_cross(alpha: float, start: float = INITIAL_TRUST, limit: int = 10000) -> int | None:
    """Smallest number of zero-observation updates for trust to become < 30 (strict)."""
    t = f32(start)
    for n in range(1, limit + 1):
        t = firmware_trust_update(t, alpha, 0.0)
        if t < THRESHOLD:
            return n
    return None


def model_expectation(workload: str, alpha: float, failure_ms: int) -> dict:
    """Rough expectation for the preview. MODEL, based on historical period summaries."""
    n = attacked_updates_to_cross(alpha)
    period = HISTORICAL_PERIOD_MS.get(workload)
    execm = HISTORICAL_EXEC_MS.get(workload)
    if failure_ms == 0:
        return {"label": "MODEL", "attacked_updates_to_cross": n, "expectation": "no injection (control)"}
    # Commands are processed only at loop boundaries. ATTACK waits w in [0, T) for the next
    # boundary; every cycle that STARTS while attack mode is set yields a zero observation
    # (RECOVER cannot be processed mid-workload). The n-th attacked cycle starts at w+(n-1)T
    # after sending, so crossing before RECOVER is processed requires F > w + (n-1)T:
    # impossible for F <= (n-1)T, certain for F > nT, phase-dependent in between.
    lo, hi = (n - 1) * period, n * period
    margin = 0.1 * period
    if failure_ms <= lo - margin:
        exp = "failure likely ends before crossing"
    elif failure_ms >= hi + margin:
        exp = "crossing likely before RECOVER is processed"
    else:
        exp = "boundary: outcome depends on command phase"
    return {"label": "MODEL", "attacked_updates_to_cross": n,
            "phase_dependent_failure_range_ms": [round(lo), round(hi)],
            "approx_crossing_after_send_ms": [round(lo + execm), round(hi + execm)],
            "basis": f"historical period {period} ms, exec {execm} ms (host-observed summaries); "
                     f"margin {margin:.0f} ms",
            "expectation": exp}


# ---------------------------------------------------------------------------------------
# Validation
# ---------------------------------------------------------------------------------------
_ID_RE = re.compile(r"^[a-z0-9][a-z0-9_-]{2,63}$")


def _num(v) -> bool:
    return isinstance(v, (int, float)) and not isinstance(v, bool) and math.isfinite(float(v))


def _int(v) -> bool:
    return isinstance(v, int) and not isinstance(v, bool)


def condition_id(workload: str, alpha: float, failure_ms: int) -> str:
    return f"{workload}-a{alpha:.2f}-f{int(failure_ms)}"


def normalize(config: dict) -> dict:
    """Return a copy with defaults filled in (validation should run on the result)."""
    c = copy.deepcopy(config)
    trial = dict(TRIAL_DEFAULTS)
    trial.update(c.get("trial") or {})
    if c.get("procedure") == "robot":
        motion = dict(MOTION_DEFAULTS)
        motion.update(trial.get("motion") or {})
        trial["motion"] = motion
    c["trial"] = trial
    tel = copy.deepcopy(TELEMETRY_DEFAULTS)
    for k, v in (c.get("telemetry") or {}).items():
        if isinstance(v, dict) and isinstance(tel.get(k), dict):
            tel[k].update(v)
        else:
            tel[k] = v
    c["telemetry"] = tel
    prog = {"mode": "automatic" if c.get("procedure") != "robot" else "operator_confirm_each_trial",
            "pause_on_operator_disconnect": True}
    prog.update(c.get("progression") or {})
    c["progression"] = prog
    return c


def validate(config: dict) -> list:
    """Return a list of problems (empty when the normalized config is valid)."""
    p = []
    if not isinstance(config, dict):
        return ["config must be a JSON object"]
    if config.get("schema") != CAMPAIGN_SCHEMA:
        p.append(f"schema must be {CAMPAIGN_SCHEMA!r}")
    if not isinstance(config.get("campaign_id"), str) or not _ID_RE.match(config.get("campaign_id", "")):
        p.append("campaign_id: 3-64 chars of a-z, 0-9, '-' or '_'")
    if not _int(config.get("config_version")) or config.get("config_version", 0) < 1:
        p.append("config_version: integer >= 1")
    for k in ("title", "purpose"):
        if not isinstance(config.get(k), str) or not config.get(k, "").strip():
            p.append(f"{k}: non-empty text required")
    if config.get("kind") not in KINDS:
        p.append(f"kind: one of {KINDS}")
    if config.get("procedure") not in PROCEDURES:
        p.append(f"procedure: one of {PROCEDURES}")
    status = config.get("status", "proposed")
    if status not in ("proposed", "approved"):
        p.append("status: 'proposed' or 'approved'")
    if status == "approved" and not (config.get("approved_by") and config.get("approved_on")):
        p.append("status 'approved' requires approved_by and approved_on")

    factors = config.get("factors")
    levels = {"workload": [], "alpha": [], "failure_ms": []}
    if not isinstance(factors, dict):
        p.append("factors: object with workload, alpha, failure_ms lists")
    else:
        for name in levels:
            items = factors.get(name)
            if not isinstance(items, list) or not items:
                p.append(f"factors.{name}: non-empty list")
                continue
            for i, it in enumerate(items):
                where = f"factors.{name}[{i}]"
                if not isinstance(it, dict) or "level" not in it:
                    p.append(f"{where}: object with 'level' and 'purpose'")
                    continue
                if not isinstance(it.get("purpose"), str) or not it["purpose"].strip():
                    p.append(f"{where}: 'purpose' text required")
                lv = it["level"]
                if name == "workload" and lv not in WORKLOADS:
                    p.append(f"{where}: workload must be one of {sorted(WORKLOADS)}")
                elif name == "alpha" and (not _num(lv) or not (0.0 < float(lv) <= 1.0)):
                    p.append(f"{where}: alpha must be a number in (0, 1]")
                elif name == "alpha" and _num(lv) and round(float(lv), 4) != float(lv):
                    p.append(f"{where}: alpha has more than 4 decimals (firmware reports 4)")
                elif name == "failure_ms" and (not _int(lv) or not (0 <= lv <= 60000)):
                    p.append(f"{where}: failure_ms must be an integer 0..60000 (0 = no-injection control)")
                levels[name].append(lv)
            if len(set(map(str, levels[name]))) != len(levels[name]):
                p.append(f"factors.{name}: duplicate levels")

    design = config.get("design") or {}
    dtype = design.get("type")
    if dtype not in ("full_factorial", "explicit"):
        p.append("design.type: 'full_factorial' or 'explicit'")
    if dtype == "explicit":
        conds = design.get("conditions")
        if not isinstance(conds, list) or not conds:
            p.append("design.conditions: non-empty list for an explicit design")
        else:
            seen = set()
            for i, c in enumerate(conds):
                where = f"design.conditions[{i}]"
                if not isinstance(c, dict):
                    p.append(f"{where}: object required")
                    continue
                for k in ("workload", "alpha", "failure_ms"):
                    if c.get(k) not in levels[k] and not (k == "alpha" and any(
                            _num(c.get(k)) and _num(x) and float(x) == float(c.get(k)) for x in levels[k])):
                        p.append(f"{where}.{k}: {c.get(k)!r} is not a declared factor level")
                if not isinstance(c.get("purpose"), str) or not c.get("purpose", "").strip():
                    p.append(f"{where}: 'purpose' text required")
                if "repetitions" in c and (not _int(c["repetitions"]) or not 1 <= c["repetitions"] <= 100):
                    p.append(f"{where}.repetitions: integer 1..100")
                key = (c.get("workload"), str(c.get("alpha")), c.get("failure_ms"))
                if key in seen:
                    p.append(f"{where}: duplicate condition")
                seen.add(key)
    reps = config.get("repetitions")
    if not _int(reps) or not 1 <= reps <= 100:
        p.append("repetitions: integer 1..100")

    ordering = config.get("ordering") or {}
    method = ordering.get("method")
    if method not in ORDERINGS:
        p.append(f"ordering.method: one of {ORDERINGS}")
    if method in ("randomized_complete_blocks", "randomized"):
        if not _int(ordering.get("seed")) or not 0 <= ordering["seed"] < 2 ** 63:
            p.append("ordering.seed: integer 0..2^63-1 required for randomized ordering")
    if method == "explicit_sequence":
        seq = ordering.get("sequence")
        if not isinstance(seq, list) or not seq or not all(isinstance(s, str) for s in seq):
            p.append("ordering.sequence: list of condition ids required for explicit_sequence")

    trial = config.get("trial") or {}
    for k, lo, hi in (("baseline_ms", 500, 60000), ("injection_jitter_ms", 0, 5000),
                      ("post_recover_ms", 0, 60000), ("config_ack_timeout_ms", 200, 10000),
                      ("config_attempts", 1, 5), ("attack_ack_timeout_ms", 100, 10000),
                      ("recover_ack_timeout_ms", 100, 10000), ("inter_trial_ms", 0, 600000)):
        v = trial.get(k)
        if not _int(v) or not lo <= v <= hi:
            p.append(f"trial.{k}: integer {lo}..{hi}")
    rs = trial.get("attack_resend_interval_ms")
    if not _int(rs) or not (rs == 0 or 20 <= rs <= 1000):
        p.append("trial.attack_resend_interval_ms: 0 (send once) or 20..1000")
    if config.get("procedure") == "robot":
        m = trial.get("motion") or {}
        if m.get("program") != "pick_place_v1":
            p.append("trial.motion.program: only 'pick_place_v1' is implemented")
        for k, lo, hi in (("inject_after_moving_ms", 0, 8000), ("moving_timeout_ms", 500, 20000),
                          ("settle_timeout_ms", 500, 30000)):
            if not _int(m.get(k)) or not lo <= m[k] <= hi:
                p.append(f"trial.motion.{k}: integer {lo}..{hi}")
        if not _num(m.get("approach_s")) or not 2.0 <= float(m["approach_s"]) <= 20.0:
            p.append("trial.motion.approach_s: 2..20 s")
        if not _num(m.get("trajectory_timeout_s")) or not 5.0 <= float(m["trajectory_timeout_s"]) <= 120.0:
            p.append("trial.motion.trajectory_timeout_s: 5..120 s")
        if not isinstance(m.get("require_moving"), bool):
            p.append("trial.motion.require_moving: true/false")
        if not isinstance(m.get("switch_controller_each_trial"), bool):
            p.append("trial.motion.switch_controller_each_trial: true/false")
        if m.get("resume_program") not in ("operator_pendant", "dashboard_play"):
            p.append("trial.motion.resume_program: 'operator_pendant' or 'dashboard_play'")
        if not _num(m.get("program_wait_s")) or not 5.0 <= float(m["program_wait_s"]) <= 600.0:
            p.append("trial.motion.program_wait_s: 5..600 s")
        ts = m.get("time_scale")
        if not _num(ts) or not 0.05 <= float(ts) <= 1.0:
            p.append("trial.motion.time_scale: 0.05..1.0")
        elif float(ts) < 1.0 and config.get("kind") != "software_test":
            p.append("trial.motion.time_scale < 1 is only allowed for kind 'software_test'")
        # The injection, failure window and post-recover observation should fall inside the
        # 10 s phase-2 sweep so that the arm is still commanded to move when the monitor reacts.
        if _int(m.get("inject_after_moving_ms")) and levels["failure_ms"]:
            longest = max([f for f in levels["failure_ms"] if _int(f)] or [0])
            span = m["inject_after_moving_ms"] + trial.get("injection_jitter_ms", 0) + longest
            usable = 8500 * (float(m["time_scale"]) if _num(m.get("time_scale")) else 1.0)
            if span > usable:
                p.append(f"trial: inject_after_moving + jitter + longest failure = {span} ms exceeds the "
                         f"{usable / 1000:.1f} s usable part of the sweep")
    tel = config.get("telemetry") or {}
    st = tel.get("standstill") or {}
    mv = tel.get("moving") or {}
    for name, v, lo, hi in (("standstill.v_still_rad_s", st.get("v_still_rad_s"), 1e-4, 0.5),
                            ("standstill.hold_ms", st.get("hold_ms"), 10, 5000),
                            ("standstill.max_gap_ms", st.get("max_gap_ms"), 2, 1000),
                            ("moving.v_move_rad_s", mv.get("v_move_rad_s"), 1e-3, 3.0),
                            ("moving.hold_ms", mv.get("hold_ms"), 10, 5000),
                            ("joint_stale_ms", tel.get("joint_stale_ms"), 5, 5000),
                            ("device_stale_ms", tel.get("device_stale_ms"), 100, 10000)):
        if not _num(v) or not lo <= float(v) <= hi:
            p.append(f"telemetry.{name}: number {lo}..{hi}")
    if _num(st.get("v_still_rad_s")) and _num(mv.get("v_move_rad_s")) and st["v_still_rad_s"] >= mv["v_move_rad_s"]:
        p.append("telemetry: v_still_rad_s must be below v_move_rad_s")
    prog = config.get("progression") or {}
    if prog.get("mode") not in PROGRESSION:
        p.append(f"progression.mode: one of {PROGRESSION}")
    if config.get("procedure") == "robot" and prog.get("mode") != "operator_confirm_each_trial":
        p.append("progression.mode: robot procedures require 'operator_confirm_each_trial'")
    if not isinstance(prog.get("pause_on_operator_disconnect"), bool):
        p.append("progression.pause_on_operator_disconnect: true/false")
    return p


def load_config(path: str) -> dict:
    with open(path, "r", encoding="utf-8") as f:
        raw = f.read()
    try:
        cfg = json.loads(raw)
    except ValueError as exc:
        raise ConfigError([f"{os.path.basename(path)}: invalid JSON: {exc}"])
    return cfg


def canonical_json(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)


def sha256_text(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


# ---------------------------------------------------------------------------------------
# Plan generation
# ---------------------------------------------------------------------------------------

def _conditions(cfg: dict) -> list:
    f = cfg["factors"]
    purpose = {("workload", it["level"]): it["purpose"] for it in f["workload"]}
    purpose.update({("alpha", float(it["level"])): it["purpose"] for it in f["alpha"]})
    purpose.update({("failure_ms", it["level"]): it["purpose"] for it in f["failure_ms"]})
    out = []
    if cfg["design"]["type"] == "full_factorial":
        for w in f["workload"]:
            for a in f["alpha"]:
                for fm in f["failure_ms"]:
                    out.append({"workload": w["level"], "alpha": float(a["level"]), "failure_ms": fm["level"],
                                "repetitions": cfg["repetitions"],
                                "purpose": " | ".join([purpose[("workload", w["level"])],
                                                       purpose[("alpha", float(a["level"]))],
                                                       purpose[("failure_ms", fm["level"])]])})
    else:
        for c in cfg["design"]["conditions"]:
            out.append({"workload": c["workload"], "alpha": float(c["alpha"]), "failure_ms": c["failure_ms"],
                        "repetitions": c.get("repetitions", cfg["repetitions"]), "purpose": c["purpose"]})
    for c in out:
        c["condition_id"] = condition_id(c["workload"], c["alpha"], c["failure_ms"])
        c["model"] = model_expectation(c["workload"], c["alpha"], c["failure_ms"])
    return out


def build_plan(config: dict) -> dict:
    """Validate and expand a config into the explicit, ordered trial plan."""
    cfg = normalize(config)
    problems = validate(cfg)
    if problems:
        raise ConfigError(problems)
    conds = _conditions(cfg)
    ordering = cfg["ordering"]
    method = ordering["method"]
    rng = SplitMix64(ordering.get("seed", 0))
    trials = []
    if method == "explicit_sequence":
        by_id = {c["condition_id"]: c for c in conds}
        unknown = [s for s in ordering["sequence"] if s not in by_id]
        if unknown:
            raise ConfigError([f"ordering.sequence: unknown condition ids {unknown}"])
        counts: dict = {}
        for cid in ordering["sequence"]:
            counts[cid] = counts.get(cid, 0) + 1
            trials.append((by_id[cid], counts[cid], None))
    elif method in ("randomized_complete_blocks", "fixed_blocks"):
        max_reps = max(c["repetitions"] for c in conds)
        for block in range(1, max_reps + 1):
            members = [c for c in conds if c["repetitions"] >= block]
            if method == "randomized_complete_blocks":
                rng.shuffle(members)
            trials.extend((c, block, block) for c in members)
    else:  # randomized
        pool = [(c, r, None) for c in conds for r in range(1, c["repetitions"] + 1)]
        rng.shuffle(pool)
        trials = pool
    jitter_max = cfg["trial"]["injection_jitter_ms"]
    jitter_rng = SplitMix64((ordering.get("seed", 0) ^ 0x5DEECE66D) & _M64)
    plan_trials = []
    for i, (c, rep, block) in enumerate(trials, start=1):
        plan_trials.append({
            "trial_index": i, "trial_id": f"T{i:03d}", "condition_id": c["condition_id"],
            "workload": c["workload"], "alpha": c["alpha"], "failure_ms": c["failure_ms"],
            "repetition": rep, "block": block,
            "injection_jitter_ms": jitter_rng.below(jitter_max + 1) if jitter_max > 0 else 0,
        })
    config_text = canonical_json(config)
    plan = {
        "schema": "onedge.v8.plan/1",
        "campaign_id": cfg["campaign_id"], "config_version": cfg["config_version"],
        "title": cfg["title"], "kind": cfg["kind"], "procedure": cfg["procedure"],
        "status": cfg.get("status", "proposed"),
        "config_sha256": sha256_text(config_text),
        "generated_by": f"{SOFTWARE_NAME} {SOFTWARE_VERSION}",
        "ordering": {"method": method, "seed": ordering.get("seed"),
                     "prng": "SplitMix64 + Fisher-Yates (see onedge_v8/campaign.py)"},
        "conditions": conds,
        "n_conditions": len(conds),
        "n_trials": len(plan_trials),
        "estimated_duration_s": round(estimate_duration_s(cfg, plan_trials)),
        "trials": plan_trials,
        "normalized_config": cfg,
    }
    plan["plan_sha256"] = sha256_text(canonical_json({k: v for k, v in plan.items() if k != "normalized_config"}))
    return plan


def estimate_duration_s(cfg: dict, trials: list) -> float:
    t = cfg["trial"]
    per = []
    for tr in trials:
        s = 0.5 + t["baseline_ms"] / 1000 + tr["injection_jitter_ms"] / 1000 + tr["failure_ms"] / 1000
        s += t["post_recover_ms"] / 1000 + t["inter_trial_ms"] / 1000
        if cfg["procedure"] == "robot":
            s += float(t["motion"]["approach_s"]) + 12.0 + 20.0   # approach, sweep, operator reset
        per.append(s)
    return sum(per)


def preview_text(plan: dict) -> str:
    lines = [f"{plan['title']}  [{plan['campaign_id']} v{plan['config_version']}, {plan['kind'].upper()}, "
             f"{plan['procedure']}, status {plan['status']}]",
             f"{plan['n_conditions']} conditions, {plan['n_trials']} trials, ordering {plan['ordering']['method']} "
             f"seed {plan['ordering']['seed']}, estimated {plan['estimated_duration_s'] / 60:.1f} min",
             f"plan_sha256 {plan['plan_sha256']}", "",
             f"{'condition':<22}{'reps':>5}  {'MODEL n':>7}  expectation"]
    for c in plan["conditions"]:
        m = c["model"]
        lines.append(f"{c['condition_id']:<22}{c['repetitions']:>5}  {str(m.get('attacked_updates_to_cross')):>7}  "
                     f"{m['expectation']}")
    return "\n".join(lines)


def list_campaigns(directory: str) -> list:
    """Load every *.json campaign config in a directory with its validation result."""
    out = []
    if not os.path.isdir(directory):
        return out
    for name in sorted(os.listdir(directory)):
        if not name.endswith(".json"):
            continue
        path = os.path.join(directory, name)
        entry = {"file": name}
        try:
            cfg = load_config(path)
            entry["campaign_id"] = cfg.get("campaign_id")
            entry["config_version"] = cfg.get("config_version")
            entry["title"] = cfg.get("title")
            entry["kind"] = cfg.get("kind")
            entry["procedure"] = cfg.get("procedure")
            entry["status"] = cfg.get("status", "proposed")
            plan = build_plan(cfg)
            entry.update({"valid": True, "n_trials": plan["n_trials"], "n_conditions": plan["n_conditions"],
                          "plan_sha256": plan["plan_sha256"]})
        except ConfigError as exc:
            entry.update({"valid": False, "problems": exc.problems})
        except (OSError, KeyError, TypeError) as exc:
            entry.update({"valid": False, "problems": [f"{type(exc).__name__}: {exc}"]})
        out.append(entry)
    return out
