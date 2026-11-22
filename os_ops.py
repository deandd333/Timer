from __future__ import annotations
import logging
import os
import subprocess
import sys
from enum import Enum

logger = logging.getLogger(__name__)

class OS(Enum):
    WINDOWS = 'W'
    LINUX = 'L'
    UNKNOW = '?'

class ShutdownError(RuntimeError):
    pass

def detect_os() -> OS:
    if sys.platform == 'win32':
        return OS.WINDOWS
    if sys.platform.startswith('linux'):
        return OS.LINUX
    return OS.UNKNOW

class OperationSys:
    def __init__(self) -> None:
        self.osp = detect_os()


    def schedule_shutdown(self,seconds: int) -> None:
        if seconds <= 0:
            raise ValueError("Время до выключения должно быть положительным")

        if self.osp is OS.WINDOWS:
            self._windows_schedule(seconds)
        elif self.osp is OS.LINUX:
            self._linux_schedule(seconds)
        else:
            raise ShutdownError(f"ОС не поддерживается: {sys.platform}")

    
    def cancel_shutdown(self) -> None:
        if self.osp is OS.WINDOWS:
            self._windows_cancel()
        elif self.osp is OS.LINUX:
            self._linux_cancel()
        else:
            raise ShutdownError(f"ОС не поддерживается: {sys.platform}")


    def _windows_schedule(self, seconds: int) -> None:
        self._run(["shutdown", "-s", "-f", "-t", str(seconds)])


    def _windows_cancel(self) -> None:
        self._run(
            ["shutdown", "/a"],
            encoding="cp866",)


    def _linux_schedule(self, seconds: int) -> None:
        minutes = seconds // 60
        self._run(["shutdown", "-h", f"+{minutes}"])


    def _linux_cancel(self) -> None:
        try:
            self._run(["shutdown", "-c"], check=True)
        except ShutdownError as exc:
            raise ShutdownError(
            "Не удалось отменить: таймер не запланирован или нет прав"
        ) from exc

    @staticmethod
    def _run(
        cmd: list[str],
        *,
        check: bool = True,
        encoding: str = "utf-8",) -> None:
        try:
            subprocess.run(
                cmd,
                shell=False,
                check=check,
                capture_output=True,
                text=True,
                encoding=encoding,
                errors="replace",
            )
        except FileNotFoundError as exc:
            raise ShutdownError(f"Команда не найдена: {cmd[0]}") from exc
        except subprocess.CalledProcessError as exc:
            stderr = (exc.stderr or exc.stdout or "").strip()
            raise ShutdownError(
                f"Код {exc.returncode}: {stderr or 'без вывода'}"
            ) from exc        