import asyncio
import platform
import subprocess
import time

from .base import Agent

APPS = {
    "notepad": "notepad.exe", "calculator": "calc.exe", "paint": "mspaint.exe",
    "file explorer": "explorer.exe", "explorer": "explorer.exe", "folder": "explorer.exe",
    "command prompt": "cmd.exe", "terminal": "wt.exe", "cmd": "cmd.exe",
    "task manager": "taskmgr.exe", "settings": "ms-settings:", "control panel": "control.exe",
    "browser": "msedge.exe", "chrome": "chrome.exe", "edge": "msedge.exe",
    "spotify": "spotify.exe", "vs code": "code.cmd", "code editor": "code.cmd",
    "word": "winword.exe", "excel": "excel.exe", "powerpoint": "powerpnt.exe",
}


class SystemAgent(Agent):
    name = "system"
    description = "Open/close apps, volume, brightness, screenshots, system stats, lock screen"
    keywords = ["open", "launch", "start", "close", "kill", "volume", "mute", "brightness",
                "screenshot", "screen capture", "system", "status", "cpu", "ram", "memory",
                "battery", "disk", "lock", "stats", "task manager"]

    async def run(self, task, context=""):
        t = task.lower()
        loop = asyncio.get_running_loop()
        if "screenshot" in t or "screen capture" in t:
            return await loop.run_in_executor(None, self._shot)
        if "volume" in t or "mute" in t:
            return self._volume(t)
        if "brightness" in t:
            return await loop.run_in_executor(None, self._brightness, t)
        if "lock" in t:
            return self._lock()
        if any(k in t for k in ("cpu", "ram", "battery", "disk", "stats", "status", "memory", "system")):
            return await loop.run_in_executor(None, self._stats)
        if "close" in t or "kill" in t:
            return self._kill(t)
        return self._open(t)

    def _open(self, t):
        for app, exe in APPS.items():
            if app in t:
                subprocess.Popen(exe, shell=True)
                return self.done(f"Opening {app}, boss.")
        query = t.replace("open", "").replace("launch", "").replace("start", "").strip()
        if query:
            subprocess.Popen(["cmd", "/c", "start", "", query])
            return self.done(f"Launching {query}, boss.")
        return self.done("Which app, boss?")

    def _kill(self, t):
        import os
        for app, exe in APPS.items():
            if app in t:
                name = os.path.basename(exe)
                subprocess.run(f"taskkill /IM {name} /F", shell=True, capture_output=True)
                return self.done(f"Closed {app}.")
        return self.done("Tell me which app to close.")

    def _volume(self, t):
        from tools import winhw
        if "mute" in t:
            winhw.mute(); return self.done("Muted, boss.")
        if any(k in t for k in ("up", "raise", "increase", "louder")):
            winhw.volume_up(4); return self.done("Volume up.")
        winhw.volume_down(4); return self.done("Volume down.")

    def _brightness(self, t):
        import re
        from tools import winhw
        m = re.search(r"(\d{1,3})", t)
        level = int(m.group(1)) if m else (70 if "up" in t else 30)
        ok = winhw.set_brightness(level)
        return self.done(f"Brightness set to {level}%." if ok else "Brightness control isn't available on this display driver, boss.")

    def _lock(self):
        from tools import winhw
        winhw.lock_screen()
        return self.done("Locking the screen.")

    def _shot(self):
        from tools import winhw
        import datetime
        p = self.ctx.cfg.out_dir / f"screenshot_{datetime.datetime.now():%Y%m%d_%H%M%S}.png"
        winhw.screenshot(str(p))
        return self.done("Screenshot captured, boss.", str(p), [str(p)])

    def _stats(self):
        import psutil
        cpu = psutil.cpu_percent(interval=0.3)
        vm = psutil.virtual_memory()
        du = psutil.disk_usage("C:\\")
        lines = [f"OS: {platform.system()} {platform.release()}  |  Host: {platform.node()}",
                 f"CPU: {cpu}%   RAM: {vm.percent}% ({vm.used // (1024**3)} / {vm.total // (1024**3)} GB)",
                 f"Disk C: {du.percent}% used ({du.free // (1024**3)} GB free)"]
        try:
            bat = psutil.sensors_battery()
            if bat:
                lines.append(f"Battery: {bat.percent}% {'(charging)' if bat.power_plugged else '(on battery)'}")
        except Exception:
            pass
        top = sorted(psutil.process_iter(["name", "memory_percent"]),
                     key=lambda p: p.info.get("memory_percent") or 0, reverse=True)[:3]
        lines.append("Top processes: " + ", ".join(f"{p.info['name']} ({p.info['memory_percent']:.1f}%)" for p in top))
        up = time.time() - psutil.boot_time()
        lines.append(f"Uptime: {int(up // 3600)}h {int(up % 3600 // 60)}m")
        return self.done(f"All systems nominal, boss. CPU {cpu}%, RAM {vm.percent}%.", "\n".join(lines))


AGENT = SystemAgent