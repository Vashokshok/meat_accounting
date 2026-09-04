"""Фикстуры на реальном PostgreSQL (SQLite запрещён: нужны локи)."""

import os
from collections.abc import AsyncIterator

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy import text
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

from app.api.deps import get_db
from app.core.database import Base
from app.core.security import hash_password
from app.main import app
from app.models.franchise import Franchise  # noqa: F401
from app.models.operation import Operation  # noqa: F401
from app.models.operation_change import OperationChange  # noqa: F401
from app.models.user import User

TEST_URL = os.getenv(
    "TEST_DATABASE_URL", "postgresql+asyncpg://meat:meat@localhost:5434/meat_test"
)
TABLES = ("operation_changes", "operations", "franchises", "users")


def _engine():
    """Новый движок без пула (без привязки к циклу)."""
    return create_async_engine(TEST_URL, poolclass=NullPool)


@pytest_asyncio.fixture(scope="session", autouse=True)
async def _schema():
    """Схема тестовой БД один раз."""
    eng = _engine()
    async with eng.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    await eng.dispose()
    yield


@pytest_asyncio.fixture()
async def client() -> AsyncIterator[AsyncClient]:
    """Чистые таблицы + клиент API на тестовой БД."""
    eng = _engine()
    async with eng.begin() as conn:
        for t in TABLES:
            await conn.execute(text(f"DELETE FROM {t}"))
    sm = async_sessionmaker(eng, expire_on_commit=False)

    async def _test_db():
        async with sm() as session:
            yield session

    app.dependency_overrides[get_db] = _test_db
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c
    app.dependency_overrides.clear()
    await eng.dispose()


@pytest_asyncio.fixture()
async def auth_headers(client: AsyncClient) -> dict[str, str]:
    """Seed-юзер admin + токен."""
    eng = _engine()
    sm = async_sessionmaker(eng, expire_on_commit=False)
    async with sm() as s:
        s.add(User(username="admin", password_hash=hash_password("meat123")))
        await s.commit()
    await eng.dispose()
    r = await client.post(
        "/api/v1/auth/login", json={"username": "admin", "password": "meat123"}
    )
    assert r.status_code == 200, r.text
    return {"Authorization": "Bearer " + r.json()["access_token"]}
