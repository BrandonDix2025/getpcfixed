import subprocess
import socket

def run_wifi_scan():
    results = []

    # Check internet connectivity
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        results.append("Internet Connection : ✅ Connected")
    except OSError:
        results.append("Internet Connection : ❌ No Connection Detected")

    # Check WiFi profiles
    try:
        output = subprocess.run(
            ["netsh", "wlan", "show", "profiles"],
            capture_output=True, text=True
        )
        profiles = [line.split(":")[1].strip() for line in output.stdout.splitlines() if "All User Profile" in line]
        if profiles:
            results.append(f"\nSaved WiFi Networks ({len(profiles)} found):")
            for p in profiles[:5]:
                results.append(f"  • {p}")
        else:
            results.append("\nNo saved WiFi profiles found.")
    except Exception as e:
        results.append(f"\nCould not read WiFi profiles: {e}")

    # Check current connection
    try:
        output = subprocess.run(
            ["netsh", "wlan", "show", "interfaces"],
            capture_output=True, text=True
        )
        lines = output.stdout.splitlines()
        ssid = next((l.split(":")[1].strip() for l in lines if "SSID" in l and "BSSID" not in l), None)
        signal = next((l.split(":")[1].strip() for l in lines if "Signal" in l), None)
        state = next((l.split(":")[1].strip() for l in lines if "State" in l), None)

        results.append(f"\nCurrent WiFi Status:")
        if state:
            results.append(f"  State   : {state}")
        if ssid:
            results.append(f"  Network : {ssid}")
        if signal:
            results.append(f"  Signal  : {signal}")
        if not ssid:
            results.append("  Not connected to any WiFi network.")
            results.append("\n💡 Tips to fix WiFi:")
            results.append("  1. Toggle Airplane mode on then off")
            results.append("  2. Forget the network and reconnect")
            results.append("  3. Run: netsh winsock reset (then restart)")
            results.append("  4. Update your WiFi adapter driver")
    except Exception as e:
        results.append(f"\nCould not check WiFi status: {e}")

    return "\n".join(results)
