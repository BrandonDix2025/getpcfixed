import os
import sys
import anthropic
from scanner import scan_system_data
from logger import log_event
from ratelimit import can_scan, record_scan
from cache import get_cached, store_cache

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def diagnose():
    allowed, msg = can_scan()
    if not allowed:
        return msg

    data = scan_system_data()

    # ── Check cache first ──────────────────────────────────────────────────────
    cached = get_cached(data)
    if cached:
        log_event("AI Diagnosis", f"Served from cache for {data['machine']}")
        return cached + "\n\n*(from recent scan — results are up to date)*"

    # ── No cache hit — call Claude ─────────────────────────────────────────────
    message = f"""
    You are a PC repair expert. Analyze this Windows PC health data and give a plain English diagnosis.
    Tell the user if anything looks wrong and what might be causing it.

    CPU Usage: {data['cpu']}%
    RAM Used: {data['ram_used']} GB of {data['ram_total']} GB
    Disk Used: {data['disk_used']} GB of {data['disk_total']} GB
    System: {data['system']}
    Machine: {data['machine']}

    Keep your response friendly, simple, and helpful. No technical jargon.
    """

    client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    response = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=1024,
        messages=[{"role": "user", "content": message}]
    )

    result = response.content[0].text
    store_cache(data, result)
    record_scan()
    log_event("AI Diagnosis", f"Fresh diagnosis run on {data['machine']}")
    return result


def diagnose_print():
    print("=== GetPCFixed - AI Diagnosis ===")
    print("")
    print(diagnose())
    print("")
    print("=== End of Diagnosis ===")

if __name__ == "__main__":
    diagnose_print()
