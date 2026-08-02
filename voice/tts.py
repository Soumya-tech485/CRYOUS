import asyncio
import hashlib
import threading


class Speaker:
    """edge-tts free Microsoft neural voices, cached to disk, interruptible.
    Falls back to the offline system voice (pyttsx3) if the network is down."""

    def __init__(self, cfg):
        self.cfg = cfg
        self.voice = cfg.tts_voice
        self.cache = cfg.data / "tts_cache"
        self.cache.mkdir(exist_ok=True)
        self._stop = threading.Event()
        self.busy = False

    async def say(self, text, interrupt=True):
        text = (text or "").strip()
        if not self.cfg.tts_enabled or not text:
            return
        if interrupt:
            self.stop()
        self._stop.clear()
        self.busy = True
        try:
            path = await self._synth(text)
            loop = asyncio.get_running_loop()
            if path:
                await loop.run_in_executor(None, self._play_file, path)
            else:
                await loop.run_in_executor(None, self._fallback_speak, text)
        finally:
            self.busy = False

    async def _synth(self, text):
        key = hashlib.md5(f"{self.voice}:{text[:400]}".encode()).hexdigest()
        p = self.cache / f"{key}.mp3"
        if p.exists() and p.stat().st_size > 500:
            return p                                    # cached phrase -> instant, zero network
        tmp = self.cache / f"{key}.part"
        try:
            import edge_tts
            comm = edge_tts.Communicate(text[:500], self.voice, rate="+5%")
            await comm.save(str(tmp))
            tmp.replace(p)
            return p
        except Exception as e:
            print(f"[tts] edge-tts failed ({e}) — using system voice")
            try:
                tmp.unlink(missing_ok=True)
            except Exception:
                pass
            return None

    def _fallback_speak(self, text):
        try:
            import pyttsx3
            eng = pyttsx3.init()
            eng.setProperty("rate", 185)
            eng.say(text[:400])
            eng.runAndWait()
            eng.stop()
        except Exception as e:
            print("[tts] system voice failed:", e)

    def _play_file(self, path):
        try:
            import miniaudio
            src = miniaudio.Mp3File(str(path))
            done = threading.Event()
            stop = self._stop

            def gen():
                try:
                    for chunk in src.read_frames(4096):
                        if stop.is_set():
                            break
                        yield chunk
                finally:
                    done.set()

            with miniaudio.PlaybackDevice(output_format=src.sample_format,
                                          sample_rate=src.sample_rate,
                                          channels=src.nchannels) as dev:
                dev.start(gen())
                while not done.wait(0.12):
                    if stop.is_set():
                        break
        except Exception as e:
            print("[tts] playback error:", e)

    def stop(self):
        self._stop.set()