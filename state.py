from __future__ import annotations

import logging 
from pathlib import Path

logger = logging.getLogger(__name__)

STATE_FILE : Path = Path.home() / '.shutdown_timer.state'


def save_state(shutdown_ts: float)-> None:
    if not shutdown_ts:
        return
    try:
        STATE_FILE.write_text(str(shutdown_ts), encoding="utf-8")
    except OSError as exc:
        logger.warning("Не удалось сохранить состояние: %s", exc)


def load_state() -> float | None:
    if not STATE_FILE.exists():
        return None
    try:
        raw = STATE_FILE.read_text(encoding='utf-8').strip()
        return float(raw)
    except (OSError, ValueError) as exc:
        logger.warning("Повреждённый файл состояния (%s), удаляю", exc)
        clear_state()
        return None
    

def clear_state() -> None:
    try:
        STATE_FILE.unlink(missing_ok=True)
    except OSError as exc:
        logger.warning("Не удалось удалить файл состояния: %s", exc)  

                   