import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool, create_engine

from alembic import context

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

# Sync URL для миграций (перекрывается env)
SYNC_URL = os.getenv(
    "DATABASE_SYNC_URL", "postgresql+psycopg2://meat:meat@localhost:5434/meat"
)


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
