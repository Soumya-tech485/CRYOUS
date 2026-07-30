import pyaudio
import json
from vosk import Model, KaldiRecognizer

class WakeWordDetector:
    def __init__(self, model_path: str):
        """Initializes the offline Vosk wake word recognizer."""
        self.model_path = model_path
        self.model = Model(model_path)

    def listen_for_wake_word(self, triggers=None) -> bool:
        """
        Runs continuously in the background using minimal CPU.
        Returns True immediately when a wake word is detected.
        """
        if triggers is None:
            triggers = ["cryous", "cry us", "krios", "boss"]

        pa = pyaudio.PyAudio()
        stream = pa.open(
            format=pyaudio.paInt16, 
            channels=1, 
            rate=16000, 
            input=True, 
            frames_per_buffer=8000
        )
        stream.start_stream()

        # Restricted grammar forces Vosk to match only these words, reducing memory & CPU load
        grammar = '["cry us", "cryous", "krios", "boss", "[unk]"]'
        rec = KaldiRecognizer(self.model, 16000, grammar)

        print("\n[Background] CRYOUS service active. Listening for wake word...")

        try:
            while True:
                data = stream.read(4000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")

                    if any(trigger in text for trigger in triggers):
                        print(f"\n[System] Wake word triggered! Heard: '{text}'")
                        return True
        finally:
            stream.stop_stream()
            stream.close()
            pa.terminate()