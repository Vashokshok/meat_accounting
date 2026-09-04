from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.operation import Operation
from app.models.operation_change import OperationChange
from app.models.user import User
from app.schemas.operation import (
    OperationChangeOut,
    OperationCreate,
    OperationListOut,
    OperationOut,
    OperationPatch,
)
from app.services import operation_service

router = APIRouter(prefix="/api/v1/operations", tags=["operations"])


@router.post("", response_model=OperationOut, status_code=201)
async def create(
    data: OperationCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Operation:
    """Новая операция учёта."""
    return await operation_service.create_operation(db, data, user.id)


@router.get("", response_model=OperationListOut)
async def history(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    date_from: date | None = None,
    date_to: date | None = None,
    type: str | None = None,
    meat_type: str | None = None,
    user_id: int | None = None,
    franchise_id: int | None = None,
    status: str | None = None,
    limit: int = Query(default=50, le=200),
    offset: int = 0,
) -> OperationListOut:
    """История с фильтрами по operation_date."""
    q = select(Operation)
    if date_from is not None:
        q = q.where(Operation.operation_date >= date_from)
    if date_to is not None:
        q = q.where(Operation.operation_date <= date_to)
    if type is not None:
        q = q.where(Operation.type == type)
    if meat_type is not None:
        q = q.where(Operation.meat_type == meat_type)
    if user_id is not None:
        q = q.where(Operation.created_by == user_id)
    if franchise_id is not None:
        q = q.where(Operation.franchise_id == franchise_id)
    if status is not None:
        q = q.where(Operation.status == status)
    total = await db.scalar(select(func.count()).select_from(q.subquery())) or 0
    rows = (
        await db.execute(q.order_by(Operation.id.desc()).limit(limit).offset(offset))
    ).scalars()
    return OperationListOut(items=list(rows), total=total)


@router.get("/{op_id}", response_model=OperationOut)
async def one(
    op_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Operation:
    """Одна операция по id."""
    op = (await db.execute(select(Operation).where(Operation.id == op_id))).scalar_one_or_none()
    if op is None:
        raise HTTPException(status_code=404, detail="Операция не найдена")
    return op


@router.patch("/{op_id}", response_model=OperationOut)
async def patch(
    op_id: int,
    data: OperationPatch,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Operation:
    """Правка + аудит одной транзакцией."""
    return await operation_service.update_operation(db, op_id, data, user.id)


@router.post("/{op_id}/cancel", response_model=OperationOut)
async def cancel(
    op_id: int,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
) -> Operation:
    """Отмена без удаления (CANCELLED)."""
    return await operation_service.cancel_operation(db, op_id, user.id)


@router.get("/{op_id}/changes", response_model=list[OperationChangeOut])
async def changes(
    op_id: int,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> list:
    """Аудит было → стало → кто → когда."""
    rows = (
        await db.execute(
            select(OperationChange)
            .where(OperationChange.operation_id == op_id)
            .order_by(OperationChange.id)
        )
    ).scalars()
    return list(rows)
