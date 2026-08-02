import queue

import numpy as np
import sounddevice as sd
from vosk import Model, KaldiRecognizer, SetLogLevel

SetLogLevel(-1)

_cache = {}


def get_model(cfg):
    """Load the small offline Vosk model once (~40 MB, ~1-3% CPU while listening)."""
    key = str(cfg.model_dir / cfg.vosk_model)
    if key not in _cache:
        _cache[key] = Model(key)
    return _cache[key]


class Mic:
    """16 kHz mono int16 stream -> queue. Shared by wake-word engine and STT."""

    def __init__(self, block=4000):
        self.q = queue.Queue(maxsize=200)
        self.block = block
        self.stream = None

    def _cb(self, indata, frames, t, status):
        try:
            self.q.put_nowait(bytes(indata))
        except queue.Full:
            try:
                self.q.get_nowait()
                self.q.put_nowait(bytes(indata))
            except queue.Empty:
                pass

    def start(self):
        if self.stream:
            return
        self.stream = sd.RawInputStream(samplerate=16000, blocksize=self.block,
                                        dtype="int16", channels=1, callback=self._cb)
        self.stream.start()

    def stop(self):
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    def read(self, timeout=0.25):
        try:
            return self.q.get(timeout=timeout)
        except queue.Empty:
            return b""

    @staticmethod
    def rms(data):
        a = np.frombuffer(data, np.int16)
        if not len(a):
            return 0.0
        return float(np.sqrt(np.mean(a.astype(np.float64) ** 2)))