import sys
import os
import anthropic
from dotenv import load_dotenv
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QLabel, QTextEdit, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from scanner import scan_system_data
from diagnose import diagnose as run_diagnosis
from cleaner import scan_junk, clean_junk_silent
from startup import get_startup_programs
from logger import log_event, load_log
from network import get_connection_type, check_internet, check_dns, check_gateway, ping_test, speed_test
from wifi import run_wifi_scan
from bsod import run_bsod_scan
from crashes import run_crash_scan
from malware import run_malware_scan
from temps import run_temp_scan
from updates import run_updates_scan
from devices import run_devices_scan
from diskhealth import run_diskhealth_scan
from battery import run_battery_scan

load_dotenv()


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
3. End with: "Want me to fix this for you?"

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GetPCFixed")
        self.setMinimumSize(700, 500)
        self.last_diagnosis = ""
        self.last_question = ""
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
                background-color: #2563eb;
                color: white;
                border: 1px solid #2563eb;
                border-radius: 6px;
                padding: 12px 20px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover { background-color: #1d4ed8; }
        """)
        ask_btn.clicked.connect(self.show_ask)
        sidebar_layout.addWidget(ask_btn)
        sidebar_layout.addSpacing(6)

        buttons = [
            ("Scan My PC", "scan"),
            ("AI Diagnosis", "diagnose"),
            ("Clean Junk Files", "junk"),
            ("Fix Startup", "startup"),
            ("Network Diagnostic", "network"),
            ("WiFi Issues", "wifi"),
            ("Blue Screen (BSOD)", "bsod"),
            ("App Crashes", "crashes"),
            ("Malware Check", "malware"),
            ("Overheating", "temps"),
            ("Windows Updates", "updates"),
            ("Devices & USB", "devices"),
            ("Disk Health", "diskhealth"),
            ("Battery", "battery"),
            ("View History", "history"),
            ("About", "about"),
        ]

        for label, task in buttons:
            btn = QPushButton(label)
            btn.clicked.connect(lambda checked, t=task: self.run_task(t))
            sidebar_layout.addWidget(btn)

        sidebar_layout.addStretch()

        self.status = QLabel("Ready")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("color: #8b949e; font-size: 12px; border: none;")
        sidebar_layout.addWidget(self.status)

        main_layout.addWidget(sidebar)

        content = QFrame()
        content.setStyleSheet("QFrame { border: 1px solid #30363d; border-radius: 8px; }")
        self.content_layout = QVBoxLayout(content)
        self.content_layout.setContentsMargins(16, 16, 16, 16)

        self.title = QLabel("Welcome to GetPCFixed")
        self.title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title.setStyleSheet("color: #e6edf3; border: none;")
        self.content_layout.addWidget(self.title)

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
        self.output.setText("Select an option from the left to get started.\n\nGetPCFixed will scan, diagnose, and fix your PC — always asking before changing anything.")
        self.content_layout.addWidget(self.output)

        main_layout.addWidget(content)

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
        self.status.setText("Working...")
        self.output.setText("Please wait...")

        if task == "startup":
            self.show_startup()
            return

        if task == "about":
            self.show_about()
            return

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
