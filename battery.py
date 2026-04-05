import psutil
import subprocess

def run_battery_scan():
    results = []
    results.append("Battery & Power Diagnostic\n")

    # Check if battery exists
    battery = psutil.sensors_battery()
    if not battery:
        results.append("No battery detected — this appears to be a desktop PC.")
        results.append("Battery diagnostics only apply to laptops.")
        return "\n".join(results)

    # Battery status
    pct = battery.percent
    plugged = battery.power_plugged
    flag = "✅ OK" if pct > 40 else "⚠️  LOW" if pct > 20 else "🔴 CRITICAL"
    results.append(f"Battery Level   : {round(pct)}%  [{flag}]")
    results.append(f"Power Source    : {'🔌 Plugged In' if plugged else '🔋 On Battery'}")

    if battery.secsleft and battery.secsleft > 0 and not plugged:
        mins = battery.secsleft // 60
        hrs = mins // 60
        mins_rem = mins % 60
        results.append(f"Time Remaining  : {hrs}h {mins_rem}m")

    # Get battery report
    results.append("\nGenerating Battery Report...")
    try:
        report_path = r"C:\GetpcFixed\battery_report.html"
        subprocess.run(
            ["powercfg", "/batteryreport", "/output", report_path],
            capture_output=True, timeout=15
        )
        if __import__('os').path.exists(report_path):
            results.append(f"  ✅ Battery report saved to: {report_path}")
            results.append("  Open this file in your browser for a full history.")
        else:
            results.append("  Could not generate battery report.")
    except Exception as e:
        results.append(f"  Battery report error: {e}")

    # Check power plan
    results.append("\nCurrent Power Plan:")
    try:
        cmd = ["powercfg", "/getactivescheme"]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        line = output.stdout.strip()
        if "Balanced" in line:
            results.append(f"  ✅ {line}")
        elif "Power saver" in line:
            results.append(f"  ⚠️  {line}")
            results.append("  Consider switching to Balanced for better performance.")
        elif "High performance" in line:
            results.append(f"  ⚠️  {line}")
            results.append("  High Performance mode drains battery faster.")
        else:
            results.append(f"  {line}")
    except Exception as e:
        results.append(f"  Could not check power plan: {e}")

    results.append("\n💡 Tips to improve battery life:")
    results.append("  1. Lower your screen brightness")
    results.append("  2. Switch to Balanced power plan")
    results.append("  3. Close apps you are not using")
    results.append("  4. Turn off Bluetooth and WiFi when not needed")
    results.append("  5. Check battery health in the battery report above")

    return "\n".join(results)
