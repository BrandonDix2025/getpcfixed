import psutil
import platform
from logger import log_event

def scan_system():
    print("=== GetPCFixed — System Scan ===")
    print("")
    cpu = psutil.cpu_percent(interval=1)
    print(f"CPU Usage:     {cpu}%")
    ram = psutil.virtual_memory()
    ram_used = round(ram.used / (1024**3), 2)
    ram_total = round(ram.total / (1024**3), 2)
    print(f"RAM Usage:     {ram_used} GB used of {ram_total} GB")
    disk = psutil.disk_usage("C:\\")
    disk_used = round(disk.used / (1024**3), 2)
    disk_total = round(disk.total / (1024**3), 2)
    print(f"Disk Usage:    {disk_used} GB used of {disk_total} GB")
    print(f"System:        {platform.system()} {platform.release()}")
    print(f"Machine Name:  {platform.node()}")
    print("")
    print("=== Scan Complete ===")
    log_event("Scan", f"CPU: {cpu}% | RAM: {ram_used}GB of {ram_total}GB | Disk: {disk_used}GB of {disk_total}GB")

def scan_system_data():
    cpu = psutil.cpu_percent(interval=1)
    ram = psutil.virtual_memory()
    disk = psutil.disk_usage("C:\\")
    return {
        "cpu": cpu,
        "ram_used": round(ram.used / (1024**3), 2),
        "ram_total": round(ram.total / (1024**3), 2),
        "disk_used": round(disk.used / (1024**3), 2),
        "disk_total": round(disk.total / (1024**3), 2),
        "system": platform.system() + " " + platform.release(),
        "machine": platform.node()
    }

if __name__ == "__main__":
    scan_system()