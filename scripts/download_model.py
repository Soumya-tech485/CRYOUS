"""Downloads the offline Vosk voice model (~40 MB) — one time only."""
import shutil
import urllib.request
import zipfile
from pathlib import Path

URL = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
NAME = "vosk-model-small-en-us-0.15"

def main():
    dest = Path(__file__).resolve().parent.parent / "data" / "models"
    dest.mkdir(parents=True, exist_ok=True)
    if (dest / NAME).exists():
        print("Model already present.")
        return
    zip_path = dest / "model.zip"
    print(f"Downloading {URL} (~40 MB)...")
    with urllib.request.urlopen(URL) as r, open(zip_path, "wb") as f:
        shutil.copyfileobj(r, f)
    print("Extracting...")
    with zipfile.ZipFile(zip_path) as z:
        z.extractall(dest)
    zip_path.unlink()
    print("Done. Offline voice recognition ready.")

if __name__ == "__main__":
    main()