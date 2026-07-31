import winreg as reg
import os
import sys

def add_cryous_to_startup():
    """
    Programmatically adds the compiled CRYOUS executable to the Windows Registry
    so it boots automatically on system startup.
    """
    # Use the path to the current executable (PyInstaller) or script
    if getattr(sys, 'frozen', False):
        app_path = sys.executable
    else:
        app_path = os.path.realpath(sys.argv[0])

    app_name = "CRYOUS_OS"
    key = reg.HKEY_CURRENT_USER
    key_value = r"Software\Microsoft\Windows\CurrentVersion\Run"

    try:
        registry_key = reg.OpenKey(key, key_value, 0, reg.KEY_ALL_ACCESS)
        # Add the script to startup
        reg.SetValueEx(registry_key, app_name, 0, reg.REG_SZ, app_path)
        reg.CloseKey(registry_key)
        print("[System] CRYOUS successfully added to Windows startup registry.")
    except Exception as e:
        print(f"[Error] Failed to add to registry: {e}")

if __name__ == "__main__":
    add_cryous_to_startup()