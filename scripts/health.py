"""Diagnostics:  python scripts/health.py"""
import importlib
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
print(f"python {sys.version.split()[0]}  ({sys.executable})\n")

for lib in ("vosk", "numpy", "sounddevice", "miniaudio", "edge_tts", "httpx",
            "fastapi", "uvicorn", "psutil", "fpdf", "docx", "PIL"):
    try:
        importlib.import_module(lib)
        print(f"  ok   {lib}")
    except ImportError:
        print(f"  MISS {lib}  -> pip install -r requirements.txt")

model = ROOT / "data" / "models" / "vosk-model-small-en-us-0.15"
print("\nvosk model:", "ok" if model.exists() else "MISSING -> python scripts/download_model.py")

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")
keys = [k for k in ("GEMINI_API_KEY", "GROQ_API_KEY", "OPENROUTER_API_KEY") if os.getenv(k)]
print("LLM keys:  ", ", ".join(keys) or "NONE — add at least one free key to .env")

try:
    import sounddevice as sd
    print("\naudio devices:")
    print(sd.query_devices())
except Exception as e:
    print("audio:", e)