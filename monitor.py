import psutil
import time
import threading
from logger import log_event

# Thresholds
CPU_THRESHOLD  = 85   # %
RAM_THRESHOLD  = 85   # %
DISK_THRESHOLD = 90   # %
CHECK_INTERVAL = 300  # seconds (5 minutes)

# Track last alert state to avoid repeat notifications
_last_alerts = {
    "cpu":  False,
    "ram":  False,
    "disk": False,
}

_running = False
_thread  = None
_notify_callback = None  # Set by app.py to show in-app alerts


def set_notify_callback(fn):
    """Register the app's notification function."""
    global _notify_callback
    _notify_callback = fn


def _notify(title, message):
    """Fire a Windows taskbar notification."""
    try:
        from win10toast import ToastNotifier
        toaster = ToastNotifier()
        toaster.show_toast(
            title,
            message,
            icon_path=None,
            duration=8,
            threaded=True
        )
        log_event("Keep Me Running", f"{title}: {message}")
    except ImportError:
        # win10toast not installed — fall back to callback
        log_event("Keep Me Running", f"{title}: {message}")
    except Exception as e:
        log_event("Keep Me Running Error", str(e))

    # Also call app callback if registered
    if _notify_callback:
        try:
            _notify_callback(title, message)
        except Exception:
            pass


def _check():
    """Run one round of checks and fire alerts if thresholds are crossed."""
    global _last_alerts

    cpu  = psutil.cpu_percent(interval=2)
    ram  = psutil.virtual_memory().percent
    disk = psutil.disk_usage("C:\\").percent

    # --- CPU ---
    if cpu >= CPU_THRESHOLD:
        if not _last_alerts["cpu"]:
            _notify(
                "GetPCFixed — High CPU Usage",
                f"CPU is at {cpu}%. Open GetPCFixed to see what's going on."
            )
        _last_alerts["cpu"] = True
    else:
        _last_alerts["cpu"] = False

    # --- RAM ---
    if ram >= RAM_THRESHOLD:
        if not _last_alerts["ram"]:
            _notify(
                "GetPCFixed — Low Memory",
                f"RAM is {ram}% full. Open GetPCFixed to free up memory."
            )
        _last_alerts["ram"] = True
    else:
        _last_alerts["ram"] = False

    # --- Disk ---
    if disk >= DISK_THRESHOLD:
        if not _last_alerts["disk"]:
            _notify(
                "GetPCFixed — Low Disk Space",
                f"C: drive is {disk}% full. Open GetPCFixed to clean up."
            )
        _last_alerts["disk"] = True
    else:
        _last_alerts["disk"] = False


def _loop():
    """The background loop — checks every 5 minutes."""
    global _running
    while _running:
        try:
            _check()
        except Exception as e:
            log_event("Keep Me Running Error", str(e))
        # Sleep in 1-second chunks so we can stop cleanly
        for _ in range(CHECK_INTERVAL):
            if not _running:
                break
            time.sleep(1)


def start_monitor():
    """Start Keep Me Running in a background thread."""
    global _running, _thread
    if _running:
        return
    _running = True
    _thread = threading.Thread(target=_loop, daemon=True)
    _thread.start()
    log_event("Keep Me Running", "Background monitor started — checking every 5 minutes")


def stop_monitor():
    """Stop Keep Me Running."""
    global _running
    _running = False
    log_event("Keep Me Running", "Background monitor stopped")


def is_running():
    return _running
