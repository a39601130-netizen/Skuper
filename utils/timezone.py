"""
Утилиты для работы с часовым поясом.
Все даты/время в приложении должны быть по минскому времени.
"""
from datetime import date, datetime
from zoneinfo import ZoneInfo

MINSK_TZ = ZoneInfo("Europe/Minsk")


def now_minsk() -> datetime:
    """Текущее datetime по минскому времени."""
    return datetime.now(MINSK_TZ)


def today_minsk() -> date:
    """Текущая дата по минскому времени."""
    return now_minsk().date()
