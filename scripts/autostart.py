"""CRYOUS auto-start at Windows login (Task Scheduler, silent, 30s delay).
   Usage:  python scripts/autostart.py            -> enable
           python scripts/autostart.py --remove   -> disable"""
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VBS = ROOT / "run_silent.vbs"


def build_vbs():
    pyw = ROOT / "venv" / "Scripts" / "pythonw.exe"
    VBS.write_text(
        'Set sh = CreateObject("WScript.Shell")\n'
        f'sh.Run """" & "{pyw}" & """ """ & "{ROOT / "main.py"}" & """", 0, False\n',
        encoding="utf-8")


def enable():
    build_vbs()
    r = subprocess.run(["schtasks", "/create", "/tn", "CRYOUS Assistant", "/tr", str(VBS),
                        "/sc", "onlogon", "/delay", "0000:30", "/f"],
                       capture_output=True, text=True)
    print(r.stdout or r.stderr)
    print("CRYOUS will now boot ~30s after login. Remove with: python scripts/autostart.py --remove")


def disable():
    r = subprocess.run(["schtasks", "/delete", "/tn", "CRYOUS Assistant", "/f"],
                       capture_output=True, text=True)
    print(r.stdout or r.stderr)


if __name__ == "__main__":
    disable() if "--remove" in sys.argv else enable()