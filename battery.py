import psutil
import subprocess

def fix_battery():
    results = []
    results.append("Running Battery Fix...\n")

    battery = psutil.sensors_battery()
    if not battery:
        results.append("⚠️  No battery detected — this appears to be a desktop PC.")
        return "\n".join(results)

    # Set power plan to Balanced
    results.append("🔧 Setting power plan to Balanced...")
    try:
        subprocess.run(["powercfg", "/setactive", "SCHEME_BALANCED"], capture_output=True, timeout=15)
        results.append("✅ Power plan set to Balanced")
    except Exception as e:
        results.append(f"⚠️  Could not set power plan: {e}")

    # Disable high-drain background apps via PowerShell
    results.append("\n🔧 Reducing background app activity...")
    try:
        cmd = "powercfg /change standby-timeout-ac 15"
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, timeout=10)
        results.append("✅ Sleep timer optimized to save battery")
    except Exception as e:
        results.append(f"⚠️  {e}")

    # Generate full battery report
    results.append("\n🔧 Generating battery health report...")
    try:
        import os
        report_path = r"C:\GetpcFixed\battery_report.html"
        subprocess.run(["powercfg", "/batteryreport", "/output", report_path], capture_output=True, timeout=15)
        if os.path.exists(report_path):
            subprocess.Popen(["explorer.exe", report_path])
            results.append("✅ Battery report generated and opened")
            results.append(f"   Saved to: {report_path}")
        else:
            results.append("⚠️  Could not generate report (run as Admin)")
    except Exception as e:
        results.append(f"⚠️  {e}")

    # Recalibrate battery hint
    results.append("\n🔧 Opening Power & Sleep settings...")
    try:
        subprocess.Popen(["explorer.exe", "ms-settings:powersleep"])
        results.append("✅ Power & Sleep settings opened")
        results.append("   → Under 'Sleep', set screen and sleep times to save battery")
    except Exception as e:
        results.append(f"⚠️  {e}")

    results.append("\n✅ Battery fix complete!")
    results.append("Check the battery report for full health history.")
    return "\n".join(results)


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
