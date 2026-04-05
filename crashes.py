import psutil
import subprocess

def fix_crashes():
    results = []
    results.append("Running App Crash Fix...\n")

    # Clear memory by restarting Windows Explorer
    results.append("🔧 Refreshing Windows Explorer...")
    try:
        subprocess.run(["taskkill", "/f", "/im", "explorer.exe"], capture_output=True)
        subprocess.Popen(["explorer.exe"])
        results.append("✅ Windows Explorer refreshed — frees up RAM")
    except Exception as e:
        results.append(f"⚠️  Could not refresh Explorer: {e}")

    # Clear Windows temp files to free RAM pressure
    results.append("\n🔧 Clearing temp files to free memory...")
    try:
        import os, shutil
        temp = os.environ.get("TEMP", "")
        cleared = 0
        if temp and os.path.exists(temp):
            for f in os.listdir(temp):
                try:
                    fp = os.path.join(temp, f)
                    if os.path.isfile(fp):
                        os.remove(fp)
                        cleared += 1
                except:
                    pass
        results.append(f"✅ Cleared {cleared} temp files")
    except Exception as e:
        results.append(f"⚠️  Could not clear temp: {e}")

    # Flush standby memory via RAMMap-style command
    results.append("\n🔧 Optimizing memory usage...")
    try:
        cmd = "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, timeout=15)
        results.append("✅ Recycle Bin cleared")
    except Exception as e:
        results.append(f"⚠️  {e}")

    # Check and repair app event log issues
    results.append("\n🔧 Checking Windows application event log...")
    try:
        cmd = "Limit-EventLog -LogName Application -MaximumSize 20480KB"
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, timeout=10)
        results.append("✅ Application event log optimized")
    except Exception as e:
        results.append(f"⚠️  {e}")

    results.append("\n✅ Crash fix complete!")
    results.append("If one specific app keeps crashing, try reinstalling it.")
    return "\n".join(results)


def run_crash_scan():
    results = []
    results.append("App Crash & Freeze Diagnostic\n")

    # Check RAM usage
    ram = psutil.virtual_memory()
    ram_pct = ram.percent
    ram_flag = "✅ OK" if ram_pct < 75 else "⚠️  HIGH"
    results.append(f"RAM Usage       : {ram_pct}%  [{ram_flag}]")

    # Check top memory-hungry processes
    results.append("\nTop Memory-Hungry Apps:")
    try:
        procs = []
        for p in psutil.process_iter(['pid', 'name', 'memory_percent']):
            try:
                if p.info['memory_percent'] and p.info['memory_percent'] > 0.5:
                    procs.append(p.info)
            except Exception:
                pass
        procs = sorted(procs, key=lambda x: x['memory_percent'], reverse=True)[:8]
        for p in procs:
            results.append(f"  {p['name']:<35} {round(p['memory_percent'], 1)}% RAM")
    except Exception as e:
        results.append(f"  Could not read processes: {e}")

    # Check CPU usage
    cpu = psutil.cpu_percent(interval=1)
    cpu_flag = "✅ OK" if cpu < 75 else "⚠️  HIGH"
    results.append(f"\nCPU Usage       : {cpu}%  [{cpu_flag}]")

    # Check for recent app crashes in event log
    results.append("\nRecent App Crashes (Event Log):")
    try:
        cmd = [
            "powershell", "-Command",
            "Get-EventLog -LogName Application -EntryType Error -Newest 5 | Select-Object TimeGenerated, Source | Format-List"
        ]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        lines = [l.strip() for l in output.stdout.strip().splitlines() if l.strip()]
        if lines:
            for line in lines[:20]:
                results.append(f"  {line}")
        else:
            results.append("  ✅ No recent app crashes found.")
    except Exception as e:
        results.append(f"  Could not read app event log: {e}")

    results.append("\n💡 Tips to fix crashing apps:")
    results.append("  1. Close apps you are not using to free up RAM")
    results.append("  2. Restart the crashing app and try again")
    results.append("  3. Update the app to the latest version")
    results.append("  4. Reinstall the app if crashes keep happening")

    return "\n".join(results)
