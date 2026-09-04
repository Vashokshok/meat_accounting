from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import SessionLocal


async def get_db() -> AsyncIterator[AsyncSession]:
    """Сессия БД на запрос."""
    async with SessionLocal() as session:
        yield session
