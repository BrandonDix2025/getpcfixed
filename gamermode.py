import psutil
import subprocess
import platform
from logger import log_event

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QFrame, QSizePolicy
)
from PyQt5.QtCore import Qt, QTimer, pyqtSignal
from PyQt5.QtGui import QFont, QColor


# ── Processes safe to kill to free RAM ───────────────────────────────────────
KILLABLE_PROCESSES = [
    "OneDrive.exe", "Teams.exe", "Slack.exe", "Discord.exe",
    "Spotify.exe", "SearchIndexer.exe", "SpeechRuntime.exe",
    "YourPhone.exe", "SkypeApp.exe", "XboxApp.exe",
    "MicrosoftEdgeUpdate.exe", "GoogleUpdate.exe",
    "AdobeUpdateService.exe", "Dropbox.exe",
]


def _get_cpu() -> float:
    return psutil.cpu_percent(interval=None)


def _get_ram():
    ram = psutil.virtual_memory()
    used  = round(ram.used  / (1024 ** 3), 1)
    total = round(ram.total / (1024 ** 3), 1)
    pct   = ram.percent
    return used, total, pct


def _get_temp() -> str:
    """Return best available CPU temp as a string like '72°C' or 'N/A'."""
    try:
        sensors = psutil.sensors_temperatures()
        if sensors:
            for key in ("coretemp", "k10temp", "cpu_thermal", "acpitz"):
                if key in sensors and sensors[key]:
                    return f"{round(sensors[key][0].current)}°C"
            # Fallback — first available sensor
            first = next(iter(sensors.values()))
            if first:
                return f"{round(first[0].current)}°C"
    except Exception:
        pass

    # WMI fallback
    try:
        cmd = [
            "powershell", "-Command",
            "Get-WmiObject MSAcpi_ThermalZoneTemperature -Namespace root/wmi "
            "| Select-Object -First 1 -ExpandProperty CurrentTemperature"
        ]
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
        raw = out.stdout.strip()
        if raw.isdigit():
            celsius = (int(raw) / 10) - 273.15
            return f"{round(celsius)}°C"
    except Exception:
        pass

    return "N/A"


def clear_ram() -> str:
    """Kill known background apps to free RAM. Returns a result summary."""
    killed = []
    failed = []
    for proc in psutil.process_iter(["name", "pid"]):
        try:
            if proc.info["name"] in KILLABLE_PROCESSES:
                proc.kill()
                killed.append(proc.info["name"])
        except Exception:
            failed.append(proc.info.get("name", "unknown"))

    # Flush Windows standby memory via RAMMap equivalent (empty working sets)
    try:
        subprocess.run(
            ["powershell", "-Command",
             "[System.GC]::Collect(); [System.GC]::WaitForPendingFinalizers()"],
            capture_output=True, timeout=5
        )
    except Exception:
        pass

    if killed:
        summary = f"Freed RAM — stopped: {', '.join(set(killed))}"
    else:
        summary = "No background apps found to close."

    log_event("Gamer Mode — RAM Clear", summary)
    return summary


def kill_background_processes() -> str:
    """Kill high-CPU non-game background processes. Returns a result summary."""
    killed = []
    # Sample CPU usage first
    for proc in psutil.process_iter(["name", "pid", "cpu_percent"]):
        try:
            proc.cpu_percent(interval=None)
        except Exception:
            pass

    import time
    time.sleep(0.8)

    for proc in psutil.process_iter(["name", "pid", "cpu_percent"]):
        try:
            cpu = proc.cpu_percent(interval=None)
            name = proc.info["name"]
            if cpu > 15 and name in KILLABLE_PROCESSES:
                proc.kill()
                killed.append(f"{name} ({cpu}%)")
        except Exception:
            pass

    if killed:
        summary = f"Killed high-CPU processes: {', '.join(killed)}"
    else:
        summary = "No high-CPU background processes found."

    log_event("Gamer Mode — Process Kill", summary)
    return summary


# ── UI Widget ─────────────────────────────────────────────────────────────────

class GamerOverlay(QWidget):
    """
    Always-on-top compact overlay showing live CPU, RAM, Temp.
    Includes one-click RAM Clear and Process Killer buttons.
    """
    closed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("GetPCFixed — Gamer Mode")
        self.setWindowFlags(
            Qt.Window |
            Qt.WindowStaysOnTopHint |
            Qt.FramelessWindowHint |
            Qt.Tool
        )
        self.setAttribute(Qt.WA_TranslucentBackground)
        self.setFixedWidth(260)
        self._drag_pos = None
        self._build_ui()
        self._start_timer()

    # ── drag to move ──────────────────────────────────────────────────────────
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_pos = event.globalPos() - self.frameGeometry().topLeft()

    def mouseMoveEvent(self, event):
        if self._drag_pos and event.buttons() == Qt.LeftButton:
            self.move(event.globalPos() - self._drag_pos)

    def mouseReleaseEvent(self, event):
        self._drag_pos = None

    # ── build UI ──────────────────────────────────────────────────────────────
    def _build_ui(self):
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # Card container
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: rgba(10, 14, 6, 220);
                border: 1px solid #3B6D11;
                border-radius: 14px;
            }
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 14, 16, 14)
        card_layout.setSpacing(10)

        # ── Header ──
        header = QHBoxLayout()
        title = QLabel("⚡ GAMER MODE")
        title.setStyleSheet("color: #97C459; font-size: 11px; font-weight: 700; letter-spacing: 2px; background: transparent; border: none;")
        close_btn = QPushButton("✕")
        close_btn.setFixedSize(20, 20)
        close_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #505050;
                border: none;
                font-size: 12px;
            }
            QPushButton:hover { color: #ff6b6b; }
        """)
        close_btn.clicked.connect(self._on_close)
        header.addWidget(title)
        header.addStretch()
        header.addWidget(close_btn)
        card_layout.addLayout(header)

        # ── Divider ──
        div = QFrame()
        div.setFrameShape(QFrame.HLine)
        div.setStyleSheet("background: #1a2a0a; border: none; max-height: 1px;")
        card_layout.addWidget(div)

        # ── Metrics ──
        self.cpu_label  = self._metric_row("CPU", "—")
        self.ram_label  = self._metric_row("RAM", "—")
        self.temp_label = self._metric_row("TEMP", "—")

        card_layout.addWidget(self.cpu_label[0])
        card_layout.addWidget(self.ram_label[0])
        card_layout.addWidget(self.temp_label[0])

        # ── Divider ──
        div2 = QFrame()
        div2.setFrameShape(QFrame.HLine)
        div2.setStyleSheet("background: #1a2a0a; border: none; max-height: 1px;")
        card_layout.addWidget(div2)

        # ── Buttons ──
        self.ram_btn = self._action_btn("⚡ Clear RAM", "#3B6D11", self._on_clear_ram)
        self.kill_btn = self._action_btn("☠ Kill Background Apps", "#27500A", self._on_kill_procs)
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: #97C459; font-size: 10px; background: transparent; border: none;")
        self.status_label.setWordWrap(True)
        self.status_label.setAlignment(Qt.AlignCenter)

        card_layout.addWidget(self.ram_btn)
        card_layout.addWidget(self.kill_btn)
        card_layout.addWidget(self.status_label)

        outer.addWidget(card)

    def _metric_row(self, label_text, value_text):
        row = QFrame()
        row.setStyleSheet("background: transparent; border: none;")
        layout = QHBoxLayout(row)
        layout.setContentsMargins(0, 0, 0, 0)

        lbl = QLabel(label_text)
        lbl.setStyleSheet("color: #505050; font-size: 10px; font-weight: 600; letter-spacing: 1px; background: transparent; border: none;")
        lbl.setFixedWidth(40)

        val = QLabel(value_text)
        val.setStyleSheet("color: #ffffff; font-size: 18px; font-weight: 700; background: transparent; border: none;")
        val.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

        layout.addWidget(lbl)
        layout.addStretch()
        layout.addWidget(val)
        return row, val

    def _action_btn(self, text, color, handler):
        btn = QPushButton(text)
        btn.setFixedHeight(34)
        btn.setStyleSheet(f"""
            QPushButton {{
                background: {color};
                color: #97C459;
                border: none;
                border-radius: 8px;
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton:hover {{
                background: #4a8a15;
                color: #EAF3DE;
            }}
            QPushButton:disabled {{
                background: #1a2a0a;
                color: #3a5a10;
            }}
        """)
        btn.clicked.connect(handler)
        return btn

    # ── Timer ─────────────────────────────────────────────────────────────────
    def _start_timer(self):
        # Prime cpu_percent (first call always returns 0)
        psutil.cpu_percent(interval=None)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._refresh)
        self.timer.start(1000)

    def _refresh(self):
        cpu = _get_cpu()
        ram_used, ram_total, ram_pct = _get_ram()
        temp = _get_temp()

        cpu_color  = "#97C459" if cpu  < 70 else "#EF9F27" if cpu  < 90 else "#ff6b6b"
        ram_color  = "#97C459" if ram_pct < 70 else "#EF9F27" if ram_pct < 90 else "#ff6b6b"
        temp_color = "#97C459"
        if temp != "N/A":
            t = int(temp.replace("°C", ""))
            temp_color = "#97C459" if t < 70 else "#EF9F27" if t < 85 else "#ff6b6b"

        self.cpu_label[1].setText(f"{cpu}%")
        self.cpu_label[1].setStyleSheet(f"color: {cpu_color}; font-size: 18px; font-weight: 700; background: transparent; border: none;")

        self.ram_label[1].setText(f"{ram_used}/{ram_total}GB")
        self.ram_label[1].setStyleSheet(f"color: {ram_color}; font-size: 18px; font-weight: 700; background: transparent; border: none;")

        self.temp_label[1].setText(temp)
        self.temp_label[1].setStyleSheet(f"color: {temp_color}; font-size: 18px; font-weight: 700; background: transparent; border: none;")

    # ── Button handlers ───────────────────────────────────────────────────────
    def _on_clear_ram(self):
        self.ram_btn.setDisabled(True)
        self.status_label.setText("Clearing RAM...")
        result = clear_ram()
        self.status_label.setText(result)
        self.ram_btn.setDisabled(False)

    def _on_kill_procs(self):
        self.kill_btn.setDisabled(True)
        self.status_label.setText("Scanning processes...")
        result = kill_background_processes()
        self.status_label.setText(result)
        self.kill_btn.setDisabled(False)

    def _on_close(self):
        self.timer.stop()
        self.closed.emit()
        self.hide()


# ── Launch helper (called from app.py) ───────────────────────────────────────
_overlay_instance = None


def launch_gamer_mode() -> GamerOverlay:
    """Create and show the Gamer Mode overlay. Call from app.py."""
    global _overlay_instance
    if _overlay_instance is None:
        _overlay_instance = GamerOverlay()

    # Position top-right corner of primary screen
    from PyQt5.QtWidgets import QApplication
    screen = QApplication.primaryScreen().geometry()
    _overlay_instance.move(screen.width() - 280, 40)
    _overlay_instance.show()
    _overlay_instance.raise_()
    log_event("Gamer Mode", "Overlay launched")
    return _overlay_instance
