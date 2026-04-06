import threading
import urllib.request
import json
import os
import subprocess
import tempfile

# ── Current app version ──────────────────────────────────────────────────────
CURRENT_VERSION = "v0.5"
GITHUB_API_URL  = "https://api.github.com/repos/BrandonDix2025/getpcfixed/releases/latest"

# ── Callback set by app.py to show the update banner ─────────────────────────
_update_callback = None

def set_update_callback(fn):
    """Register the function app.py calls to show the update banner."""
    global _update_callback
    _update_callback = fn


def _parse_version(tag: str) -> tuple:
    """Turn 'v0.6' into (0, 6) for easy comparison."""
    clean = tag.lstrip("v").strip()
    parts = clean.split(".")
    try:
        return tuple(int(p) for p in parts)
    except ValueError:
        return (0,)


def _check_for_update():
    """Background worker - hits GitHub API and fires callback if newer version exists."""
    try:
        req = urllib.request.Request(
            GITHUB_API_URL,
            headers={"User-Agent": "GetPCFixed-Updater"}
        )
        with urllib.request.urlopen(req, timeout=8) as resp:
            data = json.loads(resp.read().decode())

        latest_tag   = data.get("tag_name", "")       # e.g. "v0.6"
        latest_name  = data.get("name", latest_tag)   # e.g. "GetPCFixed v0.6"
        download_url = ""

        # Find the .exe asset in the release
        for asset in data.get("assets", []):
            if asset.get("name", "").endswith(".exe"):
                download_url = asset["browser_download_url"]
                break

        if not latest_tag or not download_url:
            return

        if _parse_version(latest_tag) > _parse_version(CURRENT_VERSION):
            if _update_callback:
                _update_callback(latest_tag, latest_name, download_url)

    except Exception:
        pass  # Silent fail - never crash the app over an update check


def check_for_update():
    """Launch the update check in a background thread. Call this on app start."""
    t = threading.Thread(target=_check_for_update, daemon=True)
    t.start()


def download_and_run(download_url: str, version_tag: str):
    """
    Download the installer to a temp file and launch it.
    The installer handles closing the old app and installing the new one.
    """
    try:
        tmp_dir  = tempfile.gettempdir()
        filename = f"GetPCFixed_Setup_{version_tag}.exe"
        tmp_path = os.path.join(tmp_dir, filename)

        req = urllib.request.Request(
            download_url,
            headers={"User-Agent": "GetPCFixed-Updater"}
        )
        with urllib.request.urlopen(req, timeout=60) as resp:
            with open(tmp_path, "wb") as f:
                f.write(resp.read())

        # Launch the installer - runs independently
        subprocess.Popen([tmp_path], shell=False)

    except Exception as e:
        raise RuntimeError(f"Download failed: {e}")
