"""Manual exclusions: separate, append-only, reversible, and always explained.

Exclusions are analyst decisions ("do not use this attempt in these plots/analyses because
..."). They are stored in <data_root>/annotations/exclusions.jsonl, never inside a session
directory, and never change recorded data. Each exclude/restore is a new event with a
required reason; the current state is derived by replaying all events in order.

Acquisition-quality warnings are different: they are computed automatically into each
attempt's summary.json and never exclude anything by themselves.
"""
from __future__ import annotations

import json
import os
import threading
import time
import uuid

from . import EXCLUSION_SCHEMA

ALL = "all"
SCOPES = (ALL, "comparison_plots", "timing_analysis", "motion_analysis")
MIN_REASON = 8


class ExclusionError(ValueError):
    pass


def _key(session_id: str, attempt_id: str) -> str:
    return f"{session_id}/{attempt_id}"


class ExclusionRegistry:
    def __init__(self, data_root: str):
        self.path = os.path.join(os.path.abspath(data_root), "annotations", "exclusions.jsonl")
        self._lock = threading.Lock()

    def _events(self) -> list:
        from .dataset import read_jsonl
        recs, _ = read_jsonl(self.path)
        return [r for r in recs if r.get("schema") == EXCLUSION_SCHEMA]

    def _append(self, event: dict):
        os.makedirs(os.path.dirname(self.path), exist_ok=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(json.dumps(event, ensure_ascii=False) + "\n")
            f.flush()
            os.fsync(f.fileno())

    def _new_event(self, action, session_id, attempt_id, scopes, reason, operator) -> dict:
        if not isinstance(reason, str) or len(reason.strip()) < MIN_REASON:
            raise ExclusionError(f"a reason of at least {MIN_REASON} characters is required")
        if not session_id or not attempt_id:
            raise ExclusionError("session_id and attempt_id are required")
        scopes = list(scopes or [ALL])
        bad = [s for s in scopes if s not in SCOPES]
        if bad:
            raise ExclusionError(f"unknown scope(s) {bad}; allowed {SCOPES}")
        return {"schema": EXCLUSION_SCHEMA, "event_id": uuid.uuid4().hex, "t_wall_ns": time.time_ns(),
                "t_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "action": action,
                "session_id": session_id, "attempt_id": attempt_id, "scopes": scopes,
                "reason": reason.strip(), "operator": (operator or "unspecified").strip()}

    def exclude(self, session_id, attempt_id, reason, operator=None, scopes=None) -> dict:
        with self._lock:
            ev = self._new_event("exclude", session_id, attempt_id, scopes, reason, operator)
            self._append(ev)
            return ev

    def restore(self, session_id, attempt_id, reason, operator=None, scopes=None) -> dict:
        with self._lock:
            current = self.state().get(_key(session_id, attempt_id), {})
            if not current:
                raise ExclusionError("attempt is not currently excluded")
            ev = self._new_event("restore", session_id, attempt_id, scopes or sorted(current), reason, operator)
            self._append(ev)
            return ev

    def state(self) -> dict:
        """{'session/attempt': {scope: exclude_event}} for currently active exclusions."""
        cur: dict = {}
        for ev in self._events():
            k = _key(ev["session_id"], ev["attempt_id"])
            for s in ev.get("scopes", [ALL]):
                if ev["action"] == "exclude":
                    cur.setdefault(k, {})[s] = ev
                elif ev["action"] == "restore":
                    cur.get(k, {}).pop(s, None)
            if k in cur and not cur[k]:
                del cur[k]
        return cur

    def is_excluded(self, session_id: str, attempt_id: str, scope: str = ALL) -> bool:
        active = self.state().get(_key(session_id, attempt_id), {})
        return ALL in active or scope in active

    def history(self, session_id: str | None = None, attempt_id: str | None = None) -> list:
        return [ev for ev in self._events()
                if (session_id is None or ev["session_id"] == session_id)
                and (attempt_id is None or ev["attempt_id"] == attempt_id)]

    def counts(self, session_id: str, attempt_ids, scope: str = ALL) -> dict:
        ids = list(attempt_ids)
        excluded = [a for a in ids if self.is_excluded(session_id, a, scope)]
        return {"scope": scope, "total": len(ids), "excluded": len(excluded), "included": len(ids) - len(excluded),
                "excluded_ids": excluded}
