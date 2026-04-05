import subprocess
import psutil
import os

def run_diskhealth_scan():
    results = []
    results.append("Disk Health & File Integrity Check\n")

    # Disk usage
    disk = psutil.disk_usage("C:\\")
    used_pct = round((disk.used / disk.total) * 100)
    free_gb = round(disk.free / (1024**3), 1)
    flag = "✅ OK" if used_pct < 85 else "⚠️  HIGH" if used_pct < 95 else "🔴 CRITICAL"
    results.append(f"Disk Usage      : {used_pct}%  [{flag}]")
    results.append(f"Free Space      : {free_gb} GB")

    # Check SMART disk health via WMIC
    results.append("\nDisk Health (SMART):")
    try:
        cmd = [
            "powershell", "-Command",
            "Get-WmiObject -Class MSStorageDriver_FailurePredictStatus -Namespace root\\wmi | Select-Object InstanceName, PredictFailure | Format-List"
        ]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        lines = [l.strip() for l in output.stdout.strip().splitlines() if l.strip()]
        if lines:
            for line in lines[:10]:
                if "False" in line:
                    results.append(f"  ✅ {line.replace('PredictFailure', 'Failure Predicted')}")
                elif "True" in line:
                    results.append(f"  🔴 WARNING: Disk failure predicted! Back up your data NOW!")
                else:
                    results.append(f"  {line}")
        else:
            results.append("  SMART data not available on this system.")
    except Exception as e:
        results.append(f"  Could not check SMART data: {e}")

    # Check disk errors in event log
    results.append("\nRecent Disk Errors:")
    try:
        cmd = [
            "powershell", "-Command",
            "Get-EventLog -LogName System -Source disk -Newest 5 -ErrorAction SilentlyContinue | Select-Object TimeGenerated, Message | Format-List"
        ]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        lines = [l.strip() for l in output.stdout.strip().splitlines() if l.strip()]
        if lines:
            results.append("  ⚠️  Disk errors found in event log:")
            for line in lines[:15]:
                results.append(f"    {line}")
        else:
            results.append("  ✅ No recent disk errors found.")
    except Exception as e:
        results.append(f"  Could not check disk event log: {e}")

    results.append("\n💡 Tips to protect your files:")
    results.append("  1. Run: chkdsk C: /f /r in Admin Command Prompt")
    results.append("  2. Back up important files to an external drive or cloud")
    results.append("  3. Run: sfc /scannow to fix corrupted Windows files")
    results.append("  4. If SMART predicts failure — replace the drive ASAP")

    return "\n".join(results)
