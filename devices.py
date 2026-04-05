import subprocess

def run_devices_scan():
    results = []
    results.append("Printer, USB & Device Diagnostic\n")

    # Check for problem devices
    results.append("Devices with Issues:")
    try:
        cmd = [
            "powershell", "-Command",
            "Get-PnpDevice | Where-Object { $_.Status -ne 'OK' } | Select-Object Status, Class, FriendlyName | Format-List"
        ]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        lines = [l.strip() for l in output.stdout.strip().splitlines() if l.strip()]
        if lines:
            results.append("  ⚠️  Problem devices found:")
            for line in lines[:30]:
                results.append(f"    {line}")
        else:
            results.append("  ✅ All devices are working correctly.")
    except Exception as e:
        results.append(f"  Could not check devices: {e}")

    # Check connected USB devices
    results.append("\nConnected USB Devices:")
    try:
        cmd = [
            "powershell", "-Command",
            "Get-PnpDevice -Class USB | Where-Object { $_.Status -eq 'OK' } | Select-Object FriendlyName | Format-List"
        ]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        lines = [l.strip() for l in output.stdout.strip().splitlines() if "FriendlyName" in l]
        if lines:
            for line in lines[:10]:
                name = line.split(":", 1)[1].strip() if ":" in line else line
                if name:
                    results.append(f"  • {name}")
        else:
            results.append("  No USB devices detected.")
    except Exception as e:
        results.append(f"  Could not list USB devices: {e}")

    # Check printers
    results.append("\nInstalled Printers:")
    try:
        cmd = [
            "powershell", "-Command",
            "Get-Printer | Select-Object Name, PrinterStatus, DriverName | Format-List"
        ]
        output = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
        lines = [l.strip() for l in output.stdout.strip().splitlines() if l.strip()]
        if lines:
            for line in lines[:20]:
                results.append(f"  {line}")
        else:
            results.append("  No printers found.")
    except Exception as e:
        results.append(f"  Could not check printers: {e}")

    results.append("\n💡 Tips to fix device problems:")
    results.append("  1. Unplug and replug the USB device")
    results.append("  2. Try a different USB port")
    results.append("  3. Update the device driver in Device Manager")
    results.append("  4. For printers: delete and reinstall the printer")
    results.append("  5. Restart the Print Spooler service for printer issues")

    return "\n".join(results)
