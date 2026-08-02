import os
from pathlib import Path
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"


class Config:
    def __init__(self):
        load_dotenv(ROOT / ".env")
        self.root = ROOT
        self.data = DATA
        self.model_dir = DATA / "models"
        self.out_dir = DATA / "output"
        self.log_dir = DATA / "logs"
        for d in (self.model_dir, self.out_dir, self.log_dir, DATA / "db", DATA / "tts_cache"):
            d.mkdir(parents=True, exist_ok=True)

        self.gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
        self.groq_key = os.getenv("GROQ_API_KEY", "").strip()
        self.openrouter_key = os.getenv("OPENROUTER_API_KEY", "").strip()
        self.ollama_url = os.getenv("OLLAMA_URL", "").strip()

        self.tts_voice = os.getenv("TTS_VOICE", "en-GB-GeorgeNeural")
        self.tts_enabled = os.getenv("TTS_ENABLED", "1") == "1"
        self.wake_word = os.getenv("WAKE_WORD", "cryous").lower()
        self.barge = os.getenv("BARGE_IN", "0") == "1"
        self.greet = os.getenv("GREET_ON_BOOT", "1") == "1"
        self.speak_ui = os.getenv("SPEAK_UI", "1") == "1"
        self.vosk_model = os.getenv("VOSK_MODEL", "vosk-model-small-en-us-0.15")

        self.ui_port = int(os.getenv("UI_PORT", "8123"))
        self.weekly_budget = int(os.getenv("WEEKLY_TOKEN_BUDGET", "1500000000"))
        self.max_history = int(os.getenv("MAX_HISTORY", "8"))
        self.user_name = os.getenv("USER_NAME", "boss")

        self.smtp_host = os.getenv("SMTP_HOST", "")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_user = os.getenv("SMTP_USER", "")
        self.smtp_pass = os.getenv("SMTP_PASS", "")

    @classmethod
    def load(cls):
        return cls()