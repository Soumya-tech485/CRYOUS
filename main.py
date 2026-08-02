"""CRYOUS — self-growing personal AI operating system. Entry point."""
import asyncio

from core.config import Config
from core.bus import Bus
from core.memory import Memory
from core.router import OmniRouter
from core.brain import Brain
from core.improver import Improver
from agents import build_registry
from agents.reminder_agent import ReminderService
from voice.assistant import VoiceAssistant
from ui.server import UIServer


async def main():
    cfg = Config.load()
    bus = Bus()
    db = Memory(cfg)
    router = OmniRouter(cfg, db)
    improver = Improver(cfg, db)
    brain = Brain(cfg, router, db, improver)
    registry = build_registry(cfg, router, db, bus, brain)
    brain.set_wiring(registry, bus)

    voice = VoiceAssistant(cfg, bus, brain, registry, db)
    brain.voice = voice
    reminders = ReminderService(db, bus, voice)
    ui = UIServer(cfg, bus, voice, brain, db, registry, router)

    await bus.emit("log", {"msg": f"core online | providers: {[p.name for p in router.providers] or 'NONE - add a key to .env'}"})
    await bus.emit("log", {"msg": f"command deck -> http://127.0.0.1:{cfg.ui_port}"})

    try:
        await asyncio.gather(ui.run(), voice.run(), reminders.run())
    except (KeyboardInterrupt, asyncio.CancelledError):
        pass
    finally:
        voice.shutdown()
        db.close()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nCRYOUS offline.")