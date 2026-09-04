from collections.abc import AsyncIterator

from fastapi import Depends, Header, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal
from app.core.security import parse_token
from app.models.user import User


async def get_db() -> AsyncIterator[AsyncSession]:
    """Сессия БД на запрос."""
    async with SessionLocal() as session:
        yield session


async def get_current_user(
    authorization: str = Header(default=""),
    db: AsyncSession = Depends(get_db),
) -> User:
    """Текущий юзер по Bearer-токену."""
    scheme, _, token = authorization.partition(" ")
    user_id = parse_token(token) if scheme.lower() == "bearer" and token else None
    if user_id is None:
        raise HTTPException(status_code=401, detail="Не авторизован")
    res = await db.execute(select(User).where(User.id == user_id))
    user = res.scalar_one_or_none()
    if user is None or not user.is_active:
        raise HTTPException(status_code=401, detail="Не авторизован")
    return user
