from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки из .env."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    app_name: str = "Meat accounting"
    database_url: str = "postgresql+asyncpg://meat:meat@localhost:5434/meat"
    secret_key: str = "change-me"
    access_token_expire_hours: int = 24
    timezone: str = "Europe/Moscow"


settings = Settings()
