import io
from datetime import date

from openpyxl import Workbook
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.franchise import Franchise
from app.models.operation import Operation
from app.models.operation_change import OperationChange
from app.models.user import User
from app.schemas.report import ReportOut


def _fill_sheet(ws, headers: list[str], rows: list[list]) -> None:
    """Шапка + строки в лист."""
    ws.append(headers)
    for row in rows:
        ws.append(row)


async def build_excel(
    db: AsyncSession, report: ReportOut, frm: date, to_excl: date
) -> io.BytesIO:
    """Excel из report_service (без своей математики)."""
    wb = Workbook()

    ws = wb.active
    ws.title = "Сводка"
    ws.append(["Период", f"{frm.isoformat()} — {report.date_to.isoformat()}"])
    ws.append([])
    _fill_sheet(
        ws,
        [
            "Мясо",
            "На начало",
            "Приход",
            "Вертель",
            "Списание",
            "Конвектомат",
            "Франшиза",
            "На конец",
        ],
        [
            [
                i.meat_type,
                i.opening,
                i.incoming,
                i.spit,
                i.write_off,
                i.convection,
                i.franchise,
                i.closing,
            ]
            for i in report.items
        ],
    )

    ops = (
        await db.execute(
            select(
                Operation,
                User.display_name,
                User.username,
                Franchise.name,
            )
            .join(User, User.id == Operation.created_by)
            .outerjoin(Franchise, Franchise.id == Operation.franchise_id)
            .where(Operation.operation_date >= frm, Operation.operation_date < to_excl)
            .order_by(Operation.id)
        )
    ).all()
    ws2 = wb.create_sheet("Операции")
    _fill_sheet(
        ws2,
        [
            "ID",
            "Дата",
            "Тип",
            "Мясо",
            "Кг",
            "ID франшизы",
            "Статус",
            "Автор",
            "Коммент",
            "Название франшизы",
            "Автор ID",
            "Создано",
            "Обновлено",
        ],
        [
            [
                o.id,
                o.operation_date.isoformat(),
                o.type,
                o.meat_type,
                float(o.quantity),
                o.franchise_id,
                o.status,
                display_name or username,
                o.comment,
                franchise_name,
                o.created_by,
                o.created_at.isoformat(),
                o.updated_at.isoformat(),
            ]
            for o, display_name, username, franchise_name in ops
        ],
    )

    changes = (
        await db.execute(
            select(
                OperationChange,
                User.display_name,
                User.username,
                Operation.operation_date,
            )
            .join(Operation, Operation.id == OperationChange.operation_id)
            .join(User, User.id == OperationChange.changed_by)
            .where(
                Operation.operation_date >= frm,
                Operation.operation_date < to_excl,
            )
            .order_by(OperationChange.id)
        )
    ).all()
    ws3 = wb.create_sheet("История изменений")
    _fill_sheet(
        ws3,
        [
            "ID",
            "Операция",
            "Кто",
            "Когда",
            "Было",
            "Стало",
            "Дата операции",
            "ID пользователя",
        ],
        [
            [
                c.id,
                c.operation_id,
                display_name or username,
                c.changed_at.isoformat(),
                str(c.old_data),
                str(c.new_data),
                operation_date.isoformat(),
                c.changed_by,
            ]
            for c, display_name, username, operation_date in changes
        ],
    )

    buf = io.BytesIO()
    wb.save(buf)
    buf.seek(0)
    return buf
