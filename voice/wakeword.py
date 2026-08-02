import difflib
import json
import time

from vosk import KaldiRecognizer

from .capture import get_model


def _variants(word):
    v = {word, word[:4], word.replace("y", "i"), word + "s"}
    if word == "cryous":
        v |= {"cryus", "kryous", "kryus", "crys", "cryoss"}
    return [w for w in v if len(w) >= 4]


def _hit(text, words):
    for tok in text.lower().split():
        tok = tok.strip(".,!?'\"")
        if len(tok) < 4:
            continue
        for w in words:
            if abs(len(tok) - len(w)) > 2:
                continue
            if tok == w or difflib.SequenceMatcher(None, tok, w).ratio() >= 0.8:
                return True
    return False


class WakeWordEngine:
    """Continuous offline detection of 'Cryous' with fuzzy matching."""

    def __init__(self, cfg):
        self.model = get_model(cfg)
        self.words = _variants(cfg.wake_word)

    def listen(self, mic, alive):
        """Blocking. Returns True the moment the wake word is heard."""
        rec = KaldiRecognizer(self.model, 16000)
        last_reset = time.time()
        while alive():
            data = mic.read(0.2)
            if not data:
                continue
            if rec.AcceptWaveform(data):
                text = json.loads(rec.Result())["text"]
            else:
                text = json.loads(rec.PartialResult())["partial"]
            if text and _hit(text, self.words):
                rec.Reset()
                return True
            if time.time() - last_reset > 25:
                rec.Reset()
                last_reset = time.time()
        return False