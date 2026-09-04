from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.operation import Operation
from app.models.operation_change import OperationChange


def snapshot(op: Operation) -> dict[str, Any]:
    """Снимок операции для аудита."""
    return {
        "type": op.type,
        "meat_type": op.meat_type,
        "quantity": str(op.quantity),
        "franchise_id": op.franchise_id,
        "comment": op.comment,
        "status": op.status,
        "operation_date": op.operation_date.isoformat(),
    }


async def log_change(
    db: AsyncSession, op_id: int, user_id: int, old: dict, new: dict
) -> None:
    """Запись было → стало."""
    db.add(
        OperationChange(
            operation_id=op_id, changed_by=user_id, old_data=old, new_data=new
        )
    )
