import asyncio
import re

from . import stt
from .capture import Mic, get_model
from .tts import Speaker
from .wakeword import WakeWordEngine

NEG = re.compile(r"\b(no|nope|nah|not really|that'?s all|thats all|nothing else|no thanks|"
                 r"no thank you|bye|goodbye|dismissed|stand down)\b")
SLEEP_PHRASES = ("go to sleep", "power down", "goodnight", "sleep mode", "shut down cryous")


class VoiceAssistant:
    DORMANT = "dormant"
    LISTENING = "listening"
    THINKING = "thinking"
    SPEAKING = "speaking"
    FOLLOWUP = "followup"
    SLEEP = "sleep"
    OFF = "off"

    def __init__(self, cfg, bus, brain, registry, db):
        self.cfg, self.bus, self.brain, self.registry, self.db = cfg, bus, brain, registry, db
        self.speaker = Speaker(cfg)
        self.state = self.OFF
        self.enabled = False
        self.mic_on = True
        self.mic = None
        self.ww = None
        self._sleep_handle = None

    async def set_state(self, s):
        self.state = s
        await self.bus.emit("state", {"state": s})

    # ── power ──
    async def power_on(self):
        if self.enabled:
            return
        self.enabled = True
        await self.set_state(self.DORMANT)
        await self.bus.emit("log", {"msg": "voice engine armed — waiting for wake word"})
        await self.speaker.say("Systems online. Say my name and I'm at your service, boss.")

    async def power_off(self, silent=False):
        self.enabled = False
        if self._sleep_handle:
            self._sleep_handle.cancel()
            self._sleep_handle = None
        await self.set_state(self.OFF)
        if not silent:
            await self.speaker.say("Powering down my ears, boss. Use the dashboard to wake me.")

    async def sleep_for(self, minutes=10):
        await self.speaker.say(f"Sleeping for {minutes} minutes, boss.")
        self.enabled = False
        await self.set_state(self.SLEEP)
        loop = asyncio.get_running_loop()
        self._sleep_handle = loop.call_later(minutes * 60, lambda: asyncio.ensure_future(self.power_on()))

    # ── main loop ──
    async def run(self):
        await asyncio.sleep(1.0)                        # let the UI come up first
        try:
            self.mic = Mic()
            self.ww = WakeWordEngine(self.cfg)
            self.mic.start()
        except Exception as e:
            await self.bus.emit("log", {"msg": f"microphone unavailable ({e}) — text mode only"})
            return

        model = get_model(self.cfg)
        self.enabled = True
        await self.set_state(self.DORMANT)
        if self.cfg.greet:
            await self.speaker.say("Systems online. Say my name and I'm at your service, boss.")

        loop = asyncio.get_running_loop()
        while True:
            try:
                if not (self.enabled and self.mic_on):
                    await asyncio.sleep(0.4)
                    continue
                while self.speaker.busy:                # never listen to my own voice
                    await asyncio.sleep(0.2)
                heard = await loop.run_in_executor(
                    None, self.ww.listen, self.mic, lambda: self.enabled and self.mic_on)
                if heard:
                    await self._session(model, loop)
            except asyncio.CancelledError:
                raise
            except Exception as e:
                await self.bus.emit("log", {"msg": f"voice loop: {e}"})
                await asyncio.sleep(2)

    # ── a full wake → command → followup session ──
    async def _session(self, model, loop):
        await self.bus.emit("wake", {"ts": 1})
        await self.speaker.say("Yes boss. Tell me, what can I do for you?")
        barge = self.speaker.stop if self.cfg.barge else None
        first = True
        while self.enabled:
            await self.set_state(self.LISTENING if first else self.FOLLOWUP)
            while self.speaker.busy:
                await asyncio.sleep(0.12)
            text = await loop.run_in_executor(None, stt.listen_for_command,
                                              self.mic, model, 7, 1.25, 0.35, barge)
            if not text:
                await self.speaker.say("I didn't catch that, boss. Back to standby." if first
                                       else "Standing by, boss.")
                return
            await self.bus.emit("transcript", {"text": text, "source": "voice"})
            low = text.lower()
            if not first and NEG.search(low):
                await self.speaker.say("Very well, boss. Back to standby.")
                return
            if any(p in low for p in SLEEP_PHRASES):
                await self.sleep_for(10)
                return
            await self.handle_command(text)
            first = False
            await self.speaker.say("Anything else, boss?")

    # ── shared command handler (voice path) ──
    async def handle_command(self, text):
        await self.set_state(self.THINKING)
        try:
            resp = await self.brain.think(text, session="voice")
        except Exception as e:
            resp = {"summary": f"Sorry boss, systems hiccuped: {e}", "detail": str(e), "kind": "error"}
        summary = (resp.get("summary") or resp.get("detail") or "Done.")[:300]
        await self.bus.emit("assistant", {"summary": summary,
                                          "detail": resp.get("detail", ""),
                                          "kind": resp.get("kind", "chat")})
        await self.set_state(self.SPEAKING)
        await self.speaker.say(summary)
        return resp

    # ── typed chat path ──
    async def handle_text(self, text, speak=None):
        speak = self.cfg.speak_ui if speak is None else speak
        resp = await self.brain.think(text, session="ui")
        summary = (resp.get("summary") or "")[:300]
        await self.bus.emit("assistant", {"summary": summary,
                                          "detail": resp.get("detail", ""),
                                          "kind": resp.get("kind", "chat")})
        if speak and self.enabled:
            await self.speaker.say(summary)
        return resp

    def shutdown(self):
        self.enabled = False
        try:
            if self.mic:
                self.mic.stop()
        except Exception:
            pass