"""Hardware control via native Windows APIs — no bloatware, near-zero CPU."""
import ctypes
import subprocess
import sys

PUL = ctypes.POINTER(ctypes.c_ulong)


class KeyBdInput(ctypes.Structure):
    _fields_ = [("wVk", ctypes.c_ushort), ("wScan", ctypes.c_ushort),
                ("dwFlags", ctypes.c_ulong), ("time", ctypes.c_ulong), ("dwExtraInfo", PUL)]


class InputUnion(ctypes.Union):
    _fields_ = [("ki", KeyBdInput), ("pad", ctypes.c_byte * 24)]


class Input(ctypes.Structure):
    _fields_ = [("type", ctypes.c_ulong), ("union", InputUnion)]


def _press(vk):
    if sys.platform != "win32":
        return
    extra = ctypes.c_ulong(0)
    down = Input(1, InputUnion(ki=KeyBdInput(vk, 0, 0, 0, ctypes.pointer(extra))))
    up = Input(1, InputUnion(ki=KeyBdInput(vk, 0, 0x0002, 0, ctypes.pointer(extra))))
    ctypes.windll.user32.SendInput(2, (Input * 2)(down, up), ctypes.sizeof(Input))


def volume_up(n=2):
    for _ in range(n):
        _press(0xAF)


def volume_down(n=2):
    for _ in range(n):
        _press(0xAE)


def mute():
    _press(0xAD)


def lock_screen():
    if sys.platform == "win32":
        ctypes.windll.user32.LockWorkStation()


def screenshot(path):
    from PIL import ImageGrab
    ImageGrab.grab().save(path)


def set_brightness(level):
    if sys.platform != "win32":
        return False
    ps = (f"(Get-WmiObject -Namespace root/WMI -Class WmiMonitorBrightnessMethods) | "
          f"Foreach-Object {{ $_.WmiSetBrightness(1, {max(0, min(100, level))}) }}")
    try:
        r = subprocess.run(["powershell", "-Command", ps], capture_output=True, timeout=10)
        return r.returncode == 0
    except Exception:
        return False