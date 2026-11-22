"""Тесты OperationSys. subprocess.run подменяется — реальные команды НЕ выполняются."""
import subprocess

import pytest

from os_ops import OperationSys, OS, ShutdownError, detect_os


# ---------- вспомогательная фикстура ----------

@pytest.fixture
def mock_subprocess(monkeypatch):
    """
    Подменяет subprocess.run фейком, который:
    - записывает все вызовы в список calls
    - возвращает объект, похожий на CompletedProcess
    - НЕ запускает реальные команды
    """
    calls = []

    def fake_run(cmd, **kwargs):
        calls.append({"cmd": cmd, "kwargs": kwargs})
        return subprocess.CompletedProcess(args=cmd, returncode=0)

    monkeypatch.setattr(subprocess, "run", fake_run)
    return calls


# ---------- detect_os ----------

def test_detect_os_windows(monkeypatch):
    monkeypatch.setattr("sys.platform", "win32")
    assert detect_os() is OS.WINDOWS


def test_detect_os_linux(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    assert detect_os() is OS.LINUX


def test_detect_os_unknown(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    assert detect_os() is OS.UNKNOW


# ---------- schedule_shutdown на Windows ----------

def test_schedule_windows(monkeypatch, mock_subprocess):
    monkeypatch.setattr("sys.platform", "win32")
    ops = OperationSys()

    ops.schedule_shutdown(120)

    assert len(mock_subprocess) == 1
    assert mock_subprocess[0]["cmd"] == ["shutdown", "-s", "-f", "-t", "120"]


# ---------- schedule_shutdown на Linux (НОВАЯ ЛОГИКА: seconds // 60) ----------

def test_schedule_linux_exact_minutes(monkeypatch, mock_subprocess):
    """300 секунд ровно = 5 минут → shutdown -h +5."""
    monkeypatch.setattr("sys.platform", "linux")
    ops = OperationSys()

    ops.schedule_shutdown(300)

    assert mock_subprocess[0]["cmd"] == ["shutdown", "-h", "+5"]


def test_schedule_linux_one_minute(monkeypatch, mock_subprocess):
    """Ровно 60 секунд → 1 минута."""
    monkeypatch.setattr("sys.platform", "linux")
    ops = OperationSys()

    ops.schedule_shutdown(60)

    assert mock_subprocess[0]["cmd"] == ["shutdown", "-h", "+1"]



def test_schedule_linux_less_than_minute_gives_zero(monkeypatch, mock_subprocess):
    monkeypatch.setattr("sys.platform", "linux")
    ops = OperationSys()

    ops.schedule_shutdown(30)

    assert mock_subprocess[0]["cmd"] == ["shutdown", "-h", "+0"]


def test_schedule_linux_exactly_one_second(monkeypatch, mock_subprocess):
    """1 секунда → +0."""
    monkeypatch.setattr("sys.platform", "linux")
    ops = OperationSys()

    ops.schedule_shutdown(1)

    assert mock_subprocess[0]["cmd"] == ["shutdown", "-h", "+0"]


# ---------- отмена ----------

def test_cancel_windows(monkeypatch, mock_subprocess):
    monkeypatch.setattr("sys.platform", "win32")
    ops = OperationSys()

    ops.cancel_shutdown()

    assert mock_subprocess[0]["cmd"] == ["shutdown", "/a"]


def test_cancel_linux(monkeypatch, mock_subprocess):
    monkeypatch.setattr("sys.platform", "linux")
    ops = OperationSys()

    ops.cancel_shutdown()

    assert mock_subprocess[0]["cmd"] == ["shutdown", "-c"]


def test_cancel_linux_raises_on_failure(monkeypatch):
    """Если shutdown -c вернул ошибку — бросаем ShutdownError."""
    monkeypatch.setattr("sys.platform", "linux")

    def fake_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1, cmd=cmd, stderr="No scheduled shutdown"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    ops = OperationSys()

    with pytest.raises(ShutdownError, match="Не удалось отменить"):
        ops.cancel_shutdown()


# ---------- ошибки ----------

def test_schedule_raises_on_zero(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    ops = OperationSys()

    with pytest.raises(ValueError):
        ops.schedule_shutdown(0)


def test_schedule_raises_on_negative(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")
    ops = OperationSys()

    with pytest.raises(ValueError):
        ops.schedule_shutdown(-5)


def test_schedule_raises_on_unknown_os(monkeypatch):
    monkeypatch.setattr("sys.platform", "darwin")
    ops = OperationSys()

    with pytest.raises(ShutdownError):
        ops.schedule_shutdown(60)


def test_schedule_raises_on_command_failure(monkeypatch):
    """Если shutdown вернул ненулевой код — бросаем ShutdownError."""
    monkeypatch.setattr("sys.platform", "linux")

    def fake_run(cmd, **kwargs):
        raise subprocess.CalledProcessError(
            returncode=1, cmd=cmd, stderr="permission denied"
        )

    monkeypatch.setattr(subprocess, "run", fake_run)
    ops = OperationSys()

    with pytest.raises(ShutdownError, match="permission denied"):
        ops.schedule_shutdown(60)


def test_schedule_raises_when_command_not_found(monkeypatch):
    monkeypatch.setattr("sys.platform", "linux")

    def fake_run(cmd, **kwargs):
        raise FileNotFoundError()

    monkeypatch.setattr(subprocess, "run", fake_run)
    ops = OperationSys()

    with pytest.raises(ShutdownError, match="не найдена"):
        ops.schedule_shutdown(60)