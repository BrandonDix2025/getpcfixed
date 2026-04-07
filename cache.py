import hashlib
import json
import os
import time

# ── Cache settings ────────────────────────────────────────────────────────────
CACHE_TTL_SECONDS = 3600  # 1 hour — after this, force a fresh Claude call
CACHE_DIR = os.path.join(os.environ.get("APPDATA", ""), "GetPCFixed", "cache")
CACHE_FILE = os.path.join(CACHE_DIR, "diagnosis_cache.json")

# ── Ensure cache directory exists ─────────────────────────────────────────────
os.makedirs(CACHE_DIR, exist_ok=True)


def _load_cache() -> dict:
    """Load the cache file from disk. Returns empty dict if missing or corrupt."""
    try:
        if os.path.exists(CACHE_FILE):
            with open(CACHE_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}


def _save_cache(data: dict):
    """Write cache dict to disk."""
    try:
        with open(CACHE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception:
        pass


def _make_key(scan_data: dict, question: str = "") -> str:
    """
    Build a cache key from PC scan data + optional user question.
    We round CPU/RAM/Disk to nearest 5% so minor fluctuations don't bust the cache.
    """
    cpu_rounded  = round(scan_data.get("cpu", 0) / 5) * 5
    ram_pct      = round((scan_data.get("ram_used", 0) / max(scan_data.get("ram_total", 1), 1)) * 100 / 5) * 5
    disk_pct     = round((scan_data.get("disk_used", 0) / max(scan_data.get("disk_total", 1), 1)) * 100 / 5) * 5
    system       = scan_data.get("system", "")
    question_key = question.strip().lower()[:120]  # first 120 chars of question

    raw = f"{cpu_rounded}|{ram_pct}|{disk_pct}|{system}|{question_key}"
    return hashlib.md5(raw.encode()).hexdigest()


def get_cached(scan_data: dict, question: str = "") -> str | None:
    """
    Return a cached diagnosis if one exists and hasn't expired.
    Returns None if no valid cache entry found.
    """
    key   = _make_key(scan_data, question)
    cache = _load_cache()
    entry = cache.get(key)

    if not entry:
        return None

    age = time.time() - entry.get("timestamp", 0)
    if age > CACHE_TTL_SECONDS:
        # Expired — remove it and return None
        cache.pop(key, None)
        _save_cache(cache)
        return None

    return entry.get("result")


def store_cache(scan_data: dict, result: str, question: str = ""):
    """Store a diagnosis result in the cache."""
    key   = _make_key(scan_data, question)
    cache = _load_cache()
    cache[key] = {
        "result":    result,
        "timestamp": time.time(),
        "question":  question[:120],
    }
    # Keep cache from growing forever — max 100 entries
    if len(cache) > 100:
        # Remove oldest entries first
        sorted_keys = sorted(cache, key=lambda k: cache[k].get("timestamp", 0))
        for old_key in sorted_keys[:len(cache) - 100]:
            cache.pop(old_key, None)
    _save_cache(cache)


def clear_cache():
    """Wipe the entire cache. Called if user wants a forced fresh diagnosis."""
    try:
        if os.path.exists(CACHE_FILE):
            os.remove(CACHE_FILE)
    except Exception:
        pass
