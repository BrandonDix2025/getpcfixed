import sys
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QLabel, QTextEdit, QFrame)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from scanner import scan_system_data
from diagnose import diagnose as run_diagnosis
from cleaner import scan_junk, clean_junk_silent
from startup import get_startup_programs
from logger import log_event, load_log

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


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GetPCFixed")
        self.setMinimumSize(700, 500)
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

        buttons = [
            ("Scan My PC", "scan"),
            ("AI Diagnosis", "diagnose"),
            ("Clean Junk Files", "junk"),
            ("Fix Startup", "startup"),
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
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 16, 16, 16)

        self.title = QLabel("Welcome to GetPCFixed")
        self.title.setFont(QFont("Segoe UI", 16, QFont.Bold))
        self.title.setStyleSheet("color: #e6edf3; border: none;")
        content_layout.addWidget(self.title)
        self.clean_btn = QPushButton("Clean Now")
        self.clean_btn.setStyleSheet("background-color: #16a34a; color: white; font-size: 14px; padding: 10px; border-radius: 6px;")
        self.clean_btn.clicked.connect(lambda: self.run_task("clean"))
        self.clean_btn.hide()
        content_layout.addWidget(self.clean_btn)
        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setText("Select an option from the left to get started.\n\nGetPCFixed will scan, diagnose, and fix your PC — always asking before changing anything.")
        content_layout.addWidget(self.output)

        main_layout.addWidget(content)

    def run_task(self, task):
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
            "GetPCFixed v0.4\n\n"
            "Your PC deserves better than error messages and slow boots.\n\n"
            "GetPCFixed detects, diagnoses, and fixes the most common Windows\n"
            "problems everyday people face — always asking before changing anything.\n\n"
            "Built for the 1 billion Windows users the enterprise tools forgot.\n\n"
            "getpcfixed.com | getpcfixed.app\n\n"
            "Built with Python + Claude AI"
        )
        self.status.setText("v0.4")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())