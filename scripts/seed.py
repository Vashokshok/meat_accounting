"""Сид: 3 юзера + справочник франшиз."""

import asyncio
import sys
from getpass import getpass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from sqlalchemy import select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.franchise import Franchise
from app.models.user import User

FRANCHISES = ["Франшиза №1", "Франшиза №2"]


def prompt_users() -> list[tuple[str, str]]:
    """Запросить учётные данные новых пользователей без отображения пароля."""
    users = []
    print("Введите логины и пароли сотрудников. Пустой логин завершает ввод.")
    while username := input("Логин (до 50 символов): ").strip():
        if len(username) > 50:
            raise ValueError("Логин не должен превышать 50 символов")
        password = getpass("Пароль (12–100 символов): ")
        confirmation = getpass("Повторите пароль: ")
        if not 12 <= len(password) <= 100:
            raise ValueError("Пароль должен содержать от 12 до 100 символов")
        if password != confirmation:
            raise ValueError("Пароли не совпадают")
        users.append((username, password))
    if not users:
        raise ValueError("Нужно ввести хотя бы одного пользователя")
    return users


async def main(users: list[tuple[str, str]]) -> None:
    """Создать недостающие записи (идемпотентно)."""
    created_users = 0
    async with SessionLocal() as db:
        for username, password in users:
            exists = await db.scalar(
                select(User.id).where(User.username == username)
            )
            if exists is not None:
                print(f"Пользователь {username} уже существует, пропускаю.")
                continue
            db.add(User(username=username, password_hash=hash_password(password)))
            created_users += 1
        for name in FRANCHISES:
            exists = await db.scalar(
                select(Franchise.id).where(Franchise.name == name)
            )
            if exists is None:
                db.add(Franchise(name=name))
        await db.commit()
    print(f"Готово: создано пользователей — {created_users}.")


if __name__ == "__main__":
    try:
        asyncio.run(main(prompt_users()))
    except (ValueError, EOFError) as exc:
        raise SystemExit(str(exc)) from exc
