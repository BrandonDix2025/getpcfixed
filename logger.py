import json
import os
from datetime import datetime

LOG_FILE = "getpcfixed_log.json"

def load_log():
    if not os.path.exists(LOG_FILE):
        return []
    with open(LOG_FILE, "r") as f:
        return json.load(f)

def save_log(log):
    with open(LOG_FILE, "w") as f:
        json.dump(log, f, indent=4)

def log_event(event_type, details, undo_data=None):
    log = load_log()
    entry = {
        "date":    datetime.now().strftime("%Y-%m-%d"),
        "time":    datetime.now().strftime("%I:%M %p"),
        "type":    event_type,
        "details": details
    }
    if undo_data:
        entry["undo_data"] = undo_data
    log.append(entry)
    save_log(log)

def show_log():
    log = load_log()
    print("=== GetPCFixed — History Log ===")
    print("")
    if not log:
        print("No history yet. Run a scan or fix first!")
    else:
        for entry in log:
            print(f"[{entry['date']} {entry['time']}] {entry['type']}")
            print(f"   {entry['details']}")
            print("")
    print("=== End of Log ===")

if __name__ == "__main__":
    show_log()