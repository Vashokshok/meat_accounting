"""Сид: 3 юзера + справочник франшиз."""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.franchise import Franchise
from app.models.user import User

USERS = ["admin", "user1", "user2"]
PASSWORD = "meat123"
FRANCHISES = ["Франшиза №1", "Франшиза №2"]


async def main() -> None:
    """Создать недостающие записи (идемпотентно)."""
    async with SessionLocal() as db:
        for username in USERS:
            exists = (
                await db.execute(select(User).where(User.username == username))
            ).scalar_one_or_none()
            if exists is None:
                db.add(User(username=username, password_hash=hash_password(PASSWORD)))
        for name in FRANCHISES:
            exists = (
                await db.execute(select(Franchise).where(Franchise.name == name))
            ).scalar_one_or_none()
            if exists is None:
                db.add(Franchise(name=name))
        await db.commit()
    print(f"seed ok: users={USERS}")


if __name__ == "__main__":
    asyncio.run(main())
