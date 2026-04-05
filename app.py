import sys
import os
import anthropic
from dotenv import load_dotenv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QLabel, QTextEdit, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from scanner import scan_system_data
from diagnose import diagnose as run_diagnosis
from cleaner import scan_junk, clean_junk_silent
from startup import get_startup_programs
from logger import log_event, load_log
from network import get_connection_type, check_internet, check_dns, check_gateway, ping_test, speed_test, fix_network
from wifi import run_wifi_scan
from bsod import run_bsod_scan, fix_bsod
from crashes import run_crash_scan, fix_crashes
from malware import run_malware_scan, fix_malware
from temps import run_temp_scan, fix_temps
from updates import run_updates_scan, fix_updates
from devices import run_devices_scan, fix_devices
from diskhealth import run_diskhealth_scan, fix_disk
from battery import run_battery_scan, fix_battery
from monitor import start_monitor, stop_monitor, is_running, set_notify_callback

# Find .env whether running as .exe or as Python script
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

load_dotenv(os.path.join(BASE_DIR, '.env'))


class WorkerThread(QThread):
    result = pyqtSignal(str)

    def __init__(self, task):
        super().__init__()
        self.task = task

    def run(self):
        if self.task == "scan":
            data = scan_system_data()
            cpu = data['cpu']
            ram_used = data['ram_used']
            ram_total = data['ram_total']
            disk_used = data['disk_used']
            disk_total = data['disk_total']
            ram_pct = round((ram_used / ram_total) * 100)
            disk_pct = round((disk_used / disk_total) * 100)
            cpu_flag = "OK" if cpu < 50 else "WARN" if cpu < 80 else "HIGH"
            ram_flag = "OK" if ram_pct < 50 else "WARN" if ram_pct < 80 else "HIGH"
            disk_flag = "OK" if disk_pct < 70 else "WARN" if disk_pct < 90 else "HIGH"
            result = (
                f"CPU Usage:     {cpu}%  [{cpu_flag}]\n"
                f"RAM Usage:     {ram_used} GB of {ram_total} GB  [{ram_flag}]\n"
                f"Disk Usage:    {disk_used} GB of {disk_total} GB  [{disk_flag}]\n"
                f"System:        {data['system']}\n"
                f"Machine:       {data['machine']}"
            )
            log_event("Scan", f"CPU: {cpu}% | RAM: {ram_used}GB | Disk: {disk_used}GB")
            self.result.emit(result)

        elif self.task == "diagnose":
            result = run_diagnosis()
            self.result.emit(result)

        elif self.task == "junk":
            total_files, size_mb = scan_junk()
            self.result.emit(f"Found {total_files} junk files taking up {size_mb} MB.\nClick Clean Now to free up this space.")

        elif self.task == "clean":
            cleaned, size_mb = clean_junk_silent()
            log_event("Junk Clean", f"Cleaned {cleaned} files and freed up {size_mb} MB")
            self.result.emit(f"Done! Cleaned {cleaned} junk files and freed up {size_mb} MB.")

        elif self.task == "network":
            conn_type, iface = get_connection_type()
            internet = check_internet()
            dns = check_dns()
            gateway = check_gateway()
            ping = ping_test()
            result = (
                f"Connection Type : {conn_type} ({iface})\n"
                f"Internet        : {'✅ Connected' if internet else '❌ No Connection'}\n"
                f"DNS             : {'✅ Working' if dns else '❌ Failed'}\n"
                f"Gateway         : {'✅ Reachable' if gateway else '❌ Not Reachable'}\n"
                f"Ping            : {ping}\n\n"
                f"Running speed test — this takes 15-20 seconds...\n"
            )
            self.result.emit(result)
            download, upload = speed_test()
            if download:
                result += f"Download Speed  : {download} Mbps\nUpload Speed    : {upload} Mbps"
            else:
                result += "Speed Test      : Failed to complete"
            self.result.emit(result)

        elif self.task == "wifi":
            self.result.emit(run_wifi_scan())

        elif self.task == "bsod":
            self.result.emit(run_bsod_scan())

        elif self.task == "crashes":
            self.result.emit(run_crash_scan())

        elif self.task == "malware":
            self.result.emit(run_malware_scan())

        elif self.task == "temps":
            self.result.emit(run_temp_scan())

        elif self.task == "updates":
            self.result.emit(run_updates_scan())

        elif self.task == "devices":
            self.result.emit(run_devices_scan())

        elif self.task == "diskhealth":
            self.result.emit(run_diskhealth_scan())

        elif self.task == "battery":
            self.result.emit(run_battery_scan())

        elif self.task == "fix_updates":
            self.result.emit(fix_updates())

        elif self.task == "fix_disk":
            self.result.emit(fix_disk())

        elif self.task == "fix_devices":
            self.result.emit(fix_devices())

        elif self.task == "fix_network":
            self.result.emit(fix_network())

        elif self.task == "fix_malware":
            self.result.emit(fix_malware())

        elif self.task == "fix_temps":
            self.result.emit(fix_temps())

        elif self.task == "fix_bsod":
            self.result.emit(fix_bsod())

        elif self.task == "fix_crashes":
            self.result.emit(fix_crashes())

        elif self.task == "fix_battery":
            self.result.emit(fix_battery())

        elif self.task == "history":
            entries = load_log()
            if not entries:
                self.result.emit("No history yet. Run a scan first!")
            else:
                lines = []
                for e in entries:
                    lines.append(f"[{e['date']} {e['time']}] {e['type']}")
                    lines.append(f"   {e['details']}\n")
                self.result.emit("\n".join(lines))


class AskWorkerThread(QThread):
    result = pyqtSignal(str)

    def __init__(self, user_question):
        super().__init__()
        self.user_question = user_question

    def run(self):
        try:
            data = scan_system_data()
            prompt = f"""
You are GetPCFixed — a friendly, plain-English PC repair expert.

The user described their problem as:
"{self.user_question}"

Here is their current PC health data:
- CPU Usage: {data['cpu']}%
- RAM Used: {data['ram_used']} GB of {data['ram_total']} GB
- Disk Used: {data['disk_used']} GB of {data['disk_total']} GB
- System: {data['system']}
- Machine: {data['machine']}

Based on their problem and their PC data:
1. Tell them in plain English what you think is wrong
2. Tell them exactly what you would do to fix it
3. If it is something the app can fix, end with: "Want me to fix this for you?"
4. If it requires physical repair, new hardware, or something outside of software, tell them honestly. Say something like: "This one is outside what software can fix. Here’s what I’d suggest next: [specific advice]. If none of that works, it may be time to have a technician look at it or consider a replacement."
5. Always end with a clear next step — never leave the customer with no direction.

Keep it friendly, simple, and short. No technical jargon. Talk like a helpful neighbor, not a manual.
"""
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=1024,
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.content[0].text
            log_event("Ask GetPCFixed", f"User asked: {self.user_question[:60]}")
            self.result.emit(result)
        except Exception as e:
            self.result.emit(f"Something went wrong: {e}")


class FixDecisionThread(QThread):
    decision = pyqtSignal(str)

    def __init__(self, user_question, diagnosis):
        super().__init__()
        self.user_question = user_question
        self.diagnosis = diagnosis

    def run(self):
        try:
            prompt = f"""
The user described their PC problem as:
"{self.user_question}"

The diagnosis was:
"{self.diagnosis}"

Based on this, which ONE fix should be run?
Reply with ONLY one of these exact words, nothing else:
- clean       (if junk files, disk space, or slow PC is the issue)
- startup     (if too many startup programs or slow boot is the issue)
- network     (if internet, WiFi, or connection is the issue)
- scan        (if the problem is unclear or general performance)

Reply with only the single word.
"""
            client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
            response = client.messages.create(
                model="claude-opus-4-5",
                max_tokens=10,
                messages=[{"role": "user", "content": prompt}]
            )
            decision = response.content[0].text.strip().lower()
            if decision not in ["clean", "startup", "network", "scan"]:
                decision = "scan"
            self.decision.emit(decision)
        except Exception as e:
            self.decision.emit("scan")


class DashboardThread(QThread):
    result = pyqtSignal(dict)

    def run(self):
        data = scan_system_data()
        self.result.emit(data)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GetPCFixed")
        self.setMinimumSize(700, 500)
        self.last_diagnosis = ""
        self.last_question = ""
        self.active_btn = None
        self.all_btns = []
        self.ask_btn = None
        self.repair_task = None
        self.setStyleSheet("""
            QMainWindow { background-color: #0d1117; }
            QWidget { background-color: #0d1117; color: #e6edf3; }
            QPushButton {
                background-color: #1f2937;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2563eb; border: 1px solid #2563eb; }
            QPushButton:pressed { background-color: #1d4ed8; }
            QTextEdit {
                background-color: #161b22;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 12px;
                font-size: 13px;
            }
        """)
        self.build_ui()
        self.show_dashboard()
        # Start Keep Me Running background monitor
        set_notify_callback(self.on_monitor_alert)
        start_monitor()

    def build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)

        sidebar = QFrame()
        sidebar.setFixedWidth(200)
        sidebar.setStyleSheet("QFrame { border: 1px solid #30363d; border-radius: 8px; }")
        sidebar_layout = QVBoxLayout(sidebar)
        sidebar_layout.setContentsMargins(12, 20, 12, 20)
        sidebar_layout.setSpacing(10)

        logo = QLabel("GetPCFixed")
        logo.setFont(QFont("Segoe UI", 14, QFont.Bold))
        logo.setStyleSheet("color: #2563eb; border: none;")
        logo.setAlignment(Qt.AlignCenter)
        sidebar_layout.addWidget(logo)

        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("color: #30363d;")
        sidebar_layout.addWidget(line)
        sidebar_layout.addSpacing(10)

        ask_btn = QPushButton("💬 Ask GetPCFixed")
        ask_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: white;
                border: 1px solid #16a34a;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #15803d; }
        """)
        self.ask_btn = ask_btn
        self.all_btns.append(ask_btn)
        ask_btn.clicked.connect(lambda: (self.set_active_btn(self.ask_btn), self.show_ask()))
        sidebar_layout.addWidget(ask_btn)
        sidebar_layout.addSpacing(6)

        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll_area.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: #161b22; width: 6px; border-radius: 3px; }
            QScrollBar::handle:vertical { background: #30363d; border-radius: 3px; min-height: 20px; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0px; }
        """)

        scroll_widget = QWidget()
        scroll_widget.setStyleSheet("background: transparent;")
        scroll_layout = QVBoxLayout(scroll_widget)
        scroll_layout.setContentsMargins(0, 0, 4, 0)
        scroll_layout.setSpacing(4)

        groups = [
            ("⚡ Quick Actions", [
                ("Scan My PC", "scan"),
                ("AI Diagnosis", "diagnose"),
            ]),
            ("🧹 Performance", [
                ("Clean Junk Files", "junk"),
                ("Fix Startup", "startup"),
                ("Overheating", "temps"),
            ]),
            ("🌐 Connectivity", [
                ("Network Diagnostic", "network"),
                ("WiFi Issues", "wifi"),
            ]),
            ("🛡️ Health & Safety", [
                ("Malware Check", "malware"),
                ("Windows Updates", "updates"),
                ("Disk Health", "diskhealth"),
                ("Devices & USB", "devices"),
            ]),
            ("🚨 Problems", [
                ("Blue Screen (BSOD)", "bsod"),
                ("App Crashes", "crashes"),
                ("Battery", "battery"),
            ]),
            ("📋 More", [
                ("View History", "history"),
                ("About", "about"),
            ]),
        ]

        for group_label, buttons in groups:
            header = QPushButton(f"▶  {group_label}")
            header.setStyleSheet("""
                QPushButton {
                    background-color: #161b22;
                    color: #8b949e;
                    border: none;
                    border-radius: 4px;
                    padding: 6px 8px;
                    font-size: 11px;
                    font-weight: bold;
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #1f2937;
                    color: #e6edf3;
                }
            """)
            scroll_layout.addWidget(header)

            child_buttons = []
            for label, task in buttons:
                btn = QPushButton(label)
                btn.hide()
                btn.clicked.connect(lambda checked, t=task, b=btn: (self.set_active_btn(b), self.run_task(t)))
                self.all_btns.append(btn)
                scroll_layout.addWidget(btn)
                child_buttons.append(btn)

            header.clicked.connect(lambda checked, h=header, children=child_buttons, gl=group_label: self.toggle_group(h, children, gl))

        scroll_layout.addStretch()
        scroll_area.setWidget(scroll_widget)
        sidebar_layout.addWidget(scroll_area)

        self.status = QLabel("Ready")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: #8b949e; font-size: 12px; border: none;")
        sidebar_layout.addWidget(self.status)

        self.monitor_btn = QPushButton("🟢  Keep Me Running: ON")
        self.monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: #16a34a;
                color: white;
                border: 1px solid #16a34a;
                border-radius: 6px;
                padding: 8px;
                font-size: 11px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #15803d; }
        """)
        self.monitor_btn.clicked.connect(self.toggle_monitor)
        sidebar_layout.addWidget(self.monitor_btn)

        main_layout.addWidget(sidebar)

        content = QFrame()
        content.setStyleSheet("QFrame { border: 1px solid #30363d; border-radius: 8px; }")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(16, 16, 16, 16)

        self.title = QLabel("Welcome to GetPCFixed")
        self.title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title.setStyleSheet("color: #e6edf3; border: none;")
        self.content_layout.addWidget(self.title)

        self.repair_btn = QPushButton("🔧 Fix It")
        self.repair_btn.setStyleSheet("background-color: #dc2626; color: white; font-size: 14px; padding: 10px; border-radius: 6px; font-weight: bold;")
        self.repair_btn.clicked.connect(self.run_repair)
        self.repair_btn.hide()
        self.content_layout.addWidget(self.repair_btn)

        self.clean_btn = QPushButton("Clean Now")
        self.clean_btn.setStyleSheet("background-color: #16a34a; color: white; font-size: 14px; padding: 10px; border-radius: 6px;")
        self.clean_btn.clicked.connect(lambda: self.run_task("clean"))
        self.clean_btn.hide()
        self.content_layout.addWidget(self.clean_btn)

        self.ask_input = QTextEdit()
        self.ask_input.setPlaceholderText("Describe your problem here... (e.g. My computer is really slow when I open Chrome)")
        self.ask_input.setMaximumHeight(100)
        self.ask_input.hide()
        self.content_layout.addWidget(self.ask_input)

        self.ask_hint = QLabel("If we find a solution, we'll let you know.")
        self.ask_hint.setStyleSheet("color: #8b949e; font-size: 12px; border: none; padding: 2px 0px;")
        self.ask_hint.hide()
        self.content_layout.addWidget(self.ask_hint)

        self.ask_now_btn = QPushButton("Ask Now")
        self.ask_now_btn.setStyleSheet("background-color: #2563eb; color: white; font-size: 14px; padding: 10px; border-radius: 6px;")
        self.ask_now_btn.clicked.connect(self.run_ask)
        self.ask_now_btn.hide()
        self.content_layout.addWidget(self.ask_now_btn)

        self.fix_btn = QPushButton("✅ Yes, Fix It!")
        self.fix_btn.setStyleSheet("background-color: #16a34a; color: white; font-size: 14px; padding: 10px; border-radius: 6px;")
        self.fix_btn.clicked.connect(self.run_fix)
        self.fix_btn.hide()
        self.content_layout.addWidget(self.fix_btn)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setText("Loading dashboard...")
        self.content_layout.addWidget(self.output)

        main_layout.addWidget(content)

    def run_repair(self):
        self.repair_btn.hide()
        self.status.setText("Fixing...")
        self.output.setText("Running fix — please wait, this may take a minute...")
        self.worker = WorkerThread(self.repair_task)
        self.worker.result.connect(self.show_result)
        self.worker.start()

    def show_dashboard(self):
        self.title.setText("PC Health Dashboard")
        self.clean_btn.hide()
        self.fix_btn.hide()
        self.ask_input.hide()
        self.ask_hint.hide()
        self.ask_now_btn.hide()
        self.output.setText("Scanning your PC...")
        self.status.setText("Scanning...")
        self.dash_worker = DashboardThread()
        self.dash_worker.result.connect(self.render_dashboard)
        self.dash_worker.start()

    def render_dashboard(self, data):
        cpu = data['cpu']
        ram_used = data['ram_used']
        ram_total = data['ram_total']
        disk_used = data['disk_used']
        disk_total = data['disk_total']
        ram_pct = round((ram_used / ram_total) * 100)
        disk_pct = round((disk_used / disk_total) * 100)

        issues = 0
        if cpu >= 80: issues += 2
        elif cpu >= 50: issues += 1
        if ram_pct >= 80: issues += 2
        elif ram_pct >= 50: issues += 1
        if disk_pct >= 90: issues += 2
        elif disk_pct >= 70: issues += 1

        score = max(0, 100 - (issues * 15))

        if score >= 80:
            score_color = "#22c55e"
            status_msg = "Your PC looks healthy! ✅"
        elif score >= 50:
            score_color = "#f59e0b"
            status_msg = "Your PC has a few things to check. ⚠️"
        else:
            score_color = "#ef4444"
            status_msg = "Your PC needs attention! 🚨"

        cpu_color = "#22c55e" if cpu < 50 else "#f59e0b" if cpu < 80 else "#ef4444"
        ram_color = "#22c55e" if ram_pct < 50 else "#f59e0b" if ram_pct < 80 else "#ef4444"
        disk_color = "#22c55e" if disk_pct < 70 else "#f59e0b" if disk_pct < 90 else "#ef4444"

        def bar(pct, color):
            filled = max(1, int(pct))
            empty = max(0, 100 - filled)
            return f"<table width='100%' cellspacing='0' cellpadding='0' style='margin:4px 0 14px 0;'><tr><td width='{filled}%' style='background:{color}; height:10px; border-radius:4px;'></td><td width='{empty}%' style='background:#1f2937; height:10px;'></td></tr></table>"

        html = f"""
        <div style='font-family: Segoe UI; color: #e6edf3; padding: 10px;'>

            <div style='text-align: center; padding: 20px 0 14px 0;'>
                <div style='font-size: 64px; font-weight: bold; color: {score_color};'>{score}</div>
                <div style='font-size: 12px; color: #8b949e; margin-top: 2px;'>PC HEALTH SCORE</div>
                <div style='font-size: 15px; font-weight: bold; color: {score_color}; margin-top: 10px;'>{status_msg}</div>
            </div>

            <hr style='border: none; border-top: 1px solid #30363d; margin: 16px 0;'>

            <div style='padding: 0 6px;'>

                <table width='100%' cellspacing='0' cellpadding='0' style='margin-bottom:2px;'>
                    <tr>
                        <td style='color:#8b949e; font-size:12px;'>💻 CPU Usage</td>
                        <td align='right' style='color:{cpu_color}; font-size:12px; font-weight:bold;'>{cpu}%</td>
                    </tr>
                </table>
                {bar(cpu, cpu_color)}

                <table width='100%' cellspacing='0' cellpadding='0' style='margin-bottom:2px;'>
                    <tr>
                        <td style='color:#8b949e; font-size:12px;'>🧠 RAM Usage</td>
                        <td align='right' style='color:{ram_color}; font-size:12px; font-weight:bold;'>{ram_used} GB / {ram_total} GB ({ram_pct}%)</td>
                    </tr>
                </table>
                {bar(ram_pct, ram_color)}

                <table width='100%' cellspacing='0' cellpadding='0' style='margin-bottom:2px;'>
                    <tr>
                        <td style='color:#8b949e; font-size:12px;'>💾 Disk Usage</td>
                        <td align='right' style='color:{disk_color}; font-size:12px; font-weight:bold;'>{disk_used} GB / {disk_total} GB ({disk_pct}%)</td>
                    </tr>
                </table>
                {bar(disk_pct, disk_color)}

            </div>

            <hr style='border: none; border-top: 1px solid #30363d; margin: 16px 0;'>

            <div style='padding: 0 6px; color: #6b7280; font-size: 11px; line-height: 1.8;'>
                <span style='color:#8b949e;'>System:</span> &nbsp;{data['system']}<br>
                <span style='color:#8b949e;'>Machine:</span> &nbsp;{data['machine']}
            </div>

        </div>
        """
        self.output.setHtml(html)
        self.title.setText("PC Health Dashboard")
        self.status.setText("Live")
        log_event("Dashboard", f"Score: {score} | CPU: {cpu}% | RAM: {ram_pct}% | Disk: {disk_pct}%")

    def toggle_monitor(self):
        if is_running():
            stop_monitor()
            self.monitor_btn.setText("🔴  Keep Me Running: OFF")
            self.monitor_btn.setStyleSheet("""
                QPushButton {
                    background-color: #374151;
                    color: #9ca3af;
                    border: 1px solid #374151;
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #4b5563; }
            """)
        else:
            start_monitor()
            self.monitor_btn.setText("🟢  Keep Me Running: ON")
            self.monitor_btn.setStyleSheet("""
                QPushButton {
                    background-color: #16a34a;
                    color: white;
                    border: 1px solid #16a34a;
                    border-radius: 6px;
                    padding: 8px;
                    font-size: 11px;
                    font-weight: bold;
                }
                QPushButton:hover { background-color: #15803d; }
            """)

    def on_monitor_alert(self, title, message):
        """Called by monitor when an alert fires — updates status bar."""
        self.status.setText(f"⚠️ {message[:40]}...")

    def toggle_group(self, header, children, group_label):
        if children[0].isVisible():
            for btn in children:
                btn.hide()
            header.setText(f"▶  {group_label}")
        else:
            for btn in children:
                btn.show()
            header.setText(f"▼  {group_label}")

    def set_active_btn(self, btn):
        default_style = """
            QPushButton {
                background-color: #1f2937;
                color: #e6edf3;
                border: 1px solid #30363d;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #2563eb; border: 1px solid #2563eb; }
        """
        ask_style = """
            QPushButton {
                background-color: #16a34a;
                color: white;
                border: 1px solid #16a34a;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #15803d; }
        """
        active_style = """
            QPushButton {
                background-color: #2563eb;
                color: white;
                border: 1px solid #2563eb;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
        """
        for b in self.all_btns:
            if b == self.ask_btn:
                b.setStyleSheet(ask_style)
            else:
                b.setStyleSheet(default_style)
        btn.setStyleSheet(active_style)
        self.active_btn = btn

    def show_ask(self):
        self.title.setText("💬 Ask GetPCFixed")
        self.clean_btn.hide()
        self.fix_btn.hide()
        self.ask_input.show()
        self.ask_input.clear()
        self.ask_hint.show()
        self.ask_now_btn.show()
        self.output.setText("Describe your problem above and click Ask Now.\n\nGetPCFixed will scan your PC and tell you exactly what's wrong.")
        self.status.setText("Ready")

    def run_ask(self):
        question = self.ask_input.toPlainText().strip()
        if not question:
            self.output.setText("Please describe your problem first!")
            return
        self.last_question = question
        self.fix_btn.hide()
        self.status.setText("Working...")
        self.output.setText("Scanning your PC and thinking about your problem...\nThis will take just a moment.")
        self.ask_worker = AskWorkerThread(question)
        self.ask_worker.result.connect(self.show_ask_result)
        self.ask_worker.start()

    def show_ask_result(self, text):
        self.last_diagnosis = text
        self.output.setText(text)
        self.fix_btn.show()
        self.status.setText("Done")

    def run_fix(self):
        self.fix_btn.hide()
        self.status.setText("Figuring out the best fix...")
        self.output.setText("Got it! Let me figure out the best fix for you...\nOne moment.")
        self.fix_decision_worker = FixDecisionThread(self.last_question, self.last_diagnosis)
        self.fix_decision_worker.decision.connect(self.execute_fix)
        self.fix_decision_worker.start()

    def execute_fix(self, task):
        fix_labels = {
            "clean": "Running Junk File Cleaner",
            "startup": "Checking Startup Programs",
            "network": "Running Network Diagnostic",
            "scan": "Running Full System Scan"
        }
        self.title.setText(fix_labels.get(task, "Running Fix"))
        self.status.setText("Fixing...")
        self.output.setText(f"Running the fix now...\nPlease wait.")
        self.worker = WorkerThread(task)
        self.worker.result.connect(self.show_result)
        self.worker.start()
        log_event("Yes Fix It", f"Ran {task} after Ask diagnosis")

    def run_task(self, task):
        self.ask_input.hide()
        self.ask_hint.hide()
        self.ask_now_btn.hide()
        self.fix_btn.hide()
        self.repair_btn.hide()
        self.repair_task = None
        self.status.setText("Working...")
        self.output.setText("Please wait...")

        fix_map = {
            "updates":    "fix_updates",
            "diskhealth": "fix_disk",
            "devices":    "fix_devices",
            "network":    "fix_network",
            "wifi":       "fix_network",
            "malware":    "fix_malware",
            "temps":      "fix_temps",
            "bsod":       "fix_bsod",
            "crashes":    "fix_crashes",
            "battery":    "fix_battery",
        }

        if task == "startup":
            self.show_startup()
            return

        if task == "about":
            self.show_about()
            return

        if task in fix_map:
            self.repair_task = fix_map[task]

        self.title.setText({
            "scan": "System Scan Results",
            "diagnose": "AI Diagnosis",
            "junk": "Junk File Scanner",
            "clean": "Junk File Cleaner",
            "network": "Network Diagnostic",
            "wifi": "WiFi Diagnostic",
            "bsod": "Blue Screen (BSOD) Report",
            "crashes": "App Crash & Freeze Check",
            "malware": "Malware & Security Check",
            "temps": "Overheating Check",
            "updates": "Windows Update Check",
            "devices": "Devices & USB Check",
            "diskhealth": "Disk Health Check",
            "battery": "Battery Diagnostic",
            "history": "History Log"
        }.get(task, "GetPCFixed"))

        self.worker = WorkerThread(task)
        self.worker.result.connect(self.show_result)
        self.worker.start()

    def show_result(self, text):
        self.clean_btn.hide()
        if "Click Clean Now" in text:
            self.clean_btn.show()

        if self.repair_task:
            self.repair_btn.show()
        else:
            self.repair_btn.hide()

        html = ""
        for line in text.split("\n"):
            if "[OK]" in line:
                line = line.replace("[OK]", "<span style='color:#22c55e'>[OK]</span>")
            elif "[WARN]" in line:
                line = line.replace("[WARN]", "<span style='color:#f59e0b'>[WARN]</span>")
            elif "[HIGH]" in line:
                line = line.replace("[HIGH]", "<span style='color:#ef4444'>[HIGH]</span>")
            html += line + "<br>"

        self.output.setHtml(html)
        self.status.setText("Done")

    def show_startup(self):
        self.title.setText("Startup Programs")
        programs = get_startup_programs()
        if not programs:
            self.output.setText("No startup programs found.")
            self.status.setText("Done")
            return
        lines = ["These programs load every time Windows starts:\n"]
        for i, p in enumerate(programs):
            lines.append(f"{i + 1}. {p['name']}")
            lines.append(f"   {p['path']}\n")
        lines.append("Full startup controls coming soon!")
        self.output.setText("\n".join(lines))
        self.status.setText("Done")

    def show_about(self):
        self.title.setText("About GetPCFixed")
        self.output.setText(
            "GetPCFixed v0.5\n\n"
            "Your PC deserves better than error messages and slow boots.\n\n"
            "GetPCFixed detects, diagnoses, and fixes the most common Windows\n"
            "problems everyday people face — always asking before changing anything.\n\n"
            "Built for the 1 billion Windows users the enterprise tools forgot.\n\n"
            "getpcfixed.com | getpcfixed.app\n\n"
            "Built with Python + Claude AI"
        )
        self.status.setText("v0.5")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
