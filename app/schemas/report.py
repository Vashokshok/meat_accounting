from datetime import date
from enum import StrEnum

from pydantic import BaseModel


class ReportPeriod(StrEnum):
    """Готовые периоды отчёта."""

    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    CUSTOM = "custom"


class MeatReport(BaseModel):
    """Строка отчёта по одному виду мяса."""

    meat_type: str
    opening: float
    incoming: float
    spit: float
    write_off: float
    convection: float
    franchise: float
    closing: float


class ReportOut(BaseModel):
    date_from: date
    date_to: date
    items: list[MeatReport]
