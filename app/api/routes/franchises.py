from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.franchise import Franchise
from app.models.user import User
from app.schemas.franchise import FranchiseCreate, FranchiseOut, FranchisePatch

router = APIRouter(prefix="/api/v1/franchises", tags=["franchises"])


@router.get("", response_model=list[FranchiseOut])
async def list_all(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
    active_only: bool = False,
) -> list:
    """Справочник направлений."""
    q = select(Franchise).order_by(Franchise.id)
    if active_only:
        q = q.where(Franchise.is_active.is_(True))
    return list((await db.execute(q)).scalars())


@router.post("", response_model=FranchiseOut, status_code=201)
async def create(
    data: FranchiseCreate,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Franchise:
    """Новая франшиза."""
    exists = (
        await db.execute(select(Franchise).where(Franchise.name == data.name))
    ).scalar_one_or_none()
    if exists is not None:
        raise HTTPException(status_code=409, detail="Такая франшиза уже есть")
    fr = Franchise(name=data.name)
    db.add(fr)
    await db.commit()
    await db.refresh(fr)
    return fr


@router.patch("/{fr_id}", response_model=FranchiseOut)
async def patch(
    fr_id: int,
    data: FranchisePatch,
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> Franchise:
    """Переименование / отключение (удаления нет)."""
    fr = (
        await db.execute(select(Franchise).where(Franchise.id == fr_id))
    ).scalar_one_or_none()
    if fr is None:
        raise HTTPException(status_code=404, detail="Франшиза не найдена")
    if data.name is not None:
        fr.name = data.name
    if data.is_active is not None:
        fr.is_active = data.is_active
    await db.commit()
    await db.refresh(fr)
    return fr
