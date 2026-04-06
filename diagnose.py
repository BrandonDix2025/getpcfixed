import os
import sys
import anthropic
from scanner import scan_system_data
from logger import log_event

if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

def diagnose():
    data = scan_system_data()
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
    log_event("AI Diagnosis", f"Diagnosis run on {data['machine']}")
    return result

def diagnose_print():
    print("=== GetPCFixed - AI Diagnosis ===")
    print("")
    print(diagnose())
    print("")
    print("=== End of Diagnosis ===")

if __name__ == "__main__":
    diagnose_print()