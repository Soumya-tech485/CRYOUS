import asyncio
import json
import time
from pathlib import Path

import psutil
import uvicorn
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

WEB = Path(__file__).parent / "web"
START = time.time()


class UIServer:
    def __init__(self, cfg, bus, voice, brain, db, registry, router):
        self.cfg, self.bus, self.voice, self.brain = cfg, bus, voice, brain
        self.db, self.registry, self.router = db, registry, router
        self.sockets = set()
        app = FastAPI(title="CRYOUS", docs_url=None, redoc_url=None)
        self.app = app

        for ev in ("state", "assistant", "transcript", "agent", "plan", "log", "reminder", "wake"):
            bus.on(ev, self._relay(ev))

        @app.get("/")
        async def index():
            return FileResponse(WEB / "index.html")

        app.mount("/static", StaticFiles(directory=WEB), name="static")

        @app.websocket("/ws")
        async def ws(websocket: WebSocket):
            await websocket.accept()
            self.sockets.add(websocket)
            try:
                while True:
                    await self._on_ws(await websocket.receive_text())
            except WebSocketDisconnect:
                pass
            finally:
                self.sockets.discard(websocket)

        @app.post("/api/chat")
        async def chat(request: Request):
            text = ((await request.json()).get("text") or "").strip()
            if text:
                asyncio.create_task(self._think(text))
            return {"ok": bool(text)}

        @app.post("/api/power")
        async def power(request: Request):
            d = await request.json()
            a = d.get("action", "on")
            if a == "on":
                await voice.power_on()
            elif a == "off":
                await voice.power_off()
            elif a == "sleep":
                await voice.sleep_for(int(d.get("minutes", 10)))
            return {"ok": True, "state": voice.state}

        @app.post("/api/mic")
        async def mic(request: Request):
            voice.mic_on = bool((await request.json()).get("on", True))
            await bus.emit("log", {"msg": f"microphone {'on' if voice.mic_on else 'muted'}"})
            return {"ok": True, "mic": voice.mic_on}

        @app.get("/api/stats")
        async def stats():
            try:
                bat = psutil.sensors_battery()
            except Exception:
                bat = None
            return {
                "cpu": psutil.cpu_percent(interval=None),
                "ram": psutil.virtual_memory().percent,
                "battery": bat.percent if bat else None,
                "state": voice.state, "mic": voice.mic_on, "enabled": voice.enabled,
                "usage": router.usage(),
                "providers": [{"name": p.name} for p in router.providers],
                "agents": list(registry.agents.keys()),
                "uptime": int(time.time() - START),
            }

    async def _think(self, text):
        try:
            await self.bus.emit("transcript", {"text": text, "source": "ui"})
            await self.voice.handle_text(text)
        except Exception as e:
            await self.bus.emit("assistant", {"summary": f"Error: {e}", "detail": str(e), "kind": "error"})

    async def _on_ws(self, raw):
        try:
            msg = json.loads(raw)
            if msg.get("type") == "chat":
                asyncio.create_task(self._think(msg.get("text", "")))
        except Exception:
            pass

    def _relay(self, event):
        async def handler(payload):
            await self._broadcast({"type": event, "data": payload, "ts": time.time()})
        return handler

    async def _broadcast(self, msg):
        if not self.sockets:
            return
        raw = json.dumps(msg, default=str)
        dead = set()
        for ws in list(self.sockets):
            try:
                await ws.send_text(raw)
            except Exception:
                dead.add(ws)
        self.sockets -= dead

    async def run(self):
        config = uvicorn.Config(self.app, host="127.0.0.1", port=self.cfg.ui_port,
                                log_level="warning", access_log=False)
        await uvicorn.Server(config).serve()