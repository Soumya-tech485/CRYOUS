import os
import json
import time
import threading
import pyaudio
from vosk import Model, KaldiRecognizer

class WakeWordDetector:
    def __init__(self, model_path: str = "model"):
        """
        Initializes the offline Vosk wake word detector for background daemon execution.
        """
        self.model_path = model_path
        self._model = None
        self._stop_event = threading.Event()

    def _load_model(self) -> Model:
        """Lazy-loads and validates the Vosk model directory."""
        if self._model is None:
            if not os.path.exists(self.model_path):
                raise FileNotFoundError(
                    f"[Error] Vosk model directory not found at path: '{self.model_path}'"
                )
            self._model = Model(self.model_path)
        return self._model

    def stop(self):
        """Signals the background listener to stop listening cleanly."""
        self._stop_event.set()

    def reset(self):
        """Resets the stop signal for subsequent listening sessions."""
        self._stop_event.clear()

    def listen_for_wake_word(self, triggers: list = None) -> bool:
        """
        Runs continuously in background loop using minimal CPU.
        Releases audio hardware and returns True immediately upon wake word detection.
        """
        if triggers is None:
            triggers = ["cryous", "cry us", "krios", "boss"]

        try:
            model = self._load_model()
        except Exception as e:
            print(f"[Error] Failed to load Vosk model for WakeWordDetector: {e}")
            return False

        # Dynamically construct Vosk grammar filter from trigger list
        grammar_list = list(set([t.lower() for t in triggers] + ["[unk]"]))
        grammar = json.dumps(grammar_list)

        pa = pyaudio.PyAudio()
        stream = None

        try:
            stream = pa.open(
                format=pyaudio.paInt16,
                channels=1,
                rate=16000,
                input=True,
                frames_per_buffer=8000
            )
            stream.start_stream()
            rec = KaldiRecognizer(model, 16000, grammar)

            print("\n[Background] CRYOUS service active. Listening for wake word...")

            self.reset()
            while not self._stop_event.is_set():
                data = stream.read(4000, exception_on_overflow=False)
                if rec.AcceptWaveform(data):
                    result = json.loads(rec.Result())
                    text = result.get("text", "")

                    if any(trigger in text for trigger in triggers):
                        print(f"\n[System] Wake word triggered! Heard: '{text}'")
                        return True

                # Small sleep tick to prevent CPU starvation
                time.sleep(0.01)

        except Exception as e:
            print(f"[Error] Exception in WakeWordDetector: {e}")
            return False
        finally:
            if stream is not None:
                try:
                    stream.stop_stream()
                    stream.close()
                except Exception:
                    pass
            pa.terminate()

        return False

# --- Standalone Function Wrapper ---

def start_wake_word_listener(model_path: str = "model", triggers: list = None) -> bool:
    """Helper wrapper for quick single-call detection."""
    detector = WakeWordDetector(model_path=model_path)
    return detector.listen_for_wake_word(triggers=triggers)