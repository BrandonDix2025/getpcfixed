import os
from logger import log_event

JUNK_FOLDERS = [
    os.environ.get("TEMP"),
    os.environ.get("TMP"),
    "C:\\Windows\\Temp",
]

def scan_junk():
    total_size = 0
    total_files = 0

    for folder in JUNK_FOLDERS:
        if not folder or not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for file in files:
                try:
                    filepath = os.path.join(root, file)
                    total_size += os.path.getsize(filepath)
                    total_files += 1
                except:
                    pass

    size_mb = round(total_size / (1024**2), 2)
    return total_files, size_mb

def clean_junk():
    print("=== GetPCFixed — Junk File Cleaner ===")
    print("")
    print("Scanning for junk files...")
    print("")

    total_files, size_mb = scan_junk()

    print(f"Found {total_files} junk files taking up {size_mb} MB")
    print("")

    confirm = input("Want us to clean these up? (yes/no): ")

    if confirm.lower() != "yes":
        print("No changes made. Goodbye!")
        return

    cleaned = 0
    for folder in JUNK_FOLDERS:
        if not folder or not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for file in files:
                try:
                    filepath = os.path.join(root, file)
                    os.remove(filepath)
                    cleaned += 1
                except:
                    pass

    print("")
    print(f"✅ FIXED — Cleaned {cleaned} junk files and freed up {size_mb} MB!")
    print("Your PC has more breathing room now.")
    log_event("Junk Clean", f"Cleaned {cleaned} files and freed up {size_mb} MB")
def clean_junk_silent():
    cleaned = 0
    total_size = 0

    for folder in JUNK_FOLDERS:
        if not folder or not os.path.exists(folder):
            continue
        for root, dirs, files in os.walk(folder):
            for file in files:
                try:
                    filepath = os.path.join(root, file)
                    total_size += os.path.getsize(filepath)
                    os.remove(filepath)
                    cleaned += 1
                except:
                    pass

    size_mb = round(total_size / (1024**2), 2)
    return cleaned, size_mb
if __name__ == "__main__":
    clean_junk()