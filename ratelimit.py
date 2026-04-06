import os
import json
import sys
from datetime import datetime, timedelta

# Store rate limit data in AppData alongside the log
if getattr(sys, 'frozen', False):
    _app_data = os.path.join(os.environ.get('APPDATA', os.path.expanduser('~')), 'GetPCFixed')
else:
    _app_data = os.path.join(os.path.dirname(os.path.abspath(__file__)))

os.makedirs(_app_data, exist_ok=True)
RATE_FILE = os.path.join(_app_data, 'ratelimit.json')

FREE_LIMIT    = 1          # scans allowed per week on free tier
FREE_WINDOW   = 7          # days


def _load():
    if not os.path.exists(RATE_FILE):
        return {}
    try:
        with open(RATE_FILE, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def _save(data):
    try:
        with open(RATE_FILE, 'w') as f:
            json.dump(data, f, indent=4)
    except Exception:
        pass


def can_scan():
    """
    Returns (allowed: bool, message: str)
    allowed = True  → user may proceed
    allowed = False → user has hit the free limit
    """
    data   = _load()
    now    = datetime.now()
    window = now - timedelta(days=FREE_WINDOW)

    # Filter scans to only those within the last 7 days
    recent = [
        ts for ts in data.get('scans', [])
        if datetime.fromisoformat(ts) > window
    ]

    if len(recent) < FREE_LIMIT:
        return True, ""

    # Find when the oldest scan in the window expires
    oldest   = min(datetime.fromisoformat(ts) for ts in recent)
    unlocks  = oldest + timedelta(days=FREE_WINDOW)
    days_left = (unlocks - now).days + 1

    msg = (
        f"You've used your free AI scan for this week.\n\n"
        f"Your next free scan unlocks in {days_left} day(s).\n\n"
        f"Upgrade to GetPCFixed Pro for unlimited AI scans — $4.99/month.\n"
        f"Coming soon at getpcfixed.com"
    )
    return False, msg


def record_scan():
    """Call this AFTER a successful AI scan to record the timestamp."""
    data = _load()
    scans = data.get('scans', [])
    scans.append(datetime.now().isoformat())

    # Keep only last 30 entries to prevent file bloat
    data['scans'] = scans[-30:]
    _save(data)
