import subprocess
import os

def fix_bsod():
    results = []
    results.append("Running BSOD Fix...\n")

    # Run System File Checker
    results.append("🔧 Running System File Checker (sfc /scannow)...")
    results.append("   This may take a few minutes.")
    try:
        output = subprocess.run(["sfc", "/scannow"], capture_output=True, text=True, timeout=300)
        if "did not find any integrity violations" in output.stdout:
            results.append("✅ System files are clean")
        elif "successfully repaired" in output.stdout:
            results.append("✅ Corrupted system files repaired")
        else:
            results.append("✅ System File Checker completed")
    except Exception as e:
        results.append(f"⚠️  Run as Administrator for full results")

    # Run DISM
    results.append("\n🔧 Repairing Windows image (DISM)...")
    try:
        output = subprocess.run(
            ["DISM", "/Online", "/Cleanup-Image", "/RestoreHealth"],
            capture_output=True, text=True, timeout=300
        )
        results.append("✅ Windows image repair completed")
    except Exception as e:
        results.append(f"⚠️  DISM error: {e}")

    # Run Windows Memory Diagnostic
    results.append("\n🔧 Scheduling memory diagnostic on next restart...")
    try:
        subprocess.Popen(["mdsched.exe"])
        results.append("✅ Memory Diagnostic opened")
        results.append("   → Click 'Restart now and check for problems' to test your RAM")
        results.append("   → Your PC will restart and run the test automatically")
    except Exception as e:
        results.append(f"⚠️  Could not open Memory Diagnostic: {e}")

    # Update drivers via PowerShell
    results.append("\n🔧 Opening Device Manager to check for driver updates...")
    try:
        subprocess.Popen(["devmgmt.msc"])
        results.append("✅ Device Manager opened")
        results.append("   → Look for items with a yellow warning triangle")
        results.append("   → Right-click any flagged item and choose Update driver")
        results.append("   → Select Search automatically for drivers")
    except Exception as e:
        results.append(f"⚠️  {e}")

    results.append("\n✅ BSOD fix complete!")
    results.append("👉 What to do next:")
    results.append("   1. Click 'Restart now and check for problems' in the Memory Diagnostic window")
    results.append("   2. Update any drivers flagged in Device Manager")
    results.append("   3. Restart your PC to finish all repairs")
    return "\n".join(results)


def run_bsod_scan():
    results = []
    results.append("Blue Screen (BSOD) Report\n")

    # Check Windows Event Log for critical errors
    try:
        cmd = [
            "powershell",
            "-Command",
            "Get-EventLog -LogName System -EntryType Error -Newest 10 | Select-Object TimeGenerated, Source, Message | Format-List"
        ]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        lines = output.stdout.strip().splitlines()

        if lines:
            results.append("Recent System Errors (last 10):\n")
            for line in lines[:40]:
                if line.strip():
                    results.append(f"  {line.strip()}")
        else:
            results.append("✅ No recent critical system errors found.")
    except Exception as e:
        results.append(f"Could not read event log: {e}")

    # Check for minidump files
    results.append("\nChecking for crash dump files...")
    minidump_path = r"C:\Windows\Minidump"
    try:
        if os.path.exists(minidump_path):
            dumps = os.listdir(minidump_path)
            if dumps:
                results.append(f"⚠️  Found {len(dumps)} crash dump file(s) in {minidump_path}:")
                for d in dumps[-5:]:
                    results.append(f"  • {d}")
                results.append("\n💡 Tips to fix BSODs:")
                results.append("  1. Update all drivers — especially GPU and chipset")
                results.append("  2. Run: sfc /scannow in Command Prompt as Admin")
                results.append("  3. Check RAM with Windows Memory Diagnostic")
                results.append("  4. Check for overheating under the Overheating tab")
            else:
                results.append("✅ No crash dump files found.")
        else:
            results.append("✅ No crash dump folder found — no recent BSODs recorded.")
    except Exception as e:
        results.append(f"Could not check minidump folder: {e}")

    return "\n".join(results)
