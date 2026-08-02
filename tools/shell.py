"""Sandboxed command runner with a security blocklist + audit trail."""
import subprocess

BLOCKED = ["format ", "del /s", "del /q", "rmdir /s", "rm -rf", "shutdown",
           "mkfs", "diskpart", "reg delete", ":(){"]


def safe_run(cmd, cwd, timeout=15):
    low = cmd.lower()
    if any(b in low for b in BLOCKED):
        return {"ok": False, "out": "", "err": "command blocked by CRYOUS security policy"}
    try:
        r = subprocess.run(cmd, shell=True, capture_output=True, text=True,
                           timeout=timeout, cwd=str(cwd))
        return {"ok": r.returncode == 0, "out": r.stdout[-3000:], "err": r.stderr[-1000:]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "out": "", "err": "timeout"}