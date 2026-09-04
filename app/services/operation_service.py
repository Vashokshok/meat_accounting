from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import InsufficientStockError
from app.models.franchise import Franchise
from app.models.operation import Operation
from app.schemas.operation import OperationCreate
from app.services import stock_service
from app.utils.enums import EXPENSE_TYPES, OperationStatus


async def create_operation(
    db: AsyncSession, data: OperationCreate, user_id: int
) -> Operation:
    """Создание с проверкой остатка в одной транзакции."""
    if data.type in EXPENSE_TYPES:
        await stock_service.lock_meat(db, data.meat_type.value)
        stock = await stock_service.get_stock_for(db, data.meat_type)
        if stock < data.quantity:
            raise InsufficientStockError(str(stock))
    if data.franchise_id is not None:
        fr = (
            await db.execute(select(Franchise).where(Franchise.id == data.franchise_id))
        ).scalar_one_or_none()
        if fr is None:
            raise HTTPException(status_code=404, detail="Франшиза не найдена")
        if not fr.is_active:
            raise HTTPException(status_code=400, detail="Франшиза отключена")

    op = Operation(
        type=data.type.value,
        meat_type=data.meat_type.value,
        quantity=data.quantity,
        franchise_id=data.franchise_id,
        comment=data.comment,
        status=OperationStatus.ACTIVE.value,
        operation_date=data.operation_date,
        created_by=user_id,
    )
    db.add(op)
    await db.commit()
    await db.refresh(op)
    return op
