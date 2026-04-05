import subprocess
import os

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
