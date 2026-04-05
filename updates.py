import subprocess
import os
import shutil

def fix_updates():
    results = []
    results.append("Running Windows Update Fix...\n")

    # Stop Windows Update services
    subprocess.run(["net", "stop", "wuauserv"], capture_output=True)
    subprocess.run(["net", "stop", "bits"], capture_output=True)
    subprocess.run(["net", "stop", "cryptsvc"], capture_output=True)
    results.append("✅ Stopped Windows Update services")

    # Clear Windows Update cache
    cache_path = os.path.join(os.environ.get("SystemRoot", "C:\\Windows"), "SoftwareDistribution", "Download")
    try:
        if os.path.exists(cache_path):
            shutil.rmtree(cache_path)
            os.makedirs(cache_path)
            results.append("✅ Cleared Windows Update cache")
    except Exception as e:
        results.append(f"⚠️  Could not clear cache (run as Admin): {e}")

    # Restart Windows Update services
    subprocess.run(["net", "start", "cryptsvc"], capture_output=True)
    subprocess.run(["net", "start", "bits"], capture_output=True)
    subprocess.run(["net", "start", "wuauserv"], capture_output=True)
    results.append("✅ Restarted Windows Update services")

    # Open Windows Update settings
    subprocess.Popen(["explorer.exe", "ms-settings:windowsupdate"])
    results.append("✅ Opened Windows Update settings")

    results.append("\n✅ Done! Windows Update has been reset.")
    results.append("👉 What to do next:")
    results.append("   1. Look at the Windows Update window that just opened")
    results.append("   2. Click the 'Check for updates' button")
    results.append("   3. Let Windows download and install any updates it finds")
    results.append("   4. Restart your PC when it asks you to")

    return "\n".join(results)


def run_updates_scan():
    results = []
    results.append("Windows Update Diagnostic\n")

    # Check Windows Update service status
    results.append("Windows Update Service:")
    try:
        cmd = [
            "powershell", "-Command",
            "Get-Service -Name wuauserv | Select-Object Status, StartType | Format-List"
        ]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        lines = [l.strip() for l in output.stdout.strip().splitlines() if l.strip()]
        for line in lines:
            if "Running" in line:
                results.append(f"  ✅ {line}")
            elif "Stopped" in line:
                results.append(f"  ⚠️  {line} — Update service is stopped!")
            else:
                results.append(f"  {line}")
    except Exception as e:
        results.append(f"  Could not check update service: {e}")

    # Check last update time
    results.append("\nLast Windows Update:")
    try:
        cmd = [
            "powershell", "-Command",
            "Get-HotFix | Sort-Object InstalledOn -Descending | Select-Object -First 5 HotFixID, InstalledOn, Description | Format-List"
        ]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        lines = [l.strip() for l in output.stdout.strip().splitlines() if l.strip()]
        if lines:
            for line in lines[:20]:
                results.append(f"  {line}")
        else:
            results.append("  Could not retrieve update history.")
    except Exception as e:
        results.append(f"  Could not check update history: {e}")

    # Check disk space (updates need space)
    import psutil
    disk = psutil.disk_usage("C:\\")
    free_gb = round(disk.free / (1024**3), 1)
    flag = "✅ OK" if free_gb > 10 else "⚠️  LOW"
    results.append(f"\nFree Disk Space : {free_gb} GB  [{flag}]")
    if free_gb < 10:
        results.append("  ⚠️  Low disk space can cause Windows updates to fail!")
        results.append("  Run the Junk File Cleaner to free up space first.")

    results.append("\n💡 Tips to fix stuck updates:")
    results.append("  1. Restart your PC and try updating again")
    results.append("  2. Free up disk space — updates need at least 10 GB")
    results.append("  3. Run Windows Update Troubleshooter in Settings")
    results.append("  4. Try: net stop wuauserv then net start wuauserv")

    return "\n".join(results)
