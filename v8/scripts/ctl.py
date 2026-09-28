"""Command-line fallback for the acquisition daemon (use over SSH on the Pi if the dashboard is unavailable).

  python3 v8/scripts/ctl.py status
  python3 v8/scripts/ctl.py pause  --reason "..."
  python3 v8/scripts/ctl.py resume
  python3 v8/scripts/ctl.py abort  --reason "..."
  python3 v8/scripts/ctl.py decide retry|skip|continue|abort --reason "..."
Manual ATTACK/RECOVER and campaign start are intentionally dashboard-only.
"""
import argparse
import json
import sys
import urllib.error
import urllib.request


def call(base, method, path, body=None):
    data = json.dumps(body or {}).encode() if method == "POST" else None
    req = urllib.request.Request(f"{base}/api/{path}", data=data, method=method, headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=10) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        return {"error": json.loads(e.read().decode()).get("error", str(e)), "status": e.code}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("command", choices=["status", "pause", "resume", "abort", "decide"])
    ap.add_argument("decision", nargs="?")
    ap.add_argument("--reason", default="")
    ap.add_argument("--operator", default="cli")
    ap.add_argument("--url", default="http://127.0.0.1:8765")
    a = ap.parse_args()
    if a.command == "status":
        st = call(a.url, "GET", "status")
        if "error" in st:
            print(st); sys.exit(1)
        r, l, rob = st["runner"], st["link"], st["robot"]
        print(f"mode={st['mode']} runner={r['state']} ({r['state_reason']})")
        print(f"monitor connected={l['connected']} freshness={l['freshness']} protocol={l['protocol']} "
              f"missing={l['continuity'].get('missing_records')} resets={l['continuity'].get('resets')}")
        print(f"robot joints={rob['joint_freshness']} motion={rob['motion_state']} safety={rob['safety_mode']}")
        if r.get("current"):
            print("current:", json.dumps(r["current"]))
        if r.get("hold"):
            print("HOLD:", r["hold"]["reason"], "allowed:", r["hold"]["allowed"])
        return
    body = {"reason": a.reason, "operator": a.operator}
    path = {"pause": "campaign/pause", "resume": "campaign/resume", "abort": "campaign/abort",
            "decide": "campaign/decision"}[a.command]
    if a.command == "decide":
        body["decision"] = a.decision
    print(json.dumps(call(a.url, "POST", path, body), indent=2))


if __name__ == "__main__":
    main()
