import psutil
import subprocess

def fix_temps():
    results = []
    results.append("Running Overheating Fix...\n")

    # Set power plan to Balanced to reduce heat
    results.append("🔧 Setting power plan to Balanced...")
    try:
        cmd = "powercfg /setactive SCHEME_BALANCED"
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, timeout=15)
        results.append("✅ Power plan set to Balanced — reduces heat and battery drain")
    except Exception as e:
        results.append(f"⚠️  Could not change power plan: {e}")

    # Kill top CPU-hungry background processes (safe ones only)
    results.append("\n🔧 Checking for high-CPU background processes...")
    try:
        killed = []
        safe_to_kill = ["SearchIndexer.exe", "MsMpEng.exe"]
        for p in psutil.process_iter(['pid', 'name', 'cpu_percent']):
            try:
                cpu = p.cpu_percent(interval=0.2)
                if cpu > 50 and p.info['name'] in safe_to_kill:
                    p.kill()
                    killed.append(p.info['name'])
            except Exception:
                pass
        if killed:
            results.append(f"✅ Stopped high-CPU processes: {', '.join(killed)}")
        else:
            results.append("✅ No runaway processes found")
    except Exception as e:
        results.append(f"⚠️  Could not check processes: {e}")

    # Disable unnecessary visual effects to reduce CPU load
    results.append("\n🔧 Optimizing Windows visual effects for performance...")
    try:
        cmd = "SystemPropertiesPerformance.exe"
        subprocess.Popen(cmd)
        results.append("✅ Performance Options opened — select 'Adjust for best performance'")
        results.append("   → Select 'Adjust for best performance' then click Apply, then OK")
    except Exception as e:
        results.append(f"⚠️  Could not open Performance Options: {e}")

    results.append("\n✅ Overheating fix complete!")
    results.append("⚠️  Physical fixes: clean dust from vents, ensure airflow around PC.")
    return "\n".join(results)


def run_temp_scan():
    results = []
    results.append("Overheating & Temperature Check\n")

    # CPU usage as heat indicator
    cpu = psutil.cpu_percent(interval=1)
    cpu_flag = "✅ OK" if cpu < 60 else "⚠️  WARM" if cpu < 85 else "🔥 HOT"
    results.append(f"CPU Usage       : {cpu}%  [{cpu_flag}]")

    # Try to get temps via psutil
    results.append("\nTemperature Readings:")
    try:
        temps = psutil.sensors_temperatures()
        if temps:
            for chip, entries in temps.items():
                for entry in entries:
                    label = entry.label or chip
                    temp = entry.current
                    flag = "✅ OK" if temp < 70 else "⚠️  WARM" if temp < 85 else "🔥 HOT"
                    results.append(f"  {label:<25} {temp}°C  [{flag}]")
        else:
            results.append("  Temperature sensors not available via standard API.")
            results.append("  Trying alternate method...")
            raise Exception("No sensors")
    except Exception:
        # Try WMI for temps
        try:
            cmd = [
                "powershell", "-Command",
                "Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace root/wmi | Select-Object CurrentTemperature | Format-List"
            ]
            output = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
            lines = [l.strip() for l in output.stdout.strip().splitlines() if "CurrentTemperature" in l]
            if lines:
                for line in lines:
                    raw = line.split(":")[1].strip()
                    celsius = (int(raw) / 10) - 273.15
                    flag = "✅ OK" if celsius < 70 else "⚠️  WARM" if celsius < 85 else "🔥 HOT"
                    results.append(f"  Thermal Zone : {round(celsius, 1)}°C  [{flag}]")
            else:
                results.append("  ⚠️  Could not read hardware temps on this system.")
                results.append("  Consider using HWMonitor for detailed temperature readings.")
        except Exception as e:
            results.append(f"  Could not read temps: {e}")

    # Fan info
    results.append("\nFan Status:")
    try:
        fans = psutil.sensors_fans()
        if fans:
            for name, entries in fans.items():
                for entry in entries:
                    results.append(f"  {entry.label or name:<25} {entry.current} RPM")
        else:
            results.append("  Fan sensor data not available on this system.")
    except Exception:
        results.append("  Fan sensor data not available on this system.")

    results.append("\n💡 Tips to prevent overheating:")
    results.append("  1. Clean dust from vents and fans every 6 months")
    results.append("  2. Make sure your PC has breathing room — don't block vents")
    results.append("  3. Use your laptop on a hard flat surface, not on a bed")
    results.append("  4. Consider a laptop cooling pad if temps stay high")

    return "\n".join(results)
