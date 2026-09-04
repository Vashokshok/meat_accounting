from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.report import ReportOut
from app.services import report_service

router = APIRouter(prefix="/api/v1/reports", tags=["reports"])


@router.get("", response_model=ReportOut)
async def report(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    period: str = Query(default="today"),
    date_from: date | None = None,
    date_to: date | None = None,
) -> ReportOut:
    """Отчёт: today/week/month/custom."""
    return await report_service.build_report(db, period, date_from, date_to)
