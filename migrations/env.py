import os
import sys
from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context

# Загружаем .env для alembic
from dotenv import load_dotenv

load_dotenv()

# Путь к пакету app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.core.database import Base  # noqa: E402
import app.models.user  # noqa: E402,F401
import app.models.franchise  # noqa: E402,F401
import app.models.operation  # noqa: E402,F401
import app.models.operation_change  # noqa: E402,F401

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Метаданные всех моделей
target_metadata = Base.metadata

# Sync URL для миграций — из DATABASE_URL с заменой драйвера
def get_sync_url() -> str:
    """Преобразует async URL в sync для alembic."""
    async_url = os.getenv("DATABASE_URL")
    if not async_url:
        raise RuntimeError("DATABASE_URL не задан в окружении")
    # asyncpg -> psycopg2
    return async_url.replace("postgresql+asyncpg://", "postgresql+psycopg2://")


SYNC_URL = get_sync_url()


def run_migrations_offline() -> None:
    """Офлайн-режим без подключения."""
    context.configure(
        url=SYNC_URL,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Онлайн-режим через sync engine."""
    connectable = create_engine(SYNC_URL, poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
