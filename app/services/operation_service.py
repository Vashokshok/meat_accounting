from decimal import Decimal

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AlreadyCancelledError, InsufficientStockError
from app.models.franchise import Franchise
from app.models.operation import Operation
from app.schemas.operation import OperationCreate, OperationPatch
from app.services import stock_service
from app.services.audit_service import log_change, snapshot
from app.utils.enums import EXPENSE_TYPES, OperationStatus


def _effect(op_type: str, qty: Decimal) -> Decimal:
    """Влияние на склад: приход +, расход −."""
    return -qty if op_type in {t.value for t in EXPENSE_TYPES} else qty


async def _check_franchise(db: AsyncSession, franchise_id: int) -> None:
    """Франшиза существует и активна."""
    fr = (
        await db.execute(select(Franchise).where(Franchise.id == franchise_id))
    ).scalar_one_or_none()
    if fr is None:
        raise HTTPException(status_code=404, detail="Франшиза не найдена")
    if not fr.is_active:
        raise HTTPException(status_code=400, detail="Франшиза отключена")


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
        await _check_franchise(db, data.franchise_id)

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


async def _get_active(db: AsyncSession, op_id: int) -> Operation:
    """Операция для правки (отменённые править нельзя)."""
    op = (
        await db.execute(select(Operation).where(Operation.id == op_id))
    ).scalar_one_or_none()
    if op is None:
        raise HTTPException(status_code=404, detail="Операция не найдена")
    if op.status == OperationStatus.CANCELLED.value:
        raise HTTPException(status_code=400, detail="Отменённую операцию менять нельзя")
    return op


async def update_operation(
    db: AsyncSession, op_id: int, patch: OperationPatch, user_id: int
) -> Operation:
    """PATCH + аудит + перепроверка остатка одной транзакцией."""
    op = await _get_active(db, op_id)
    old = snapshot(op)
    sent = patch.model_fields_set

    new_type = patch.type.value if patch.type else op.type
    new_meat = patch.meat_type.value if patch.meat_type else op.meat_type
    new_qty = patch.quantity if patch.quantity is not None else op.quantity
    new_date = patch.operation_date or op.operation_date
    new_fr = patch.franchise_id if "franchise_id" in sent else op.franchise_id
    new_comment = patch.comment if "comment" in sent else op.comment

    if new_type == "FRANCHISE" and new_fr is None:
        raise HTTPException(status_code=400, detail="Для франшизы укажите franchise_id")
    if new_type != "FRANCHISE":
        new_fr = None
    if new_fr is not None:
        await _check_franchise(db, new_fr)

    # Лок по затронутым видам (сорт — от дедлока)
    for meat in sorted({op.meat_type, new_meat}):
        await stock_service.lock_meat(db, meat)

    # Остаток после замены: текущий − старый эффект + новый
    for meat in {op.meat_type, new_meat}:
        cur = await stock_service.get_stock_for(db, meat)
        after = cur
        if op.meat_type == meat:
            after -= _effect(op.type, Decimal(op.quantity))
        if new_meat == meat:
            after += _effect(new_type, new_qty)
        if after < 0:
            raise InsufficientStockError(str(cur))

    op.type, op.meat_type, op.quantity = new_type, new_meat, new_qty
    op.operation_date, op.franchise_id, op.comment = new_date, new_fr, new_comment
    await log_change(db, op.id, user_id, old, snapshot(op))
    await db.commit()
    await db.refresh(op)
    return op


async def cancel_operation(db: AsyncSession, op_id: int, user_id: int) -> Operation:
    """Отмена (CANCELLED) + аудит; отмена прихода проверяет минус."""
    op = (
        await db.execute(select(Operation).where(Operation.id == op_id))
    ).scalar_one_or_none()
    if op is None:
        raise HTTPException(status_code=404, detail="Операция не найдена")
    if op.status == OperationStatus.CANCELLED.value:
        raise AlreadyCancelledError
    old = snapshot(op)

    if op.type not in {t.value for t in EXPENSE_TYPES}:
        # Убираем приход — склад не должен уйти в минус
        await stock_service.lock_meat(db, op.meat_type)
        stock = await stock_service.get_stock_for(db, op.meat_type)
        if stock < Decimal(op.quantity):
            raise InsufficientStockError(str(stock))

    op.status = OperationStatus.CANCELLED.value
    await log_change(db, op.id, user_id, old, snapshot(op))
    await db.commit()
    await db.refresh(op)
    return op
