import pyttsx3
import threading
import queue

class Speaker:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, *args, **kwargs):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(Speaker, cls).__new__(cls)
                cls._instance._initialized = False
            return cls._instance

    def __init__(self, rate: int = 170):
        if getattr(self, '_initialized', False):
            return
            
        self.rate = rate
        self.speech_queue = queue.Queue()
        self.worker_thread = threading.Thread(target=self._process_queue, daemon=True)
        self.worker_thread.start()
        self._initialized = True

    def _process_queue(self):
        """Dedicated background thread that processes speech without blocking the OS."""
        # Initialize pyttsx3 inside the thread where it will be used
        engine = pyttsx3.init()
        engine.setProperty('rate', self.rate)
        
        while True:
            text = self.speech_queue.get()
            if text is None: # Poison pill to kill thread if needed
                break
            
            try:
                engine.say(text)
                engine.runAndWait()
            except Exception as e:
                print(f"[Error] TTS loop interrupted: {e}")
            finally:
                self.speech_queue.task_done()

    def speak(self, text: str):
        """Pushes text to the background thread. Returns immediately."""
        if not text:
            return
            
        print(f"\n[CRYOUS Speaking]: {text}")
        self.speech_queue.put(text)

# --- Standalone Function Wrapper ---
_default_speaker = Speaker(rate=170)

def speak_text(text: str):
    _default_speaker.speak(text)