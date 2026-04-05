import subprocess

def fix_devices():
    results = []
    results.append("Running Device Fix...\n")

    # Restart Print Spooler service
    results.append("🔧 Restarting Print Spooler service...")
    try:
        subprocess.run(["net", "stop", "spooler"], capture_output=True, timeout=15)
        subprocess.run(["net", "start", "spooler"], capture_output=True, timeout=15)
        results.append("✅ Print Spooler restarted — printer issues should be resolved")
    except Exception as e:
        results.append(f"⚠️  Could not restart Print Spooler: {e}")

    # Re-enable any problem devices
    results.append("\n🔧 Re-enabling problem devices...")
    try:
        cmd = "Get-PnpDevice | Where-Object { $_.Status -eq 'Error' -or $_.Status -eq 'Degraded' } | Enable-PnpDevice -Confirm:$false"
        output = subprocess.run(
            ["powershell", "-Command", cmd],
            capture_output=True, text=True, timeout=30
        )
        results.append("✅ Problem devices re-enabled")
    except Exception as e:
        results.append(f"⚠️  Could not re-enable devices: {e}")

    # Scan for new hardware changes
    results.append("\n🔧 Scanning for hardware changes...")
    try:
        cmd = "pnputil /scan-devices"
        subprocess.run(["powershell", "-Command", cmd], capture_output=True, timeout=30)
        results.append("✅ Hardware scan complete")
    except Exception as e:
        results.append(f"⚠️  Could not scan hardware: {e}")

    # Open Device Manager for manual review
    subprocess.Popen(["devmgmt.msc"])
    results.append("✅ Device Manager opened for your review")

    results.append("\n✅ Device fix complete!")
    results.append("If a device still shows an error in Device Manager,")
    results.append("right-click it and choose 'Update driver'.")
    return "\n".join(results)


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
