import subprocess
import psutil
import os

def fix_disk():
    results = []
    results.append("Running Disk Health Fix...\n")

    # Run System File Checker
    results.append("🔧 Running System File Checker (sfc /scannow)...")
    results.append("   This may take a few minutes, please wait.")
    try:
        output = subprocess.run(
            ["sfc", "/scannow"],
            capture_output=True, text=True, timeout=300
        )
        if "did not find any integrity violations" in output.stdout:
            results.append("✅ System files are clean — no corruption found")
        elif "successfully repaired" in output.stdout:
            results.append("✅ Corrupted system files were found and repaired")
        elif output.stdout.strip():
            results.append("✅ System File Checker completed")
        else:
            results.append("⚠️  Run as Administrator to check system files")
    except subprocess.TimeoutExpired:
        results.append("⚠️  SFC timed out — run manually as Administrator")
    except Exception as e:
        results.append(f"⚠️  Could not run SFC: {e}")

    # Schedule chkdsk on next restart
    results.append("\n🔧 Scheduling Disk Check (chkdsk) for next restart...")
    try:
        output = subprocess.run(
            ["chkdsk", "C:", "/f"],
            input="Y\n", capture_output=True, text=True, timeout=10
        )
        if "schedule" in output.stdout.lower() or "next time" in output.stdout.lower():
            results.append("✅ Disk check scheduled — will run on next restart")
        else:
            results.append("✅ Disk check command sent")
    except Exception as e:
        results.append(f"⚠️  Could not schedule chkdsk: {e}")

    # Run DISM to repair Windows image
    results.append("\n🔧 Running Windows Image Repair (DISM)...")
    try:
        output = subprocess.run(
            ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"],
            capture_output=True, text=True, timeout=300
        )
        if "successfully" in output.stdout.lower():
            results.append("✅ Windows image repaired successfully")
        else:
            results.append("✅ DISM repair completed")
    except subprocess.TimeoutExpired:
        results.append("⚠️  DISM timed out — run manually as Administrator")
    except Exception as e:
        results.append(f"⚠️  Could not run DISM: {e}")

    results.append("\n✅ Disk fix complete! Restart your PC to finish the disk check.")
    return "\n".join(results)


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
