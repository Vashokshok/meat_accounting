import pytest
from pydantic import ValidationError

from app.core.config import Settings


def test_settings_require_database_and_strong_secret(monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.delenv("SECRET_KEY", raising=False)

    with pytest.raises(ValidationError):
        Settings(_env_file=None, database_url="postgresql+asyncpg://meat:meat@localhost/meat")

    with pytest.raises(ValidationError):
        Settings(_env_file=None, secret_key="a" * 31)

    with pytest.raises(ValidationError):
        Settings(_env_file=None, secret_key="replace-this-with-a-random-key-value")


def test_settings_accept_random_secret() -> None:
    settings = Settings(
        _env_file=None,
        database_url="postgresql+asyncpg://meat:meat@localhost/meat",
        secret_key="0123456789abcdef" * 4,
    )

    assert len(settings.secret_key) == 64
