import calendar
from datetime import date, timedelta
from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operation import Operation
from app.schemas.report import MeatReport, ReportOut
from app.utils.dates import today
from app.utils.enums import MeatType, OperationStatus, OperationType

ACTIVE = OperationStatus.ACTIVE.value


def resolve_range(
    period: str, date_from: date | None, date_to: date | None
) -> tuple[date, date]:
    """Границы [from, to) по периоду в TZ точки."""
    now = today()
    if period == "today":
        return now, now + timedelta(days=1)
    if period == "week":
        monday = now - timedelta(days=now.weekday())
        return monday, monday + timedelta(days=7)
    if period == "month":
        first = now.replace(day=1)
        last = calendar.monthrange(now.year, now.month)[1]
        return first, now.replace(day=last) + timedelta(days=1)
    if date_from is None or date_to is None:
        raise HTTPException(
            status_code=400, detail="Для custom укажите date_from и date_to"
        )
    if date_from > date_to:
        raise HTTPException(status_code=400, detail="date_from позже date_to")
    return date_from, date_to + timedelta(days=1)


async def _opening(db: AsyncSession, frm: date) -> dict[str, Decimal]:
    """Остатки на начало периода."""
    rows = (
        await db.execute(
            select(
                Operation.meat_type,
                func.coalesce(
                    func.sum(
                        Operation.quantity
                        * case(
                            (Operation.type == OperationType.INCOMING.value, 1),
                            else_=-1,
                        )
                    ),
                    0,
                ),
            )
            .where(Operation.status == ACTIVE, Operation.operation_date < frm)
            .group_by(Operation.meat_type)
        )
    ).all()
    return {m.value: Decimal(0) for m in MeatType} | {
        meat: Decimal(val) for meat, val in rows
    }


async def _period_sums(
    db: AsyncSession, frm: date, to_excl: date
) -> dict[tuple[str, str], Decimal]:
    """Суммы по (мясо, тип) внутри периода."""
    rows = (
        await db.execute(
            select(
                Operation.meat_type,
                Operation.type,
                func.coalesce(func.sum(Operation.quantity), 0),
            )
            .where(
                Operation.status == ACTIVE,
                Operation.operation_date >= frm,
                Operation.operation_date < to_excl,
            )
            .group_by(Operation.meat_type, Operation.type)
        )
    ).all()
    return {(meat, typ): Decimal(val) for meat, typ, val in rows}


async def build_report(
    db: AsyncSession, period: str, date_from: date | None, date_to: date | None
) -> ReportOut:
    """Отчёт: остаток на начало + движение + остаток на конец."""
    frm, to_excl = resolve_range(period, date_from, date_to)
    opening = await _opening(db, frm)
    sums = await _period_sums(db, frm, to_excl)

    items = []
    for meat in MeatType:
        inc = sums.get((meat.value, OperationType.INCOMING.value), Decimal(0))
        spit = sums.get((meat.value, OperationType.SPIT.value), Decimal(0))
        wo = sums.get((meat.value, OperationType.WRITE_OFF.value), Decimal(0))
        conv = sums.get((meat.value, OperationType.CONVECTION.value), Decimal(0))
        fr = sums.get((meat.value, OperationType.FRANCHISE.value), Decimal(0))
        items.append(
            MeatReport(
                meat_type=meat.value,
                opening=float(opening[meat.value]),
                incoming=float(inc),
                spit=float(spit),
                write_off=float(wo),
                convection=float(conv),
                franchise=float(fr),
                closing=float(opening[meat.value] + inc - spit - wo - conv - fr),
            )
        )
    return ReportOut(date_from=frm, date_to=to_excl - timedelta(days=1), items=items)
