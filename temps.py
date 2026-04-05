import psutil
import subprocess

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
