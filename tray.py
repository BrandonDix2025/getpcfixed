import sys
import threading
import os
from monitor import start_monitor, stop_monitor, is_running
from logger import log_event

# ── Try to import pystray + PIL ──────────────────────────────────────────────
try:
    import pystray
    from PIL import Image, ImageDraw
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False

_tray_icon = None


def _make_icon_image():
    """Draw a simple mint-green shield icon for the tray."""
    size = 64
    img  = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Shield background
    draw.ellipse([4, 4, 60, 60], fill=(59, 109, 17, 255))

    # White checkmark
    draw.line([16, 34, 28, 46], fill="white", width=5)
    draw.line([28, 46, 48, 22], fill="white", width=5)

    return img


def _on_open(icon, item):
    """Bring the main app window to focus (handled by app.py callback)."""
    log_event("Tray", "Open GetPCFixed clicked from tray")
    if _open_callback:
        try:
            _open_callback()
        except Exception:
            pass


def _on_quit(icon, item):
    """Quit the app cleanly from the tray."""
    log_event("Tray", "Quit clicked from tray")
    stop_monitor()
    icon.stop()
    os._exit(0)


def _on_toggle_monitor(icon, item):
    """Toggle Keep Me Running on/off from the tray menu."""
    if is_running():
        stop_monitor()
        log_event("Tray", "Keep Me Running paused from tray")
    else:
        start_monitor()
        log_event("Tray", "Keep Me Running resumed from tray")


_open_callback = None


def set_open_callback(fn):
    """Register a function to bring the main window to the front."""
    global _open_callback
    _open_callback = fn


def start_tray():
    """Start the system tray icon in a background thread."""
    if not TRAY_AVAILABLE:
        log_event("Tray", "pystray or Pillow not installed — tray icon skipped")
        return

    def _run():
        global _tray_icon

        def monitor_status(item):
            return "Pause monitoring" if is_running() else "Resume monitoring"

        menu = pystray.Menu(
            pystray.MenuItem("Open GetPCFixed", _on_open, default=True),
            pystray.MenuItem(monitor_status, _on_toggle_monitor),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Quit", _on_quit),
        )

        _tray_icon = pystray.Icon(
            "GetPCFixed",
            _make_icon_image(),
            "GetPCFixed — Keep Me Running",
            menu
        )

        log_event("Tray", "System tray icon started")
        _tray_icon.run()

    t = threading.Thread(target=_run, daemon=True)
    t.start()


def stop_tray():
    """Stop the tray icon."""
    global _tray_icon
    if _tray_icon:
        try:
            _tray_icon.stop()
        except Exception:
            pass
