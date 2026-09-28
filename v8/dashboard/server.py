"""On-Edge V8 dashboard server (Windows lunchbox; any OS with Python 3.10+). Standard library only.

  python v8/dashboard/server.py --pi http://127.0.0.1:8765          # live via SSH tunnel to the Pi
  python v8/dashboard/server.py --pi none                           # replay only (no Pi)

Serves the browser UI and:
  /api/live/...      proxy to the Pi acquisition daemon (controls + live stream)
  /api/replay/...    recorded sessions from local copies (hardware mirror, simulated data)
  /api/exclusions/.. manual, reversible exclusions (annotations/exclusions.jsonl)
  /api/sync/...      verified copy of CLOSED sessions from the Pi (never overwrites)
Replay requests can never reach the Pi's control endpoints.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
V8_DIR = os.path.dirname(HERE)
REPO_ROOT = os.path.dirname(V8_DIR)
sys.path.insert(0, V8_DIR)

from onedge_v8 import dataset, replay  # noqa: E402
from onedge_v8.exclusions import ExclusionError, ExclusionRegistry  # noqa: E402
from onedge_v8.httpbase import HttpError, Router, SSE, Server  # noqa: E402

CONTROL_PREFIXES = ("campaign/", "manual", "robot/", "note", "heartbeat")


class Dashboard:
    def __init__(self, pi_url: str | None, roots: dict, port: int, bind: str = "127.0.0.1"):
        self.pi = pi_url.rstrip("/") if pi_url else None
        self.roots = {k: os.path.abspath(v) for k, v in roots.items()}
        self.registries = {k: ExclusionRegistry(v) for k, v in self.roots.items()}
        self.server = Server(self._router(), bind, port, static_dir=os.path.join(HERE, "static"))

    # ------------------------------------------------------------------ proxy
    def _pi_request(self, method: str, path: str, body: dict | None = None, timeout: float = 10.0):
        if not self.pi:
            raise HttpError(503, "no acquisition daemon configured (replay-only dashboard)")
        data = json.dumps(body or {}).encode() if method == "POST" else None
        req = urllib.request.Request(f"{self.pi}/api/{path}", data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            try:
                msg = json.loads(e.read().decode("utf-8")).get("error", str(e))
            except ValueError:
                msg = str(e)
            raise HttpError(e.code, msg)
        except (urllib.error.URLError, OSError) as e:
            raise HttpError(502, f"acquisition daemon unreachable: {e}")

    def _pi_stream(self, handler, query):
        last = handler.headers.get("Last-Event-ID") or query.get("last_id")
        url = f"{self.pi}/api/stream" + (f"?last_id={urllib.parse.quote(str(last))}" if last else "")
        try:
            resp = urllib.request.urlopen(urllib.request.Request(url), timeout=15)
        except (urllib.error.URLError, OSError) as e:
            yield ("proxy_error", None, {"error": f"acquisition daemon unreachable: {e}"})
            return
        event, eid, data = "message", None, []
        try:
            while True:
                raw = resp.readline()
                if not raw:
                    break
                line = raw.decode("utf-8").rstrip("\n")
                if line.startswith(":"):
                    yield None
                elif line == "":
                    if data:
                        yield (event, eid, json.loads("\n".join(data)))
                    event, eid, data = "message", None, []
                elif line.startswith("event:"):
                    event = line[6:].strip()
                elif line.startswith("id:"):
                    eid = line[3:].strip()
                elif line.startswith("data:"):
                    data.append(line[5:].lstrip())
        except (OSError, ValueError) as e:
            yield ("proxy_error", None, {"error": f"stream interrupted: {e}"})
        finally:
            resp.close()

    # ------------------------------------------------------------------ sync
    def sync(self, session_id: str | None = None) -> dict:
        info = self._pi_request("GET", "info")
        root_key = "sim" if info.get("simulated") else "mirror"
        root = self.roots[root_key]
        listing = self._pi_request("GET", "sessions")["sessions"]
        report = {"root": root_key, "simulated_source": bool(info.get("simulated")), "sessions": []}
        for s in listing:
            sid = s["session_id"]
            if session_id and sid != session_id:
                continue
            entry = {"session_id": sid, "copied": 0, "unchanged": 0, "conflicts": [], "skipped": None}
            if s.get("state") in ("open_or_interrupted", None) and not session_id:
                entry["skipped"] = "session still open on the Pi (sync after it closes)"
                report["sessions"].append(entry)
                continue
            man = self._pi_request("GET", f"sessions/{urllib.parse.quote(sid)}/manifest")
            local = os.path.join(root, "sessions", sid)
            for f in man["files"]:
                dest = dataset.safe_join(local, f["path"])
                if os.path.exists(dest):
                    if dataset.sha256_file(dest) == f["sha256"]:
                        entry["unchanged"] += 1
                    else:
                        entry["conflicts"].append(f["path"])       # never overwrite a local file
                    continue
                os.makedirs(os.path.dirname(dest), exist_ok=True)
                url = f"{self.pi}/api/sessions/{urllib.parse.quote(sid)}/file?path={urllib.parse.quote(f['path'])}"
                tmp = dest + ".partial"
                h = hashlib.sha256()
                with urllib.request.urlopen(url, timeout=60) as r, open(tmp, "wb") as out:
                    while True:
                        chunk = r.read(1 << 16)
                        if not chunk:
                            break
                        h.update(chunk)
                        out.write(chunk)
                if h.hexdigest() != f["sha256"]:
                    os.remove(tmp)
                    entry["conflicts"].append(f"{f['path']} (hash mismatch during copy; file changed on the Pi?)")
                    continue
                os.replace(tmp, dest)
                entry["copied"] += 1
            report["sessions"].append(entry)
        return report

    # ------------------------------------------------------------------ routes
    def _root(self, key: str) -> str:
        if key not in self.roots:
            raise HttpError(404, f"unknown data root {key!r}")
        return self.roots[key]

    def _router(self) -> Router:
        r = Router()

        def wrap(fn):
            def inner(h, params, query, body):
                try:
                    return fn(params, query, body)
                except ExclusionError as e:
                    raise HttpError(400, str(e))
                except ValueError as e:
                    raise HttpError(400, str(e))
            return inner

        r.add("GET", "/api/local/info", wrap(lambda p, q, b: {
            "service": "onedge_v8 dashboard server", "pi": self.pi, "live_available": bool(self.pi),
            "roots": {k: {"path": v, "origin": "software_simulation" if k == "sim" else "hardware"}
                      for k, v in self.roots.items()}}))

        def live_get(h, params, query, body):
            path = params["path"]
            if path == "stream":
                return SSE(self._pi_stream(h, query))
            qs = ("?" + urllib.parse.urlencode(query)) if query else ""
            return self._pi_request("GET", path + qs)

        def live_post(h, params, query, body):
            if not params["path"].startswith(CONTROL_PREFIXES):
                raise HttpError(404, "unknown control endpoint")
            return self._pi_request("POST", params["path"], body)

        r.add("GET", r"/api/live/(?P<path>[A-Za-z0-9_./\-]+)", live_get)
        r.add("POST", r"/api/live/(?P<path>[A-Za-z0-9_./\-]+)", live_post)

        r.add("GET", r"/api/replay/(?P<root>[a-z]+)/sessions",
              wrap(lambda p, q, b: {"root": p["root"], "sessions": dataset.list_sessions(self._root(p["root"]))}))
        r.add("GET", r"/api/replay/(?P<root>[a-z]+)/sessions/(?P<sid>[A-Za-z0-9_.\-]+)",
              wrap(lambda p, q, b: replay.session_payload(self._root(p["root"]), p["sid"],
                                                           self.registries[p["root"]])))

        def attempt(p, q, b):
            base = dataset.safe_join(os.path.join(self._root(p["root"]), "sessions"), p["sid"])
            adir = dataset.safe_join(os.path.join(base, "attempts"), p["aid"])
            if not os.path.isdir(adir):
                raise HttpError(404, "attempt not found")
            return replay.attempt_payload(adir)
        r.add("GET", r"/api/replay/(?P<root>[a-z]+)/sessions/(?P<sid>[A-Za-z0-9_.\-]+)/attempts/(?P<aid>[A-Za-z0-9_.\-]+)",
              wrap(attempt))

        def excl_get(p, q, b):
            reg = self.registries[p["root"]] if p["root"] in self.registries else None
            if reg is None:
                raise HttpError(404, "unknown data root")
            return {"state": {k: sorted(v) for k, v in reg.state().items()},
                    "history": reg.history(q.get("session_id"), q.get("attempt_id"))}

        def excl_post(p, q, b):
            reg = self.registries.get(p["root"])
            if reg is None:
                raise HttpError(404, "unknown data root")
            action = b.get("action")
            args = (b.get("session_id"), b.get("attempt_id"), b.get("reason"), b.get("operator"), b.get("scopes"))
            if action == "exclude":
                return reg.exclude(*args)
            if action == "restore":
                return reg.restore(*args)
            raise HttpError(400, "action must be 'exclude' or 'restore'")
        r.add("GET", r"/api/exclusions/(?P<root>[a-z]+)", wrap(excl_get))
        r.add("POST", r"/api/exclusions/(?P<root>[a-z]+)", wrap(excl_post))
        r.add("POST", "/api/sync", wrap(lambda p, q, b: self.sync(b.get("session_id"))))
        return r


def main(argv=None):
    ap = argparse.ArgumentParser(description="On-Edge V8 dashboard server")
    ap.add_argument("--pi", default="http://127.0.0.1:8765",
                    help="acquisition daemon URL (through the SSH tunnel), or 'none' for replay only")
    ap.add_argument("--data-root", default=os.path.join(REPO_ROOT, "data", "v8"), help="local hardware-data mirror")
    ap.add_argument("--sim-root", default=os.path.join(REPO_ROOT, "data", "v8_sim"), help="local simulated data")
    ap.add_argument("--port", type=int, default=8080)
    ap.add_argument("--bind", default="127.0.0.1")
    args = ap.parse_args(argv)
    pi = None if args.pi.lower() == "none" else args.pi
    d = Dashboard(pi, {"mirror": args.data_root, "sim": args.sim_root}, args.port, args.bind)
    d.server.start()
    print(f"[dashboard] http://{args.bind}:{d.server.port}   live -> {pi or 'disabled (replay only)'}", flush=True)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        d.server.stop()


if __name__ == "__main__":
    main()
