import sys
import os
import winreg
from logger import log_event

APP_NAME    = "GetPCFixed"
REG_PATH    = r"Software\Microsoft\Windows\CurrentVersion\Run"


def _get_exe_path() -> str:
    """Returns the path to the running executable."""
    if getattr(sys, 'frozen', False):
        # Running as a PyInstaller .exe
        return sys.executable
    else:
        # Running as a .py script during development
        return os.path.abspath(sys.argv[0])


def is_autostart_enabled() -> bool:
    """Returns True if GetPCFixed is set to start at Windows boot."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_READ
        )
        winreg.QueryValueEx(key, APP_NAME)
        winreg.CloseKey(key)
        return True
    except FileNotFoundError:
        return False
    except Exception as e:
        log_event("Autostart", f"Check failed: {e}")
        return False


def enable_autostart() -> bool:
    """Add GetPCFixed to Windows startup registry. Returns True on success."""
    try:
        exe_path = _get_exe_path()
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.SetValueEx(key, APP_NAME, 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
        log_event("Autostart", f"Enabled — {exe_path}")
        return True
    except Exception as e:
        log_event("Autostart", f"Enable failed: {e}")
        return False


def disable_autostart() -> bool:
    """Remove GetPCFixed from Windows startup registry. Returns True on success."""
    try:
        key = winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            REG_PATH,
            0,
            winreg.KEY_SET_VALUE
        )
        winreg.DeleteValue(key, APP_NAME)
        winreg.CloseKey(key)
        log_event("Autostart", "Disabled")
        return True
    except FileNotFoundError:
        return True   # Already not set — that's fine
    except Exception as e:
        log_event("Autostart", f"Disable failed: {e}")
        return False


def toggle_autostart() -> bool:
    """Flip autostart on or off. Returns the new state (True = enabled)."""
    if is_autostart_enabled():
        disable_autostart()
        return False
    else:
        enable_autostart()
        return True
