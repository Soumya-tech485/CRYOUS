import os
import sys
from dotenv import load_dotenv

# Import untouchable values from constants.py
try:
    from config.constants import (
        APP_NAME,
        APP_VERSION,
        DEFAULT_MODEL,
        DEFAULT_LANGUAGE,
        DEBUG_MODE,
        MAX_RETRIES,
        DEFAULT_TIMEOUT,
    )
except ImportError:
    from .constants import (
        APP_NAME,
        APP_VERSION,
        DEFAULT_MODEL,
        DEFAULT_LANGUAGE,
        DEBUG_MODE,
        MAX_RETRIES,
        DEFAULT_TIMEOUT,
    )

# Load environment variables from .env
load_dotenv()

# --- Dynamic Path Resolution for PyInstaller ---
def get_base_path() -> str:
    """
    Returns the root directory.
    Handles standard execution and PyInstaller's temporary _MEIPASS folder.
    """
    if getattr(sys, 'frozen', False):
        return sys._MEIPASS
    # Go up one level from 'config/' to reach the root project directory
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

BASE_DIR = get_base_path()

# --- Core Paths & Keys ---
VOSK_MODEL_PATH = os.getenv("VOSK_MODEL_PATH", os.path.join(BASE_DIR, "model"))
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile")

# --- Audio Engine Configurations ---
AUDIO_SAMPLE_RATE = 16000
AUDIO_CHANNELS = 1
AUDIO_CHUNK_SIZE = 4000
TTS_RATE = 170

# --- Wake Word Configurations ---
WAKE_WORD_TRIGGERS = ["cryous", "cry us", "krios", "boss"]