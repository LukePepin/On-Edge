"""Minimal JSON + Server-Sent Events HTTP plumbing on the standard library."""
from __future__ import annotations

import json
import mimetypes
import os
import re
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse


STATIC_TYPES = {".html": "text/html; charset=utf-8", ".js": "text/javascript; charset=utf-8",
                ".mjs": "text/javascript; charset=utf-8", ".css": "text/css; charset=utf-8",
                ".json": "application/json", ".jsonl": "application/x-ndjson", ".csv": "text/csv; charset=utf-8",
                ".svg": "image/svg+xml", ".png": "image/png", ".ico": "image/x-icon", ".txt": "text/plain; charset=utf-8"}


class HttpError(Exception):
    def __init__(self, status: int, message: str):
        super().__init__(message)
        self.status, self.message = status, message


class SSE:
    """Return from a route to stream events: gen yields (event, id, data) or None for keepalive."""
    def __init__(self, gen):
        self.gen = gen


class RawFile:
    def __init__(self, path: str, content_type: str | None = None):
        self.path, self.content_type = path, content_type


def _json_default(o):
    return str(o)


class Router:
    def __init__(self):
        self.routes = []

    def add(self, method: str, pattern: str, fn):
        self.routes.append((method, re.compile("^" + pattern + "$"), fn))

    def match(self, method: str, path: str):
        for m, rx, fn in self.routes:
            if m == method:
                mt = rx.match(path)
                if mt:
                    return fn, mt.groupdict()
        return None, None


class Server:
    def __init__(self, router: Router, bind: str, port: int, static_dir: str | None = None, cors: bool = False):
        self.router = router
        self.static_dir = static_dir
        self.cors = cors
        self.stopping = threading.Event()
        outer = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, fmt, *args):
                pass

            def do_OPTIONS(self):
                self.send_response(204)
                self._cors()
                self.send_header("Content-Length", "0")
                self.end_headers()

            def do_GET(self):
                self._dispatch("GET")

            def do_POST(self):
                self._dispatch("POST")

            def _cors(self):
                if outer.cors:
                    self.send_header("Access-Control-Allow-Origin", "*")
                    self.send_header("Access-Control-Allow-Headers", "Content-Type, Last-Event-ID")

            def _dispatch(self, method):
                u = urlparse(self.path)
                query = {k: v[-1] for k, v in parse_qs(u.query).items()}
                fn, params = outer.router.match(method, u.path)
                try:
                    if fn is None:
                        if method == "GET" and outer.static_dir:
                            return self._static(u.path)
                        raise HttpError(404, "not found")
                    body = {}
                    if method == "POST":
                        n = int(self.headers.get("Content-Length") or 0)
                        raw = self.rfile.read(n) if n else b""
                        if raw:
                            try:
                                body = json.loads(raw.decode("utf-8"))
                            except ValueError:
                                raise HttpError(400, "body must be JSON")
                    result = fn(self, params=params, query=query, body=body)
                    if isinstance(result, SSE):
                        return self._sse(result)
                    if isinstance(result, RawFile):
                        return self._file(result.path, result.content_type)
                    self._json(200, result)
                except HttpError as e:
                    self._json(e.status, {"error": e.message})
                except (BrokenPipeError, ConnectionResetError):
                    pass
                except Exception as e:  # report instead of dropping the connection
                    self._json(500, {"error": f"{type(e).__name__}: {e}"})

            def _json(self, status, obj):
                data = json.dumps(obj, default=_json_default, allow_nan=False).encode("utf-8")
                self.send_response(status)
                self._cors()
                self.send_header("Content-Type", "application/json; charset=utf-8")
                self.send_header("Cache-Control", "no-store")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def _file(self, path, ctype=None):
                if not os.path.isfile(path):
                    raise HttpError(404, "file not found")
                # Explicit map first: the Windows registry can map .js to text/plain, which
                # browsers refuse for module scripts.
                ctype = ctype or STATIC_TYPES.get(os.path.splitext(path)[1].lower()) \
                    or mimetypes.guess_type(path)[0] or "application/octet-stream"
                size = os.path.getsize(path)
                self.send_response(200)
                self._cors()
                self.send_header("Content-Type", ctype)
                self.send_header("Content-Length", str(size))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                with open(path, "rb") as f:
                    while True:
                        chunk = f.read(1 << 16)
                        if not chunk:
                            break
                        self.wfile.write(chunk)

            def _static(self, path):
                rel = "index.html" if path in ("", "/") else path.lstrip("/")
                base = os.path.abspath(outer.static_dir)
                p = os.path.abspath(os.path.join(base, rel))
                if os.path.commonpath([base, p]) != base:
                    raise HttpError(403, "forbidden")
                return self._file(p)

            def _sse(self, sse):
                self.send_response(200)
                self._cors()
                self.send_header("Content-Type", "text/event-stream")
                self.send_header("Cache-Control", "no-cache")
                self.send_header("Connection", "keep-alive")
                self.send_header("X-Accel-Buffering", "no")
                self.end_headers()
                self.close_connection = True
                try:
                    for item in sse.gen:
                        if outer.stopping.is_set():
                            break
                        if item is None:
                            self.wfile.write(b": keepalive\n\n")
                        else:
                            event, eid, data = item
                            payload = json.dumps(data, default=_json_default, allow_nan=False)
                            msg = (f"id: {eid}\n" if eid is not None else "") + f"event: {event}\ndata: {payload}\n\n"
                            self.wfile.write(msg.encode("utf-8"))
                        self.wfile.flush()
                except (BrokenPipeError, ConnectionResetError, ConnectionAbortedError, OSError):
                    pass
                finally:
                    close = getattr(sse.gen, "close", None)
                    if close:
                        close()

        self.httpd = ThreadingHTTPServer((bind, port), Handler)
        self.httpd.daemon_threads = True
        self.port = self.httpd.server_address[1]
        self._thread = threading.Thread(target=self.httpd.serve_forever, name=f"http-{port}", daemon=True)

    def start(self):
        self._thread.start()
        return self

    def stop(self):
        self.stopping.set()
        self.httpd.shutdown()
        self.httpd.server_close()


def require(body: dict, *keys):
    missing = [k for k in keys if body.get(k) in (None, "")]
    if missing:
        raise HttpError(400, f"missing field(s): {', '.join(missing)}")


def sleep_until(t: float):
    d = t - time.monotonic()
    if d > 0:
        time.sleep(d)
