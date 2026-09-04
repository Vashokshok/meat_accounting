from datetime import date
from zoneinfo import ZoneInfo

# Часовой пояс точки (решён на гриллинге)
TZ_NAME = "Europe/Moscow"
TZ = ZoneInfo(TZ_NAME)


def today() -> date:
    """Текущая бизнес-дата точки."""
    from datetime import datetime

    return datetime.now(TZ).date()
