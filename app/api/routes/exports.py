from datetime import date, timedelta

from fastapi import APIRouter, Depends, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.services import export_service, report_service

router = APIRouter(prefix="/api/v1/exports", tags=["exports"])


@router.get("/excel")
async def excel(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    period: str = Query(default="month"),
    date_from: date | None = None,
    date_to: date | None = None,
) -> StreamingResponse:
    """Excel: Сводка + Операции + История изменений."""
    report = await report_service.build_report(db, period, date_from, date_to)
    frm = report.date_from
    to_excl = report.date_to + timedelta(days=1)
    buf = await export_service.build_excel(db, report, frm, to_excl)
    name = f"meat_report_{report.date_from}_{report.date_to}.xlsx"
    return StreamingResponse(
        buf,
        media_type=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
        headers={"Content-Disposition": f'attachment; filename="{name}"'},
    )
