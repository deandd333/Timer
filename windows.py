from __future__ import annotations

import logging
import time

from PyQt5.QtCore import QTime, QTimer
from PyQt5.QtGui import QKeySequence
from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QMessageBox,
    QShortcut,
)

import state
from os_ops import OperationSys, ShutdownError
from ui_main import Ui_MainWindow

logger = logging.getLogger(__name__)

class MainWindow(QMainWindow, Ui_MainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setupUi(self)

        self.shutdown_ts: float = 0.0
        self.remaining_seconds: int = 0
        self.os_ops = OperationSys()

        self._setup_widgets()
        self._setup_timers()
        self._setup_shortcuts()
        self._restore_state()


    def _setup_widgets(self) -> None:
        self.setWindowTitle("Таймер")
        self.spinBox.setSuffix(" мин")
        self._refresh_clock_label()


    def _setup_timers(self) -> None:
        self.countdown_timer = QTimer(self)
        self.countdown_timer.timeout.connect(self.tick)

        self.clock_timer = QTimer(self)
        self.clock_timer.timeout.connect(self._refresh_clock_label)
        self.clock_timer.start(1000)


    def _setup_shortcuts(self) -> None:
        self.pushButton.clicked.connect(self.shutdown)
        self.pushButton_2.clicked.connect(self.shutdown_end)

        QShortcut(QKeySequence("Return"), self, activated = self.shutdown)
        QShortcut(QKeySequence("Esc"), self, activated = self.shutdown_end) 


    def shutdown(self) -> None:
        """Запуск таймера обратного отсчёта."""
        if self.countdown_timer.isActive():
            return

        minutes = self.spinBox.value()
        if minutes <= 0:
            self._confirm_immediate_shutdown()
            return

        self.remaining_seconds = minutes * 60
        self.shutdown_ts = time.time() + self.remaining_seconds

        try:
            self.os_ops.schedule_shutdown(self.remaining_seconds)
        except ShutdownError as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))
            return

        state.save_state(self.shutdown_ts)
        self.clock_timer.stop()
        self._update_countdown_label()
        self.countdown_timer.start(1000)


    def shutdown_end(self) -> None:
        """Отмена запланированного выключения."""
        self.spinBox.setValue(0)
        try:
            self.os_ops.cancel_shutdown()
        except ShutdownError as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))
            return
        finally:
            self._reset_countdown()


    def _confirm_immediate_shutdown(self) -> None:
        reply = QMessageBox.question(
            self,
            "Подтверждение",
            "Вы действительно хотите завершить работу?",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No,
        )
        if reply != QMessageBox.Yes:
            return
        try:
            self.os_ops.schedule_shutdown(1)
        except ShutdownError as exc:
            QMessageBox.critical(self, "Ошибка", str(exc))


    def tick(self) -> None:
        self.remaining_seconds = int(self.shutdown_ts - time.time())
        if self.remaining_seconds <= 0:
            self.countdown_timer.stop()
            state.clear_state()
            return
        self._update_countdown_label()


    def _update_countdown_label(self) -> None:
        minutes, seconds = divmod(self.remaining_seconds, 60)
        self.label.setText(f"Вкл: {minutes} мин {seconds:02d} сек")


    def _refresh_clock_label(self) -> None:
        self.label.setText("Время: " + QTime.currentTime().toString("hh:mm:ss"))


    def _reset_countdown(self) -> None:
        self.countdown_timer.stop()
        self.shutdown_ts = 0.0
        self.remaining_seconds = 0
        state.clear_state()
        self._refresh_clock_label()
        self.clock_timer.start(1000)


    def _restore_state(self) -> None:
        ts = state.load_state()
        if ts is None:
            return
        self.shutdown_ts = ts
        self.remaining_seconds = int(ts - time.time())
        if self.remaining_seconds > 0:
            self.clock_timer.stop()
            self._update_countdown_label()
            self.countdown_timer.start(1000)
        else:
            state.clear_state()


    def closeEvent(self, event) -> None:
        if self.countdown_timer.isActive():
            state.save_state(self.shutdown_ts)
        super().closeEvent(event)