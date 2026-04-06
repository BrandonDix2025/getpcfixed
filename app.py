import sys
import os
import anthropic
from ratelimit import can_scan, record_scan
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout,
                              QHBoxLayout, QPushButton, QLabel, QTextEdit, QFrame, QScrollArea)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from scanner import scan_system_data
from diagnose import diagnose as run_diagnosis
from cleaner import scan_junk, clean_junk_silent
from startup import get_startup_programs, disable_startup_program
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
from tray import start_tray, set_open_callback
from autostart import is_autostart_enabled, enable_autostart

# Find .env whether running as .exe or as Python script
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))



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
            allowed, msg = can_scan()
            if not allowed:
                self.result.emit(msg)
                return

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
            record_scan()
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


# ════════════════════════════════════════════════════════════
#  THEMES
# ════════════════════════════════════════════════════════════
DARK = {
    'app_bg':           '#1a1a1a',  'sidebar_bg':      '#141414',
    'sidebar_border':   '#2a2a2a',  'logo_bg':         '#0f0f0f',
    'logo_border':      '#2a2a2a',  'bot_bg':          '#0f0f0f',
    'bot_border':       '#2a2a2a',  'hdr_bg':          '#141414',
    'hdr_border':       '#2a2a2a',
    'nav_text':         '#b0b0b0',  'nav_hover':       '#252525',
    'nav_hborder':      '#3a3a3a',
    'nav_active_bg':    'rgba(0,120,212,0.12)',
    'nav_active_text':  '#ffffff',
    'nav_ask_bg':       'rgba(16,124,16,0.15)', 'nav_ask_text':  '#4ade80',
    'nav_ask_border':   '#16a34a',  'nav_ask_hover':   'rgba(16,124,16,0.25)',
    'nav_ask_htxt':     '#6ee7a0',  'section_color':   '#505050',
    'output_bg':        '#212121',  'output_border':   '#2d2d2d',
    'output_text':      '#f3f3f3',  'title_color':     '#ffffff',
    'sub_color':        '#505050',  'name_color':      '#ffffff',
    'status_color':     '#404040',
    'monitor_bg':       'rgba(16,124,16,0.18)', 'monitor_text': '#4ade80',
    'monitor_border':   '#166534',  'monitor_hover':   'rgba(16,124,16,0.30)',
    'monitor_hborder':  '#22c55e',
    'scroll_handle':    '#3a3a3a',  'scroll_hover':    '#606060',
    # HTML dashboard
    'card_bg':          '#262626',  'card_border':     '#2e2e2e',
    'bar_empty':        '#2e2e2e',
    'sys_bg':           '#1e1e1e',  'sys_border':      '#2a2a2a',
    'sys_label':        '#505050',  'sys_value':       '#808080',
    'metric_sub':       '#707070',  'row_text':        '#e0e0e0',
    'msg_text':         '#a0a0a0',
    'abt_card_bg':      'rgba(0,120,212,0.10)',
    'abt_card_brd':     'rgba(0,120,212,0.25)',
    'abt_title':        '#ffffff',  'abt_ver':         '#505050',
    'abt_body':         '#909090',  'abt_info_bg':     '#1e1e1e',
    'abt_info_brd':     '#2a2a2a',  'abt_key':         '#505050',
    'abt_link':         '#0078d4',  'abt_val':         '#808080',
    'st_hdr':           '#606060',  'st_name':         '#ffffff',
    'st_path':          '#606060',  'st_div':          '#2a2a2a',
    'st_foot':          '#505050',
    'ask_inp_bg':       '#1e1e1e',  'ask_inp_brd':     '#3a3a3a',
    'theme_icon':       '\u2600\ufe0f',
}

LIGHT = {
    'app_bg':           '#f3f3f3',  'sidebar_bg':      '#fafafa',
    'sidebar_border':   '#e0e0e0',  'logo_bg':         '#ffffff',
    'logo_border':      '#e8e8e8',  'bot_bg':          '#ffffff',
    'bot_border':       '#e8e8e8',  'hdr_bg':          '#ffffff',
    'hdr_border':       '#e8e8e8',
    'nav_text':         '#404040',  'nav_hover':       '#ebebeb',
    'nav_hborder':      '#d0d0d0',
    'nav_active_bg':    'rgba(0,120,212,0.08)',
    'nav_active_text':  '#0078d4',
    'nav_ask_bg':       'rgba(16,124,16,0.08)', 'nav_ask_text':  '#107c10',
    'nav_ask_border':   '#107c10',  'nav_ask_hover':   'rgba(16,124,16,0.14)',
    'nav_ask_htxt':     '#0a5c0a',  'section_color':   '#b0b0b0',
    'output_bg':        '#ffffff',  'output_border':   '#e0e0e0',
    'output_text':      '#1a1a1a',  'title_color':     '#1a1a1a',
    'sub_color':        '#909090',  'name_color':      '#1a1a1a',
    'status_color':     '#a0a0a0',
    'monitor_bg':       'rgba(16,124,16,0.08)', 'monitor_text': '#107c10',
    'monitor_border':   '#107c10',  'monitor_hover':   'rgba(16,124,16,0.15)',
    'monitor_hborder':  '#16a34a',
    'scroll_handle':    '#d0d0d0',  'scroll_hover':    '#b0b0b0',
    # HTML dashboard
    'card_bg':          '#f0f0f0',  'card_border':     '#e0e0e0',
    'bar_empty':        '#e0e0e0',
    'sys_bg':           '#f8f8f8',  'sys_border':      '#e8e8e8',
    'sys_label':        '#909090',  'sys_value':       '#606060',
    'metric_sub':       '#909090',  'row_text':        '#1a1a1a',
    'msg_text':         '#505050',
    'abt_card_bg':      'rgba(0,120,212,0.05)',
    'abt_card_brd':     'rgba(0,120,212,0.20)',
    'abt_title':        '#1a1a1a',  'abt_ver':         '#909090',
    'abt_body':         '#505050',  'abt_info_bg':     '#f8f8f8',
    'abt_info_brd':     '#e8e8e8',  'abt_key':         '#909090',
    'abt_link':         '#0078d4',  'abt_val':         '#606060',
    'st_hdr':           '#909090',  'st_name':         '#1a1a1a',
    'st_path':          '#909090',  'st_div':          '#e8e8e8',
    'st_foot':          '#aaaaaa',
    'ask_inp_bg':       '#ffffff',  'ask_inp_brd':     '#d0d0d0',
    'theme_icon':       '\U0001f319',
}


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("GetPCFixed  —  AI PC Repair")
        self.setMinimumSize(960, 640)
        self.resize(1120, 740)
        qr = self.frameGeometry()
        cp = QApplication.desktop().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

        self.last_diagnosis = ""
        self.last_question = ""
        self.is_dark         = True
        self.theme           = DARK
        self.active_nav_btn  = None
        self.nav_buttons     = []
        self.repair_task     = None
        self._page           = 'dashboard'  # track page for theme refresh

        self.setStyleSheet(self._global_css())
        self.build_ui()
        self.show_dashboard()
        set_notify_callback(self.on_monitor_alert)
        start_monitor()

    # ── Theme CSS ────────────────────────────────────────────────────
    def _global_css(self):
        t = self.theme
        return f"""
            QMainWindow  {{ background-color: {t['app_bg']}; }}
            QWidget      {{ background-color: transparent; color: {t['output_text']};
                           font-family: 'Segoe UI', Arial, sans-serif; }}
            QScrollBar:vertical {{
                background: transparent; width: 4px; margin: 0;
            }}
            QScrollBar::handle:vertical {{
                background: {t['scroll_handle']}; border-radius: 2px; min-height: 24px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {t['scroll_hover']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical  {{ background: transparent; }}
            QTextEdit {{
                background-color: {t['output_bg']};
                color: {t['output_text']};
                border: 1px solid {t['output_border']};
                border-radius: 8px;
                padding: 20px;
                font-size: 13px;
                font-family: 'Segoe UI', Arial, sans-serif;
                selection-background-color: #0078d4;
            }}
            QScrollArea {{ border: none; background: transparent; }}
        """

    # ── Nav helper styles ──────────────────────────────────────────────────
    def _nav_default(self):
        t = self.theme
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {t['nav_text']};
                border: none;
                border-left: 3px solid transparent;
                border-radius: 0px;
                padding: 0px 0px 0px 14px;
                font-size: 13px;
                font-family: 'Segoe UI';
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {t['nav_hover']};
                color: {t['title_color']};
                border-left: 3px solid {t['nav_hborder']};
            }}
        """

    def _nav_active(self):
        t = self.theme
        return f"""
            QPushButton {{
                background-color: {t['nav_active_bg']};
                color: {t['nav_active_text']};
                border: none;
                border-left: 3px solid #0078d4;
                border-radius: 0px;
                padding: 0px 0px 0px 14px;
                font-size: 13px;
                font-family: 'Segoe UI';
                font-weight: 600;
                text-align: left;
            }}
        """

    def _nav_ask(self):
        t = self.theme
        return f"""
            QPushButton {{
                background-color: {t['nav_ask_bg']};
                color: {t['nav_ask_text']};
                border: none;
                border-left: 3px solid {t['nav_ask_border']};
                border-radius: 0px;
                padding: 0px 0px 0px 14px;
                font-size: 13px;
                font-family: 'Segoe UI';
                font-weight: 600;
                text-align: left;
            }}
            QPushButton:hover {{
                background-color: {t['nav_ask_hover']};
                color: {t['nav_ask_htxt']};
            }}
        """

    def _make_nav(self, label, task, ask=False):
        btn = QPushButton(label)
        btn.setFixedHeight(36)
        btn.setCursor(Qt.PointingHandCursor)
        btn.setStyleSheet(self._nav_ask() if ask else self._nav_default())
        btn.clicked.connect(lambda: self._nav_click(btn, task))
        self.nav_buttons.append(btn)
        return btn

    def _nav_click(self, btn, task):
        self.set_nav_active(btn)
        if   task == "dashboard": self.show_dashboard()
        elif task == "ask":       self.show_ask()
        else:                     self.run_task(task)

    def set_nav_active(self, btn):
        for b in self.nav_buttons:
            if "Ask GetPCFixed" in b.text():
                b.setStyleSheet(self._nav_ask())
            else:
                b.setStyleSheet(self._nav_default())
        btn.setStyleSheet(self._nav_active())
        self.active_nav_btn = btn

    def _section(self, text):
        lbl = QLabel(text)
        lbl.setFixedHeight(24)
        lbl.setStyleSheet("""
            color: #505050;
            font-size: 10px;
            font-weight: bold;
            font-family: 'Segoe UI';
            padding: 6px 16px 0px 16px;
            letter-spacing: 1.5px;
            background: transparent;
            border: none;
        """)
        return lbl

    # ── Main UI build ────────────────────────────────────────────────────────
    def build_ui(self):
        central = QWidget()
        central.setStyleSheet("background-color: #1a1a1a;")
        self.setCentralWidget(central)

        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        # ════════════════════════════════════
        #  SIDEBAR
        # ════════════════════════════════════
        sidebar = QFrame()
        sidebar.setFixedWidth(244)
        self._sidebar = sidebar
        sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {self.theme['sidebar_bg']};
                border: none;
                border-right: 1px solid {self.theme['sidebar_border']};
            }}
        """)
        sb = QVBoxLayout(sidebar)
        sb.setContentsMargins(0, 0, 0, 0)
        sb.setSpacing(0)

        # Logo / brand strip
        logo_strip = QFrame()
        logo_strip.setFixedHeight(76)
        logo_strip.setStyleSheet("""
            QFrame {
                background-color: #0f0f0f;
                border: none;
                border-bottom: 1px solid #2a2a2a;
            }
        """)
        ls = QVBoxLayout(logo_strip)
        ls.setContentsMargins(16, 10, 16, 10)
        ls.setSpacing(2)

        top_row = QHBoxLayout()
        top_row.setSpacing(8)
        ico = QLabel("\U0001f5a5\ufe0f")
        ico.setFont(QFont("Segoe UI", 18))
        ico.setStyleSheet("border:none; background:transparent; color:#0078d4;")
        top_row.addWidget(ico)
        name = QLabel("GetPCFixed")
        name.setFont(QFont("Segoe UI", 14, QFont.Bold))
        name.setStyleSheet("border:none; background:transparent; color:#ffffff;")
        self._logo_name = name
        top_row.addWidget(name)
        top_row.addStretch()
        badge = QLabel("  BETA  ")
        badge.setFont(QFont("Segoe UI", 8, QFont.Bold))
        badge.setStyleSheet("""
            background-color: #0078d4; color: #ffffff;
            border: none; border-radius: 3px; padding: 2px 0px;
        """)
        top_row.addWidget(badge)
        ls.addLayout(top_row)

        sub = QLabel("AI-Powered Windows PC Repair  •  v0.5")
        sub.setFont(QFont("Segoe UI", 9))
        sub.setStyleSheet("border:none; background:transparent; color:#505050;")
        self._logo_sub = sub
        ls.addWidget(sub)
        self._logo_strip = logo_strip
        sb.addWidget(logo_strip)

        # Nav scroll area
        nav_scroll = QScrollArea()
        nav_scroll.setWidgetResizable(True)
        nav_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        nav_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: transparent; width: 4px; }
            QScrollBar::handle:vertical {
                background: #2e2e2e; border-radius: 2px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #505050; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
        """)
        nav_w = QWidget()
        nav_w.setStyleSheet("background: transparent;")
        nav_l = QVBoxLayout(nav_w)
        nav_l.setContentsMargins(0, 8, 0, 8)
        nav_l.setSpacing(1)

        self.dash_nav_btn = self._make_nav("   \U0001f3e0   Dashboard", "dashboard")
        nav_l.addWidget(self.dash_nav_btn)
        self.ask_nav_btn  = self._make_nav("   \U0001f4ac   Ask GetPCFixed", "ask", ask=True)
        nav_l.addWidget(self.ask_nav_btn)
        nav_l.addSpacing(4)

        nav_l.addWidget(self._section("DIAGNOSTICS"))
        nav_l.addWidget(self._make_nav("   \U0001f50d   Scan My PC",       "scan"))
        nav_l.addWidget(self._make_nav("   \U0001f916   AI Diagnosis",      "diagnose"))

        nav_l.addWidget(self._section("PERFORMANCE"))
        nav_l.addWidget(self._make_nav("   \U0001f9f9   Clean Junk Files",  "junk"))
        nav_l.addWidget(self._make_nav("   \U0001f680   Startup Programs",  "startup"))
        nav_l.addWidget(self._make_nav("   \U0001f321\ufe0f   Overheating Check", "temps"))

        nav_l.addWidget(self._section("CONNECTIVITY"))
        nav_l.addWidget(self._make_nav("   \U0001f310   Network Diagnostic", "network"))
        nav_l.addWidget(self._make_nav("   \U0001f4f6   WiFi Issues",        "wifi"))

        nav_l.addWidget(self._section("SECURITY"))
        nav_l.addWidget(self._make_nav("   \U0001f6e1\ufe0f   Malware Check",     "malware"))
        nav_l.addWidget(self._make_nav("   \U0001f504   Windows Updates",    "updates"))
        nav_l.addWidget(self._make_nav("   \U0001f4be   Disk Health",         "diskhealth"))
        nav_l.addWidget(self._make_nav("   \U0001f50c   Devices & USB",       "devices"))

        nav_l.addWidget(self._section("PROBLEMS"))
        nav_l.addWidget(self._make_nav("   \U0001f4a5   Blue Screen (BSOD)", "bsod"))
        nav_l.addWidget(self._make_nav("   \U0001fab2   App Crashes",         "crashes"))
        nav_l.addWidget(self._make_nav("   \U0001f50b   Battery",             "battery"))

        nav_l.addWidget(self._section("MORE"))
        nav_l.addWidget(self._make_nav("   \U0001f4cb   History",             "history"))
        nav_l.addWidget(self._make_nav("   \u2139\ufe0f   About",              "about"))
        nav_l.addStretch()

        nav_scroll.setWidget(nav_w)
        self._nav_scroll = nav_scroll
        sb.addWidget(nav_scroll)

        # Bottom bar
        bot = QFrame()
        self._bot = bot
        bot.setStyleSheet("""
            QFrame {
                background-color: #0f0f0f;
                border: none;
                border-top: 1px solid #2a2a2a;
            }
        """)
        bot_l = QVBoxLayout(bot)
        bot_l.setContentsMargins(12, 10, 12, 12)
        bot_l.setSpacing(6)

        self.monitor_btn = QPushButton("   \U0001f7e2   Keep Me Running: ON")
        self.monitor_btn.setFixedHeight(36)
        self.monitor_btn.setCursor(Qt.PointingHandCursor)
        self.monitor_btn.setStyleSheet("""
            QPushButton {
                background-color: rgba(16,124,16,0.18);
                color: #4ade80;
                border: 1px solid #166534;
                border-radius: 6px;
                padding: 0px 12px;
                font-size: 12px;
                font-weight: 600;
                font-family: 'Segoe UI';
                text-align: left;
            }
            QPushButton:hover {
                background-color: rgba(16,124,16,0.30);
                border: 1px solid #22c55e;
            }
        """)
        self.monitor_btn.clicked.connect(self.toggle_monitor)
        bot_l.addWidget(self.monitor_btn)

        self.status = QLabel("\u25cf  Ready")
        self.status.setAlignment(Qt.AlignCenter)
        self.status.setStyleSheet("""
            color: #404040;
            font-size: 11px;
            font-family: 'Segoe UI';
            border: none;
            background: transparent;
        """)
        bot_l.addWidget(self.status)
        self._status_lbl = self.status
        sb.addWidget(bot)
        root.addWidget(sidebar)

        # ════════════════════════════════════
        #  CONTENT AREA
        # ════════════════════════════════════
        content_wrap = QWidget()
        content_wrap.setStyleSheet("background-color: #1a1a1a;")
        self._content_wrap = content_wrap
        cv = QVBoxLayout(content_wrap)
        cv.setContentsMargins(0, 0, 0, 0)
        cv.setSpacing(0)

        # Header bar
        hdr = QFrame()
        hdr.setFixedHeight(56)
        self._hdr = hdr
        hdr.setStyleSheet("""
            QFrame {
                background-color: #141414;
                border: none;
                border-bottom: 1px solid #2a2a2a;
            }
        """)
        hdr_l = QHBoxLayout(hdr)
        hdr_l.setContentsMargins(28, 0, 28, 0)

        self.title = QLabel("PC Health Dashboard")
        self.title.setFont(QFont("Segoe UI", 15, QFont.Bold))
        self.title.setStyleSheet(f"color: {self.theme['title_color']}; border: none; background: transparent;")
        hdr_l.addWidget(self.title)
        hdr_l.addStretch()

        # Theme toggle button
        self.mode_lbl = QLabel("Mode")
        self.mode_lbl.setFont(QFont("Segoe UI", 10))
        self.mode_lbl.setStyleSheet(
            f"color: {self.theme['sub_color']}; border: none; background: transparent;"
        )
        hdr_l.addWidget(self.mode_lbl)

        self.theme_btn = QPushButton(self.theme['theme_icon'])
        self.theme_btn.setFixedSize(36, 36)
        self.theme_btn.setCursor(Qt.PointingHandCursor)
        self.theme_btn.setToolTip("Toggle Light / Dark Mode")
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {self.theme['title_color']};
                border: 1px solid {self.theme['hdr_border']};
                border-radius: 6px;
                font-size: 16px;
            }}
            QPushButton:hover {{
                background-color: {self.theme['nav_hover']};
            }}
        """)
        self.theme_btn.clicked.connect(self.toggle_theme)
        hdr_l.addWidget(self.theme_btn)
        cv.addWidget(hdr)

        # Action button row (shown contextually)
        act_frame = QFrame()
        act_frame.setStyleSheet("background: transparent; border: none;")
        self.act_row = QHBoxLayout(act_frame)
        self.act_row.setContentsMargins(28, 14, 28, 0)
        self.act_row.setSpacing(10)

        def _action_btn(label, color, hover):
            b = QPushButton(label)
            b.setFixedHeight(36)
            b.setCursor(Qt.PointingHandCursor)
            b.setStyleSheet(f"""
                QPushButton {{
                    background-color: {color};
                    color: white; border: none; border-radius: 6px;
                    padding: 0px 20px; font-size: 13px; font-weight: 600;
                    font-family: 'Segoe UI';
                }}
                QPushButton:hover {{ background-color: {hover}; }}
            """)
            return b

        self.repair_btn = _action_btn("\U0001f527  Fix It",    "#c42b1c", "#e03226")
        self.repair_btn.clicked.connect(self.run_repair)
        self.repair_btn.hide()
        self.act_row.addWidget(self.repair_btn)

        self.clean_btn = _action_btn("\u2728  Clean Now", "#107c10", "#1a9c1a")
        self.clean_btn.clicked.connect(lambda: self.run_task("clean"))
        self.clean_btn.hide()
        self.act_row.addWidget(self.clean_btn)

        self.fix_btn = _action_btn("\u2705  Yes, Fix It!", "#107c10", "#1a9c1a")
        self.fix_btn.clicked.connect(self.run_fix)
        self.fix_btn.hide()
        self.act_row.addWidget(self.fix_btn)

        self.act_row.addStretch()
        cv.addWidget(act_frame)

        # Ask input block (hidden until Ask tab)
        ask_frame = QFrame()
        ask_frame.setStyleSheet("background: transparent; border: none;")
        ask_vb = QVBoxLayout(ask_frame)
        ask_vb.setContentsMargins(28, 14, 28, 0)
        ask_vb.setSpacing(8)

        self.ask_input = QTextEdit()
        self.ask_input.setPlaceholderText(
            "Describe your problem here...  "
            "(e.g. My computer is really slow when I open Chrome)"
        )
        self.ask_input.setFixedHeight(88)
        self.ask_input.setStyleSheet("""
            QTextEdit {
                background-color: #1e1e1e;
                color: #f3f3f3;
                border: 1px solid #3a3a3a;
                border-radius: 6px;
                padding: 10px 14px;
                font-size: 13px;
                font-family: 'Segoe UI';
            }
            QTextEdit:focus { border: 1px solid #0078d4; }
        """)
        self.ask_input.hide()
        ask_vb.addWidget(self.ask_input)

        ask_btn_row = QHBoxLayout()
        self.ask_now_btn = _action_btn("  \U0001f50d  Analyze My PC", "#0078d4", "#1a8fe8")
        self.ask_now_btn.clicked.connect(self.run_ask)
        self.ask_now_btn.hide()
        ask_btn_row.addWidget(self.ask_now_btn)
        ask_btn_row.addStretch()
        ask_vb.addLayout(ask_btn_row)

        self.ask_hint = QLabel(
            "GetPCFixed will scan your PC and give you a plain-English diagnosis."
        )
        self.ask_hint.setStyleSheet(
            "color: #505050; font-size: 11px; border: none; background: transparent;"
        )
        self.ask_hint.hide()
        ask_vb.addWidget(self.ask_hint)
        cv.addWidget(ask_frame)

        # Output area
        out_frame = QFrame()
        out_frame.setStyleSheet("background: transparent; border: none;")
        out_vb = QVBoxLayout(out_frame)
        out_vb.setContentsMargins(28, 16, 28, 28)

        self.output = QTextEdit()
        self.output.setReadOnly(True)
        self.output.setText("Loading dashboard...")
        out_vb.addWidget(self.output)

        # Startup panel — swaps in place of output on startup page
        self.startup_scroll = QScrollArea()
        self.startup_scroll.setWidgetResizable(True)
        self.startup_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.startup_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: transparent; width: 4px; }
            QScrollBar::handle:vertical {
                background: #3a3a3a; border-radius: 2px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #606060; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
        """)
        self.startup_scroll.hide()
        out_vb.addWidget(self.startup_scroll)

        self.history_scroll = QScrollArea()
        self.history_scroll.setWidgetResizable(True)
        self.history_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.history_scroll.setStyleSheet("""
            QScrollArea { border: none; background: transparent; }
            QScrollBar:vertical { background: transparent; width: 4px; }
            QScrollBar::handle:vertical {
                background: #3a3a3a; border-radius: 2px; min-height: 20px;
            }
            QScrollBar::handle:vertical:hover { background: #606060; }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical { height: 0; }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical { background: transparent; }
        """)
        self.history_scroll.hide()
        out_vb.addWidget(self.history_scroll)
        cv.addWidget(out_frame)

        root.addWidget(content_wrap)

    def run_repair(self):
        self.repair_btn.hide()
        self.status.setText("\u25cf  Fixing...")
        self.output.setHtml(self._msg_html("Running fix — please wait, this may take a minute..."))
        self.worker = WorkerThread(self.repair_task)
        self.worker.result.connect(self.show_result)
        self.worker.start()

    def _msg_html(self, text):
        t = self.theme
        return f"""
        <div style='font-family: Segoe UI, Arial, sans-serif;
                    color: {t['msg_text']}; font-size: 13px; padding: 4px;'>
            {text}
        </div>
        """

    # ── Theme toggle ─────────────────────────────────────────────────────
    def toggle_theme(self):
        self.is_dark = not self.is_dark
        self.theme   = DARK if self.is_dark else LIGHT
        self.apply_theme()

    def apply_theme(self):
        t = self.theme
        # Global Qt stylesheet
        self.setStyleSheet(self._global_css())
        # Sidebar panel
        self._sidebar.setStyleSheet(f"""
            QFrame {{
                background-color: {t['sidebar_bg']};
                border: none; border-right: 1px solid {t['sidebar_border']};
            }}
        """)
        # Logo strip
        self._logo_strip.setStyleSheet(f"""
            QFrame {{
                background-color: {t['logo_bg']};
                border: none; border-bottom: 1px solid {t['logo_border']};
            }}
        """)
        self._logo_name.setStyleSheet(
            f"border:none; background:transparent; color:{t['name_color']};"
        )
        self._logo_sub.setStyleSheet(
            f"border:none; background:transparent; color:{t['sub_color']};"
        )
        # Nav scroll
        self._nav_scroll.setStyleSheet(f"""
            QScrollArea {{ border: none; background: transparent; }}
            QScrollBar:vertical {{ background: transparent; width: 4px; }}
            QScrollBar::handle:vertical {{
                background: {t['scroll_handle']}; border-radius: 2px; min-height: 20px;
            }}
            QScrollBar::handle:vertical:hover {{ background: {t['scroll_hover']}; }}
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height: 0; }}
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {{ background: transparent; }}
        """)
        # Nav buttons
        for b in self.nav_buttons:
            if b == self.active_nav_btn:
                b.setStyleSheet(self._nav_active())
            elif "Ask GetPCFixed" in b.text():
                b.setStyleSheet(self._nav_ask())
            else:
                b.setStyleSheet(self._nav_default())
        # Bottom bar
        self._bot.setStyleSheet(f"""
            QFrame {{
                background-color: {t['bot_bg']};
                border: none; border-top: 1px solid {t['bot_border']};
            }}
        """)
        # Monitor button
        if is_running():
            self.monitor_btn.setStyleSheet(f"""
                QPushButton {{
                    background-color: {t['monitor_bg']};
                    color: {t['monitor_text']};
                    border: 1px solid {t['monitor_border']};
                    border-radius: 6px; padding: 0px 12px;
                    font-size: 12px; font-weight: 600;
                    font-family: 'Segoe UI'; text-align: left;
                }}
                QPushButton:hover {{
                    background-color: {t['monitor_hover']};
                    border: 1px solid {t['monitor_hborder']};
                }}
            """)
        # Status label
        self._status_lbl.setStyleSheet(
            f"color:{t['status_color']}; font-size:11px; font-family:'Segoe UI';"
            f" border:none; background:transparent;"
        )
        # Content wrap + header
        self._content_wrap.setStyleSheet(f"background-color: {t['app_bg']};")
        self._hdr.setStyleSheet(f"""
            QFrame {{
                background-color: {t['hdr_bg']};
                border: none; border-bottom: 1px solid {t['hdr_border']};
            }}
        """)
        # Title + theme button + mode label
        self.title.setStyleSheet(
            f"color:{t['title_color']}; border:none; background:transparent;"
        )
        self.mode_lbl.setStyleSheet(
            f"color:{t['sub_color']}; border:none; background:transparent;"
        )
        self.theme_btn.setText(t['theme_icon'])
        self.theme_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: transparent;
                color: {t['title_color']};
                border: 1px solid {t['hdr_border']};
                border-radius: 6px; font-size: 16px;
            }}
            QPushButton:hover {{ background-color: {t['nav_hover']}; }}
        """)
        # Ask input
        self.ask_input.setStyleSheet(f"""
            QTextEdit {{
                background-color: {t['ask_inp_bg']};
                color: {t['output_text']};
                border: 1px solid {t['ask_inp_brd']};
                border-radius: 6px; padding: 10px 14px;
                font-size: 13px; font-family: 'Segoe UI';
            }}
            QTextEdit:focus {{ border: 1px solid #0078d4; }}
        """)
        # Re-render current page
        self._refresh_page()

    def _refresh_page(self):
        p = self._page
        if p == 'dashboard':  self.show_dashboard()
        elif p == 'ask':      self.show_ask()
        elif p == 'about':    self.show_about()
        elif p == 'startup':  self.show_startup()
        else:                 pass  # result pages re-render on next scan

    def show_dashboard(self):
        self._page = 'dashboard'
        self.title.setText("PC Health Dashboard")
        self.clean_btn.hide()
        self.fix_btn.hide()
        self.ask_input.hide()
        self.ask_hint.hide()
        self.ask_now_btn.hide()
        self.repair_btn.hide()
        self.startup_scroll.hide()
        self.output.show()
        self.set_nav_active(self.dash_nav_btn)
        self.output.setHtml(self._msg_html("Scanning your PC..."))
        self.status.setText("\u25cf  Scanning...")
        self.dash_worker = DashboardThread()
        self.dash_worker.result.connect(self.render_dashboard)
        self.dash_worker.start()

    def render_dashboard(self, data):
        cpu      = data['cpu']
        ram_used = data['ram_used']
        ram_total= data['ram_total']
        disk_used= data['disk_used']
        disk_total=data['disk_total']
        ram_pct  = round((ram_used  / ram_total)  * 100)
        disk_pct = round((disk_used / disk_total) * 100)

        issues = 0
        if cpu      >= 80: issues += 2
        elif cpu    >= 50: issues += 1
        if ram_pct  >= 80: issues += 2
        elif ram_pct>= 50: issues += 1
        if disk_pct >= 90: issues += 2
        elif disk_pct>=70: issues += 1

        score = max(0, 100 - (issues * 15))

        if score >= 80:
            score_color  = "#0ea368"
            score_glow   = "rgba(14,163,104,0.18)"
            status_msg   = "Your PC is running great"
            status_icon  = "\u2713"
        elif score >= 50:
            score_color  = "#d4a017"
            score_glow   = "rgba(212,160,23,0.18)"
            status_msg   = "Your PC has a few things to look at"
            status_icon  = "\u26a0"
        else:
            score_color  = "#c42b1c"
            score_glow   = "rgba(196,43,28,0.18)"
            status_msg   = "Your PC needs attention"
            status_icon  = "\u2715"

        cpu_color  = "#0ea368" if cpu      < 50 else "#d4a017" if cpu      < 80 else "#c42b1c"
        ram_color  = "#0ea368" if ram_pct  < 50 else "#d4a017" if ram_pct  < 80 else "#c42b1c"
        disk_color = "#0ea368" if disk_pct < 70 else "#d4a017" if disk_pct < 90 else "#c42b1c"

        def bar(pct, color):
            filled = max(1, int(pct))
            empty  = max(0, 100 - filled)
            return (
                f"<table width='100%' cellspacing='0' cellpadding='0' "
                f"style='margin:6px 0 18px 0; border-radius:4px; overflow:hidden;'>"
                f"<tr>"
                f"<td width='{filled}%' style='background:{color}; height:8px; "
                f"border-radius:4px 0 0 4px;'></td>"
                f"<td width='{empty}%'  style='background:{self.theme['bar_empty']}; height:8px; "
                f"border-radius:0 4px 4px 0;'></td>"
                f"</tr></table>"
            )

        def metric_card(icon, label, val_str, pct, color):
            t = self.theme
            return (
                f"<td width='33%' style='padding:0 6px;'>"
                f"<div style='background:{t['card_bg']}; border:1px solid {t['card_border']}; "
                f"border-radius:8px; padding:14px 16px;'>"
                f"<div style='color:{t['metric_sub']}; font-size:11px; "
                f"letter-spacing:0.5px; margin-bottom:6px;'>{icon}  {label}</div>"
                f"<div style='color:{color}; font-size:20px; font-weight:700; "
                f"margin-bottom:4px;'>{val_str}</div>"
                f"{bar(pct, color)}"
                f"</div></td>"
            )

        t  = self.theme
        ot = t['output_text']
        html = f"""
        <div style='font-family: Segoe UI, Arial, sans-serif;
                    color: {ot}; padding: 4px 2px;'>

            <!-- Score hero card -->
            <div style='background:{score_glow}; border:1px solid {score_color}33;
                        border-radius:10px; padding:28px 24px 22px 24px;
                        text-align:center; margin-bottom:20px;'>
                <div style='font-size:72px; font-weight:700;
                            color:{score_color}; line-height:1;'>{score}</div>
                <div style='font-size:11px; color:#606060;
                            letter-spacing:2px; margin-top:4px;'>PC HEALTH SCORE</div>
                <div style='display:inline-block; margin-top:14px;
                            background:{score_glow}; border:1px solid {score_color};
                            border-radius:20px; padding:5px 18px;
                            font-size:13px; font-weight:600; color:{score_color};'>
                    {status_icon}&nbsp;&nbsp;{status_msg}
                </div>
            </div>

            <!-- Metric cards row -->
            <table width='100%' cellspacing='0' cellpadding='0'
                   style='margin-bottom:20px;'>
                <tr>
                    {metric_card('&#128187;', 'CPU USAGE',  f'{cpu}%',
                                 cpu,  cpu_color)}
                    {metric_card('&#129504;', 'RAM USAGE',
                                 f'{ram_used} / {ram_total} GB',
                                 ram_pct,  ram_color)}
                    {metric_card('&#128190;', 'DISK USAGE',
                                 f'{disk_used} / {disk_total} GB',
                                 disk_pct, disk_color)}
                </tr>
            </table>

            <!-- System info -->
            <div style='background:#1e1e1e; border:1px solid #2a2a2a;
                        border-radius:8px; padding:12px 16px;'>
                <table width='100%' cellspacing='0' cellpadding='0'>
                    <tr>
                        <td style='color:#505050; font-size:11px;
                                   padding:4px 0;'>SYSTEM</td>
                        <td align='right' style='color:#808080; font-size:11px;
                                                 padding:4px 0;'>{data['system']}</td>
                    </tr>
                    <tr>
                        <td style='color:#505050; font-size:11px;
                                   padding:4px 0;'>MACHINE</td>
                        <td align='right' style='color:#808080; font-size:11px;
                                                 padding:4px 0;'>{data['machine']}</td>
                    </tr>
                </table>
            </div>

        </div>
        """
        self.output.setHtml(html)
        self.title.setText("PC Health Dashboard")
        self.status.setText("\u25cf  Live")
        log_event("Dashboard", f"Score: {score} | CPU: {cpu}% | RAM: {ram_pct}% | Disk: {disk_pct}%")

    def toggle_monitor(self):
        if is_running():
            stop_monitor()
            self.monitor_btn.setText("   \U0001f534   Keep Me Running: OFF")
            self.monitor_btn.setStyleSheet("""
                QPushButton {
                    background-color: #1e1e1e;
                    color: #606060;
                    border: 1px solid #2e2e2e;
                    border-radius: 6px;
                    padding: 0px 12px;
                    font-size: 12px;
                    font-weight: 600;
                    font-family: 'Segoe UI';
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: #262626;
                    color: #808080;
                }
            """)
        else:
            start_monitor()
            self.monitor_btn.setText("   \U0001f7e2   Keep Me Running: ON")
            self.monitor_btn.setStyleSheet("""
                QPushButton {
                    background-color: rgba(16,124,16,0.18);
                    color: #4ade80;
                    border: 1px solid #166534;
                    border-radius: 6px;
                    padding: 0px 12px;
                    font-size: 12px;
                    font-weight: 600;
                    font-family: 'Segoe UI';
                    text-align: left;
                }
                QPushButton:hover {
                    background-color: rgba(16,124,16,0.30);
                    border: 1px solid #22c55e;
                }
            """)

    def on_monitor_alert(self, title, message):
        self.status.setText(f"\u26a0\ufe0f  {message[:38]}...")

    def show_ask(self):
        self.title.setText("Ask GetPCFixed")
        self.clean_btn.hide()
        self.fix_btn.hide()
        self.repair_btn.hide()
        self.startup_scroll.hide()
        self.output.show()
        self.ask_input.show()
        self.ask_input.clear()
        self.ask_hint.show()
        self.ask_now_btn.show()
        self.set_nav_active(self.ask_nav_btn)
        self.output.setHtml(self._msg_html(
            "Describe your problem above and click Analyze My PC.<br><br>"
            "GetPCFixed will scan your PC and tell you exactly what\u2019s wrong."
        ))
        self.status.setText("\u25cf  Ready")

    def run_ask(self):
        question = self.ask_input.toPlainText().strip()
        if not question:
            self.output.setHtml(self._msg_html("Please describe your problem first!"))
            return
        self.last_question = question
        self.fix_btn.hide()
        self.status.setText("\u25cf  Working...")
        self.output.setHtml(self._msg_html(
            "Scanning your PC and analyzing your problem...<br>This will take just a moment."
        ))
        self.ask_worker = AskWorkerThread(question)
        self.ask_worker.result.connect(self.show_ask_result)
        self.ask_worker.start()

    def _rate_limit_html(self):
        t = self.theme
        return f"""
        <div style='font-family: Segoe UI, Arial, sans-serif; padding: 80px 8px 24px 8px; text-align: center;'>
            <div style='font-size: 52px; margin-bottom: 16px;'>⏳</div>
            <div style='font-size: 26px; font-weight: 700; color: #d4a017; margin-bottom: 14px;'>
                Weekly Scan Limit Reached
            </div>
            <div style='font-size: 16px; color: {t['output_text']}; line-height: 1.9; margin-bottom: 24px;'>
                You've used your free AI scan for this week.<br>
                Your next free scan unlocks in a few days.
            </div>
            <div style='background: rgba(212,160,23,0.12); border: 1px solid #d4a017;
                        border-radius: 10px; padding: 20px 24px; display: inline-block;'>
                <div style='font-size: 18px; font-weight: 700; color: #d4a017; margin-bottom: 8px;'>
                    🚀 Upgrade to GetPCFixed Pro
                </div>
                <div style='font-size: 15px; color: {t['output_text']};'>
                    Unlimited AI scans &bull; Priority support &bull; $4.99/month
                </div>
                <div style='font-size: 13px; color: {t['sub_color']}; margin-top: 10px;'>
                    Coming soon at getpcfixed.com
                </div>
            </div>
        </div>
        """

    def show_ask_result(self, text):
        self.last_diagnosis = text
        if "free AI scan for this week" in text or "Upgrade to GetPCFixed Pro" in text:
            self.fix_btn.hide()
            self.status.setText("\u25cf  Limit Reached")
            self.output.setHtml(self._rate_limit_html())
        else:
            self.output.setHtml(self._msg_html(text.replace("\n", "<br>")))
            self.fix_btn.show()
            self.status.setText("\u25cf  Done")

    def run_fix(self):
        self.fix_btn.hide()
        self.status.setText("\u25cf  Figuring out the best fix...")
        self.output.setHtml(self._msg_html("Got it! Finding the best fix for you...<br>One moment."))
        self.fix_decision_worker = FixDecisionThread(self.last_question, self.last_diagnosis)
        self.fix_decision_worker.decision.connect(self.execute_fix)
        self.fix_decision_worker.start()

    def execute_fix(self, task):
        fix_labels = {
            "clean":   "Running Junk File Cleaner",
            "startup": "Checking Startup Programs",
            "network": "Running Network Diagnostic",
            "scan":    "Running Full System Scan"
        }
        self.title.setText(fix_labels.get(task, "Running Fix"))
        self.status.setText("\u25cf  Fixing...")
        self.output.setHtml(self._msg_html("Running the fix now... please wait."))
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
        self.clean_btn.hide()
        self.repair_task = None
        self.startup_scroll.hide()
        self.history_scroll.hide()
        self.output.show()
        self.status.setText("\u25cf  Working...")
        self.output.setHtml(self._msg_html("Please wait..."))

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
        if task == "history":
            self.show_history()
            return

        if task in fix_map:
            self.repair_task = fix_map[task]

        titles = {
            "scan":       "System Scan Results",
            "diagnose":   "AI Diagnosis",
            "junk":       "Junk File Scanner",
            "clean":      "Junk File Cleaner",
            "network":    "Network Diagnostic",
            "wifi":       "WiFi Diagnostic",
            "bsod":       "Blue Screen (BSOD) Report",
            "crashes":    "App Crash & Freeze Check",
            "malware":    "Malware & Security Check",
            "temps":      "Overheating Check",
            "updates":    "Windows Update Check",
            "devices":    "Devices & USB Check",
            "diskhealth": "Disk Health Check",
            "battery":    "Battery Diagnostic",
            "history":    "History Log",
        }
        self.title.setText(titles.get(task, "GetPCFixed"))
        self.worker = WorkerThread(task)
        self.worker.result.connect(self.show_result)
        self.worker.start()

    def show_result(self, text):
        self.clean_btn.hide()
        if "free AI scan for this week" in text or "Upgrade to GetPCFixed Pro" in text:
            self.repair_btn.hide()
            self.clean_btn.hide()
            self.status.setText("\u25cf  Limit Reached")
            self.output.setHtml(self._rate_limit_html())
            return
        if "Click Clean Now" in text:
            self.clean_btn.show()
        if self.repair_task:
            self.repair_btn.show()
        else:
            self.repair_btn.hide()

        rows = ""
        for line in text.split("\n"):
            if not line.strip():
                rows += "<tr><td style='padding:4px 0;'>&nbsp;</td></tr>"
                continue
            if "[OK]" in line:
                line = line.replace("[OK]",
                    "<span style='color:#0ea368; font-weight:600;'>[OK]</span>")
            elif "[WARN]" in line:
                line = line.replace("[WARN]",
                    "<span style='color:#d4a017; font-weight:600;'>[WARN]</span>")
            elif "[HIGH]" in line:
                line = line.replace("[HIGH]",
                    "<span style='color:#c42b1c; font-weight:600;'>[HIGH]</span>")
            rows += (f"<tr><td style='padding:5px 0; color:#e0e0e0; "
                     f"font-size:13px; line-height:1.7;'>{line}</td></tr>")

        html = f"""
        <div style='font-family: Segoe UI, Arial, sans-serif; padding: 2px;'>
            <table width='100%' cellspacing='0' cellpadding='0'>
                {rows}
            </table>
        </div>
        """
        self.output.setHtml(html)
        self.status.setText("\u25cf  Done")

    def show_startup(self):
        self._page = 'startup'
        self.title.setText("Startup Programs")
        self.clean_btn.hide()
        self.fix_btn.hide()
        self.repair_btn.hide()
        self.ask_input.hide()
        self.ask_hint.hide()
        self.ask_now_btn.hide()
        self.output.hide()
        self.startup_scroll.show()

        programs = get_startup_programs()
        t = self.theme

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(2, 4, 8, 8)
        vbox.setSpacing(8)

        if not programs:
            empty = QLabel("No startup programs found.")
            empty.setStyleSheet(
                f"color:{t['msg_text']}; font-size:13px; border:none; background:transparent;"
            )
            vbox.addWidget(empty)
        else:
            hdr_lbl = QLabel(
                f"PROGRAMS THAT LOAD ON WINDOWS STARTUP  \u2022  {len(programs)} found"
            )
            hdr_lbl.setFont(QFont("Segoe UI", 10))
            hdr_lbl.setStyleSheet(
                f"color:{t['sub_color']}; border:none; background:transparent; letter-spacing:1px;"
            )
            vbox.addWidget(hdr_lbl)
            vbox.addSpacing(4)

            for prog in programs:
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: {t['card_bg']};
                        border: 1px solid {t['card_border']};
                        border-radius: 8px;
                    }}
                """)
                row = QHBoxLayout(card)
                row.setContentsMargins(16, 12, 12, 12)
                row.setSpacing(12)

                info_col = QVBoxLayout()
                info_col.setSpacing(3)

                name_lbl = QLabel(prog['name'])
                name_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
                name_lbl.setStyleSheet(
                    f"color:{t['output_text']}; border:none; background:transparent;"
                )
                info_col.addWidget(name_lbl)

                path_lbl = QLabel(prog['path'])
                path_lbl.setFont(QFont("Segoe UI", 9))
                path_lbl.setStyleSheet(
                    f"color:{t['sub_color']}; border:none; background:transparent;"
                )
                path_lbl.setWordWrap(True)
                info_col.addWidget(path_lbl)
                row.addLayout(info_col, stretch=1)

                dis_btn = QPushButton("Disable")
                dis_btn.setFixedWidth(90)
                dis_btn.setFixedHeight(32)
                dis_btn.setCursor(Qt.PointingHandCursor)
                dis_btn.setStyleSheet("""
                    QPushButton {
                        background-color: #c42b1c;
                        color: white; border: none; border-radius: 6px;
                        font-size: 12px; font-weight: 600;
                        font-family: 'Segoe UI';
                    }
                    QPushButton:hover { background-color: #e03226; }
                """)
                dis_btn.clicked.connect(
                    lambda checked, p=prog, b=dis_btn, nl=name_lbl:
                    self.disable_startup_item(p, b, nl)
                )
                row.addWidget(dis_btn)
                vbox.addWidget(card)

        vbox.addStretch()
        self.startup_scroll.setWidget(container)
        self.status.setText("\u25cf  Done")

    def disable_startup_item(self, program, btn, name_lbl):
        """Two-click confirm pattern: Disable → Confirm? → Disabled."""
        if btn.text() == "Disable":
            btn.setText("Confirm?")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #d4a017;
                    color: white; border: none; border-radius: 6px;
                    font-size: 11px; font-weight: 600;
                    font-family: 'Segoe UI';
                }
                QPushButton:hover { background-color: #e6b020; }
            """)
        else:
            success = disable_startup_program(program)
            if success:
                btn.setText("\u2713  Disabled")
                btn.setEnabled(False)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #505050;
                        border: 1px solid #2e2e2e;
                        border-radius: 6px;
                        font-size: 11px; font-weight: 600;
                        font-family: 'Segoe UI';
                    }
                """)
                name_lbl.setStyleSheet(
                    "color: #505050; border: none; background: transparent;"
                    " text-decoration: line-through;"
                )
                log_event(
                    "Startup Disabled",
                    f"Disabled {program['name']} from startup",
                    undo_data={
                        "action":   "startup_disable",
                        "name":     program["name"],
                        "path":     program["path"],
                        "hive":     program["hive"],
                        "key_path": program["key_path"],
                    }
                )
            else:
                btn.setText("Failed!")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #c42b1c;
                        color: white; border: none; border-radius: 6px;
                        font-size: 11px; font-weight: 600;
                        font-family: 'Segoe UI';
                    }
                """)

    def show_history(self):
        self._page = 'history'
        self.title.setText("Fix History")
        self.clean_btn.hide()
        self.fix_btn.hide()
        self.repair_btn.hide()
        self.ask_input.hide()
        self.ask_hint.hide()
        self.ask_now_btn.hide()
        self.startup_scroll.hide()
        self.output.hide()
        self.history_scroll.show()

        entries = load_log()
        t = self.theme

        container = QWidget()
        container.setStyleSheet("background: transparent;")
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(2, 4, 8, 8)
        vbox.setSpacing(8)

        if not entries:
            empty = QLabel("No history yet. Run a scan or fix first!")
            empty.setStyleSheet(
                f"color:{t['msg_text']}; font-size:13px; border:none; background:transparent;"
            )
            vbox.addWidget(empty)
        else:
            hdr_lbl = QLabel(f"FIX RECEIPTS  \u2022  {len(entries)} entries")
            hdr_lbl.setFont(QFont("Segoe UI", 10))
            hdr_lbl.setStyleSheet(
                f"color:{t['sub_color']}; border:none; background:transparent; letter-spacing:1px;"
            )
            vbox.addWidget(hdr_lbl)
            vbox.addSpacing(4)

            for entry in reversed(entries):
                card = QFrame()
                card.setStyleSheet(f"""
                    QFrame {{
                        background-color: {t['card_bg']};
                        border: 1px solid {t['card_border']};
                        border-radius: 8px;
                    }}
                """)
                row = QHBoxLayout(card)
                row.setContentsMargins(16, 12, 12, 12)
                row.setSpacing(12)

                info_col = QVBoxLayout()
                info_col.setSpacing(3)

                ts_lbl = QLabel(f"{entry['date']}  {entry['time']}")
                ts_lbl.setFont(QFont("Segoe UI", 9))
                ts_lbl.setStyleSheet(
                    f"color:{t['sub_color']}; border:none; background:transparent;"
                )
                info_col.addWidget(ts_lbl)

                type_lbl = QLabel(entry['type'])
                type_lbl.setFont(QFont("Segoe UI", 12, QFont.Bold))
                type_lbl.setStyleSheet(
                    f"color:{t['output_text']}; border:none; background:transparent;"
                )
                info_col.addWidget(type_lbl)

                detail_lbl = QLabel(entry['details'])
                detail_lbl.setFont(QFont("Segoe UI", 9))
                detail_lbl.setStyleSheet(
                    f"color:{t['sub_color']}; border:none; background:transparent;"
                )
                detail_lbl.setWordWrap(True)
                info_col.addWidget(detail_lbl)
                row.addLayout(info_col, stretch=1)

                if entry.get("undo_data"):
                    undo_btn = QPushButton("Undo")
                    undo_btn.setFixedWidth(80)
                    undo_btn.setFixedHeight(32)
                    undo_btn.setCursor(Qt.PointingHandCursor)
                    undo_btn.setStyleSheet("""
                        QPushButton {
                            background-color: #d4a017;
                            color: white; border: none; border-radius: 6px;
                            font-size: 12px; font-weight: 600;
                            font-family: 'Segoe UI';
                        }
                        QPushButton:hover { background-color: #e6b020; }
                    """)
                    undo_btn.clicked.connect(
                        lambda checked, e=entry, b=undo_btn, tl=type_lbl:
                        self.undo_action(e, b, tl)
                    )
                    row.addWidget(undo_btn)

                vbox.addWidget(card)

        vbox.addStretch()
        self.history_scroll.setWidget(container)
        self.status.setText(f"\u25cf  {len(entries)} entries")

    def undo_action(self, entry, btn, type_lbl):
        """Two-click confirm: Undo -> Confirm? -> execute."""
        if btn.text() == "Undo":
            btn.setText("Confirm?")
            btn.setStyleSheet("""
                QPushButton {
                    background-color: #c42b1c;
                    color: white; border: none; border-radius: 6px;
                    font-size: 11px; font-weight: 600;
                    font-family: 'Segoe UI';
                }
                QPushButton:hover { background-color: #e03226; }
            """)
            return

        undo_data = entry.get("undo_data", {})
        if undo_data.get("action") == "startup_disable":
            success = undo_startup_disable(
                undo_data["name"],
                undo_data["path"],
                undo_data["hive"],
                undo_data["key_path"],
            )
            if success:
                btn.setText("\u2713  Restored")
                btn.setEnabled(False)
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #505050; border: 1px solid #2e2e2e;
                        border-radius: 6px; font-size: 11px; font-weight: 600;
                        font-family: 'Segoe UI';
                    }
                """)
                type_lbl.setStyleSheet(
                    "color: #505050; border: none; background: transparent;"
                    " text-decoration: line-through;"
                )
                log_event("Startup Restored", f"Re-enabled {undo_data['name']} at startup")
            else:
                btn.setText("Failed!")
                btn.setStyleSheet("""
                    QPushButton {
                        background-color: #c42b1c;
                        color: white; border: none; border-radius: 6px;
                        font-size: 11px; font-weight: 600;
                        font-family: 'Segoe UI';
                    }
                """)

    def show_about(self):
        self.title.setText("About GetPCFixed")
        html = """
        <div style='font-family: Segoe UI, Arial, sans-serif; padding: 4px 2px;'>

            <div style='background: rgba(0,120,212,0.10);
                        border: 1px solid rgba(0,120,212,0.25);
                        border-radius:10px; padding:28px 28px 24px 28px;
                        margin-bottom:20px;'>
                <div style='font-size:26px; font-weight:700;
                            color:#ffffff; margin-bottom:4px;'>GetPCFixed</div>
                <div style='font-size:12px; color:#505050;
                            letter-spacing:1px;'>VERSION 0.5  •  BETA</div>
                <div style='color:#909090; font-size:13px;
                            margin-top:16px; line-height:1.8;'>
                    Your PC deserves better than error messages and slow boots.<br>
                    GetPCFixed detects, diagnoses, and fixes the most common Windows<br>
                    problems everyday people face &mdash; always asking before
                    changing anything.
                </div>
            </div>

            <div style='background:#1e1e1e; border:1px solid #2a2a2a;
                        border-radius:8px; padding:16px 20px;'>
                <table width='100%' cellspacing='0' cellpadding='0'>
                    <tr>
                        <td style='color:#505050; font-size:11px;
                                   padding:5px 0;'>WEBSITE</td>
                        <td align='right' style='color:#0078d4; font-size:12px;
                                                 padding:5px 0;'>getpcfixed.com</td>
                    </tr>
                    <tr>
                        <td style='color:#505050; font-size:11px;
                                   padding:5px 0;'>APP STORE</td>
                        <td align='right' style='color:#0078d4; font-size:12px;
                                                 padding:5px 0;'>getpcfixed.app</td>
                    </tr>
                    <tr>
                        <td style='color:#505050; font-size:11px;
                                   padding:5px 0;'>BUILT WITH</td>
                        <td align='right' style='color:#808080; font-size:12px;
                                                 padding:5px 0;'>Python + Claude AI</td>
                    </tr>
                    <tr>
                        <td style='color:#505050; font-size:11px;
                                   padding:5px 0;'>TARGET</td>
                        <td align='right' style='color:#808080; font-size:12px;
                                                 padding:5px 0;'>1 billion Windows users</td>
                    </tr>
                </table>
            </div>

        </div>
        """
        self.output.setHtml(html)
        self.status.setText("\u25cf  v0.5")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    app.setFont(QFont("Segoe UI", 10))
    window = MainWindow()

    # Wire tray icon open callback to bring window to front
    set_open_callback(lambda: (window.show(), window.raise_(), window.activateWindow()))

    # Start background monitor
    set_notify_callback(lambda title, msg: None)  # app handles in-app alerts separately
    start_monitor()

    # Start system tray icon
    start_tray()

    # Enable autostart at boot on first run
    if not is_autostart_enabled():
        enable_autostart()

    window.show()
    sys.exit(app.exec_())
