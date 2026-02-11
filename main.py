# -*- coding:utf-8 -*-
import ctypes
import json
import threading
import time
from pathlib import Path
from datetime import datetime
from curl_cffi import requests

from PySide6.QtCore import QObject, QPoint, QTimer, Qt, Signal, Slot
from PySide6.QtGui import QAction
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QMenu,
    QStyle,
    QSystemTrayIcon,
    QWidget,
)


class Scraper:
    def __init__(self):
        self.user_id = None
        self.cookies = None
        self.load_info()

    def load_info(self):
        try:
            with open("user_id.ini") as f:
                self.user_id = f.read()
            with open("cookies.ini") as f:
                self.cookies = f.read()
        except Exception as e:
            self.user_id = None
            self.cookies = None

    def request_user_quote(self):
        try:
            url = "https://api.ikuncode.cc/api/user/self"
            headers = {
                "cookie": self.cookies,
                "new-api-user": self.user_id,
                "referer": "https://api.ikuncode.cc/console",
            }
            response = requests.get(url, headers=headers)
            data = response.json()["data"]
            return data
        except Exception as e:
            return None

    def request_user_state(self):
        try:
            end_date = datetime.now()
            start_date = datetime(year=end_date.year, month=end_date.month, day=end_date.day, hour=0, minute=0, second=0)
            url = f"https://api.ikuncode.cc/api/log/self/stat?type=0&token_name=&model_name=&start_timestamp={int(start_date.timestamp())}&end_timestamp={int(end_date.timestamp())}&group="
            headers = {
                "cookie": self.cookies,
                "new-api-user": self.user_id,
                "referer": "https://api.ikuncode.cc/console",
            }
            response = requests.get(url, headers=headers)
            data = response.json()["data"]
            return data
        except Exception as e:
            return None

    def quota_to_balance(self, quato):
        return str(round(quato * 0.000002, 2))


class FloatingMonitorWidget(QWidget):
    def __init__(self):
        super().__init__()
        self._drag_active = False
        self._drag_offset = QPoint()
        self._position_file = Path("monitor_position.json")
        self._setup_window()
        self._setup_ui()
        self._setup_topmost_maintainer()

    def _setup_window(self):
        self.setWindowTitle("IKUN Monitor")
        self.setWindowFlags(
            Qt.Window
            | Qt.FramelessWindowHint
            | Qt.WindowStaysOnTopHint
            | Qt.WindowDoesNotAcceptFocus
            | Qt.NoDropShadowWindowHint
        )
        self.setAttribute(Qt.WA_TranslucentBackground, True)
        self.setAttribute(Qt.WA_ShowWithoutActivating, True)
        self.setFixedSize(290, 38)

    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 5, 8, 5)
        layout.setSpacing(6)

        self.balance_title = QLabel("\u4f59\u989d")
        self.balance_title.setObjectName("metricTitle")
        self.balance_value = QLabel("\u00a50.00")
        self.balance_value.setObjectName("metricValue")

        self.consume_title = QLabel("\u4eca\u65e5\u6d88\u8017")
        self.consume_title.setObjectName("metricTitle")
        self.consume_value = QLabel("\u00a50.00")
        self.consume_value.setObjectName("consumeValue")

        self.balance_title.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.balance_value.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.consume_title.setAttribute(Qt.WA_TransparentForMouseEvents, True)
        self.consume_value.setAttribute(Qt.WA_TransparentForMouseEvents, True)

        self.setStyleSheet(
            "QWidget {"
            "  background-color: rgba(18, 18, 18, 142);"
            "  border: 1px solid rgba(255, 255, 255, 30);"
            "  border-radius: 10px;"
            "}"
            "QLabel#metricTitle {"
            "  color: rgba(255,255,255,170);"
            "  font-size: 11px;"
            "  padding: 2px 6px;"
            "  border-radius: 7px;"
            "  background-color: rgba(255,255,255,20);"
            "}"
            "QLabel#metricValue {"
            "  color: #ffffff;"
            "  font-size: 12px;"
            "  font-weight: 700;"
            "  padding: 2px 7px;"
            "  border-radius: 7px;"
            "  background-color: rgba(64,140,255,35);"
            "}"
            "QLabel#consumeValue {"
            "  color: #ffd6d6;"
            "  font-size: 12px;"
            "  font-weight: 700;"
            "  padding: 2px 7px;"
            "  border-radius: 7px;"
            "  background-color: rgba(255,100,100,32);"
            "}"
        )

        layout.addWidget(self.balance_title)
        layout.addWidget(self.balance_value)
        layout.addWidget(self.consume_title)
        layout.addWidget(self.consume_value)

    def _setup_topmost_maintainer(self):
        self._topmost_timer = QTimer(self)
        self._topmost_timer.setInterval(350)
        self._topmost_timer.timeout.connect(self._ensure_topmost)
        self._topmost_timer.start()

    def _ensure_topmost(self):
        if not self.isVisible():
            return
        if not hasattr(ctypes, "windll"):
            return

        hwnd = int(self.winId())
        if not hwnd:
            return

        hwnd_topmost = -1
        swp_nosize = 0x0001
        swp_nomove = 0x0002
        swp_noactivate = 0x0010
        swp_showwindow = 0x0040
        flags = swp_nosize | swp_nomove | swp_noactivate | swp_showwindow
        ctypes.windll.user32.SetWindowPos(hwnd, hwnd_topmost, 0, 0, 0, 0, flags)

    @Slot(str)
    def set_balance(self, balance_text: str):
        self.balance_value.setText(balance_text)

    @Slot(str)
    def set_consume(self, consume_text: str):
        self.consume_value.setText(consume_text)

    @Slot(str, str)
    def set_values(self, balance_text: str, consume_text: str):
        self.set_balance(balance_text)
        self.set_consume(consume_text)

    def restore_saved_position(self) -> bool:
        if not self._position_file.exists():
            return False

        try:
            data = json.loads(self._position_file.read_text(encoding="utf-8"))
            x = int(data.get("x"))
            y = int(data.get("y"))
        except Exception:
            return False

        self.move(x, y)
        return True

    def save_current_position(self):
        payload = {"x": self.x(), "y": self.y()}
        self._position_file.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_active = True
            self._drag_offset = event.globalPosition().toPoint() - self.frameGeometry().topLeft()
            event.accept()
            return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if self._drag_active and (event.buttons() & Qt.LeftButton):
            target_pos = event.globalPosition().toPoint() - self._drag_offset
            self.move(target_pos)
            self._ensure_topmost()
            event.accept()
            return
        super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self._drag_active = False
            self.save_current_position()
            self._ensure_topmost()
            event.accept()
            return
        super().mouseReleaseEvent(event)

    def showEvent(self, event):
        super().showEvent(event)
        QTimer.singleShot(0, self._ensure_topmost)
        QTimer.singleShot(120, self._ensure_topmost)


class TrayAppController:
    def __init__(self, app: QApplication):
        self.app = app
        self.monitor_widget = FloatingMonitorWidget()
        self.signals = MonitorUpdateSignals()
        self._bind_signals()
        self.tray_icon = self._create_tray_icon()
        self.scraper = Scraper()
        thread = threading.Thread(target=self.update_process)
        thread.daemon = True
        thread.start()

    def update_process(self):
        while 1:
            try:
                quota_data = self.scraper.request_user_quote()
                balance = self.scraper.quota_to_balance(quota_data.get("quota"))
            except Exception as e:
                balance = "异常"
            try:
                stat_data = self.scraper.request_user_state()
                used_balance = self.scraper.quota_to_balance(stat_data.get("quota"))
            except Exception as e:
                used_balance = "异常"
            self.set_metrics(balance, used_balance)
            time.sleep(60)

    def _bind_signals(self):
        self.signals.balance_changed.connect(self.monitor_widget.set_balance)
        self.signals.consume_changed.connect(self.monitor_widget.set_consume)
        self.signals.metrics_changed.connect(self.monitor_widget.set_values)

    def set_balance(self, balance_text: str):
        self.signals.balance_changed.emit(balance_text)

    def set_consume(self, consume_text: str):
        self.signals.consume_changed.emit(consume_text)

    def set_metrics(self, balance_text: str, consume_text: str):
        self.signals.metrics_changed.emit(balance_text, consume_text)

    def _create_tray_icon(self):
        icon = self.app.style().standardIcon(QStyle.SP_ComputerIcon)
        tray = QSystemTrayIcon(icon, self.app)
        tray.setToolTip("IKUN Monitor")

        menu = QMenu()

        toggle_action = QAction("\u663e\u793a/\u9690\u85cf\u76d1\u63a7", tray)
        toggle_action.triggered.connect(self._toggle_monitor)
        menu.addAction(toggle_action)

        reset_pos_action = QAction("\u91cd\u7f6e\u4f4d\u7f6e", tray)
        reset_pos_action.triggered.connect(self._reset_position)
        menu.addAction(reset_pos_action)

        quit_action = QAction("\u9000\u51fa", tray)
        quit_action.triggered.connect(self.app.quit)
        menu.addAction(quit_action)

        tray.setContextMenu(menu)
        tray.show()
        return tray

    def _toggle_monitor(self):
        if self.monitor_widget.isVisible():
            self.monitor_widget.hide()
        else:
            self.monitor_widget.show()
            self.monitor_widget._ensure_topmost()

    def _reset_position(self):
        self._place_default_position()
        self.monitor_widget.show()
        self.monitor_widget.save_current_position()
        self.monitor_widget._ensure_topmost()

    def _place_default_position(self):
        screen = QApplication.primaryScreen()
        if not screen:
            return
        avail_geo = screen.availableGeometry()
        margin = 20
        x = avail_geo.right() - self.monitor_widget.width() - margin
        y = avail_geo.top() + margin
        self.monitor_widget.move(x, y)

    def start(self):
        self.set_metrics("\u00a50.00", "\u00a50.00")
        if not self.monitor_widget.restore_saved_position():
            self._place_default_position()
            self.monitor_widget.save_current_position()
        self.monitor_widget.show()
        self.app.aboutToQuit.connect(self.monitor_widget.save_current_position)


class MonitorUpdateSignals(QObject):
    balance_changed = Signal(str)
    consume_changed = Signal(str)
    metrics_changed = Signal(str, str)


def update_monitor_metrics(controller: TrayAppController, balance_text: str, consume_text: str):
    controller.set_metrics(balance_text, consume_text)


def main():
    app = QApplication([])
    app.setQuitOnLastWindowClosed(False)

    controller = TrayAppController(app)
    controller.start()

    app.exec()


if __name__ == "__main__":
    main()
