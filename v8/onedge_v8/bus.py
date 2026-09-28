"""In-process event bus feeding live displays (never feeding the recorder).

publish() never blocks: each subscriber has a bounded queue; when a slow display client
falls behind, its oldest display events are dropped and counted. Acquisition and recording
are unaffected by display clients. A ring buffer lets a reconnecting client backfill.
"""
from __future__ import annotations

import collections
import itertools
import queue
import threading
import time


class Subscription:
    def __init__(self, bus, maxsize: int):
        self.bus = bus
        self.q: queue.Queue = queue.Queue(maxsize=maxsize)
        self.dropped = 0

    def get(self, timeout: float):
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return None

    def close(self):
        self.bus._unsubscribe(self)


class EventBus:
    def __init__(self, ring_size: int = 4000, sub_queue: int = 2000):
        self._lock = threading.Lock()
        self._ids = itertools.count(1)
        self._ring = collections.deque(maxlen=ring_size)
        self._subs: list = []
        self.sub_queue = sub_queue
        self.published = 0

    def publish(self, kind: str, data: dict):
        ev = {"id": next(self._ids), "kind": kind, "t_mono_ns": time.monotonic_ns(), "data": data}
        with self._lock:
            self._ring.append(ev)
            subs = list(self._subs)
            self.published += 1
        for s in subs:
            try:
                s.q.put_nowait(ev)
            except queue.Full:
                try:
                    s.q.get_nowait()
                    s.q.put_nowait(ev)
                except (queue.Empty, queue.Full):
                    pass
                s.dropped += 1
        return ev["id"]

    def subscribe(self, last_id: int | None = None) -> Subscription:
        sub = Subscription(self, self.sub_queue)
        with self._lock:
            if last_id is not None:
                for ev in self._ring:
                    if ev["id"] > last_id:
                        try:
                            sub.q.put_nowait(ev)
                        except queue.Full:
                            sub.dropped += 1
            self._subs.append(sub)
        return sub

    def _unsubscribe(self, sub):
        with self._lock:
            if sub in self._subs:
                self._subs.remove(sub)

    def stats(self) -> dict:
        with self._lock:
            return {"published": self.published, "subscribers": len(self._subs),
                    "dropped_for_display": sum(s.dropped for s in self._subs)}
