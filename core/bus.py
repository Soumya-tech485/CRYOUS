import asyncio
import time


class Bus:
    """Lightweight async pub/sub. Voice, agents and UI all talk through this."""

    def __init__(self):
        self._subs = {}
        self._latest = {}

    def on(self, event, fn):
        self._subs.setdefault(event, []).append(fn)

    async def emit(self, event, payload=None):
        item = {"event": event, "data": payload, "ts": time.time()}
        self._latest[event] = item
        for fn in self._subs.get(event, []):
            try:
                r = fn(payload)
                if asyncio.iscoroutine(r):
                    await r
            except Exception as e:
                print(f"[bus] handler error on {event}: {e}")

    def latest(self, event):
        return self._latest.get(event)