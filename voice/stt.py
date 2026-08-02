import json
import time

from vosk import KaldiRecognizer

from .capture import Mic


def listen_for_command(mic, model, timeout=7, silence_gap=1.25, min_speech=0.35, barge=None):
    """Blocking full-vocabulary transcription. Stops after a natural pause.
    Returns text or None if nothing was heard."""
    rec = KaldiRecognizer(model, 16000)
    start = time.time()
    last_voice = 0.0
    speech = 0.0
    voiced = False
    barged = False

    while True:
        data = mic.read(0.2)
        now = time.time()
        if data:
            if Mic.rms(data) > 300:
                if not voiced:
                    voiced = True
                last_voice = now
                speech += len(data) / 32000.0
                if barge and not barged:
                    barged = True
                    try:
                        barge()
                    except Exception:
                        pass
            rec.AcceptWaveform(data)
        if voiced and now - last_voice >= silence_gap and speech >= min_speech:
            break
        if now - start > (timeout if not voiced else timeout + 6):
            break

    final = json.loads(rec.FinalResult())["text"].strip()
    partial = json.loads(rec.PartialResult())["partial"].strip()
    text = f"{final} {partial}".strip()
    return text if (text and voiced) else None