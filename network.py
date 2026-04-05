import psutil
import socket
import subprocess
import speedtest
import platform

def get_connection_type():
    stats = psutil.net_if_stats()
    addrs = psutil.net_if_addrs()
    for iface, stat in stats.items():
        if stat.isup:
            iface_lower = iface.lower()
            if any(x in iface_lower for x in ["wi-fi", "wifi", "wireless", "wlan"]):
                return "WiFi", iface
            elif any(x in iface_lower for x in ["ethernet", "eth", "local area"]):
                return "Wired (Ethernet)", iface
    return "Unknown", "Unknown"

def check_internet():
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def ping_test():
    try:
        param = "-n" if platform.system().lower() == "windows" else "-c"
        result = subprocess.run(
            ["ping", param, "4", "8.8.8.8"],
            capture_output=True, text=True
        )
        lines = result.stdout.splitlines()
        for line in lines:
            if "Average" in line or "avg" in line:
                return line.strip()
        return "Ping complete"
    except Exception as e:
        return f"Ping failed: {e}"

def speed_test():
    try:
        st = speedtest.Speedtest()
        st.get_best_server()
        download = st.download() / 1_000_000
        upload = st.upload() / 1_000_000
        return round(download, 2), round(upload, 2)
    except Exception as e:
        return None, None

def check_dns():
    try:
        socket.gethostbyname("google.com")
        return True
    except socket.gaierror:
        return False

def check_gateway():
    try:
        gateways = psutil.net_if_addrs()
        result = subprocess.run(
            ["ping", "-n", "2", "192.168.1.1"],
            capture_output=True, text=True
        )
        if "TTL" in result.stdout:
            return True
        return False
    except:
        return False

def run_network_scan():
    print("\n--- Network Diagnostic ---\n")

    conn_type, iface = get_connection_type()
    print(f"Connection Type : {conn_type} ({iface})")

    internet = check_internet()
    print(f"Internet        : {'✅ Connected' if internet else '❌ No Connection'}")

    dns = check_dns()
    print(f"DNS             : {'✅ Working' if dns else '❌ Failed'}")

    gateway = check_gateway()
    print(f"Gateway         : {'✅ Reachable' if gateway else '❌ Not Reachable'}")

    ping = ping_test()
    print(f"Ping            : {ping}")

    print("\nRunning speed test — this takes 15-20 seconds...")
    download, upload = speed_test()
    if download:
        print(f"Download Speed  : {download} Mbps")
        print(f"Upload Speed    : {upload} Mbps")
    else:
        print("Speed Test      : Failed to complete")

    print("\n--- Scan Complete ---\n")

if __name__ == "__main__":
    run_network_scan()