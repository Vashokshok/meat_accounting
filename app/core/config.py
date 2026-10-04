from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки из окружения и .env; URL базы и секрет обязательны."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "Meat accounting"
    database_url: str
    secret_key: str = Field(min_length=32)
    access_token_expire_hours: int = 24
    timezone: str = "Europe/Moscow"
    allowed_origins: str = ""
    debug: bool = False
    log_level: str = "INFO"
    log_json: bool = True

    @property
    def cors_origins(self) -> list[str]:
        """Разрешённыеorigins для CORS."""
        if not self.allowed_origins:
            return []
        return [o.strip() for o in self.allowed_origins.split(",") if o.strip()]

    @field_validator("secret_key")
    @classmethod
    def validate_secret_key(cls, value: str) -> str:
        if any(marker in value.lower() for marker in ("replace", "example", "change-me")):
            raise ValueError("SECRET_KEY должен быть заменён на случайное значение")
        return value


settings = Settings()
