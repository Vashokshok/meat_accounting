from datetime import UTC, datetime, timedelta

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Хеширование паролей
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    """Хеш пароля для хранения."""
    return pwd_context.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    """Проверка пароля при логине."""
    return pwd_context.verify(password, hashed)


def create_token(user_id: int) -> str:
    """JWT на 24ч (одна смена)."""
    expire = datetime.now(UTC) + timedelta(
        hours=settings.access_token_expire_hours
    )
    return jwt.encode(
        {"sub": str(user_id), "exp": expire},
        settings.secret_key,
        algorithm=ALGORITHM,
    )


def parse_token(token: str) -> int | None:
    """ID юзера из токена или None."""
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return int(payload["sub"])
    except (JWTError, ValueError, KeyError, TypeError):
        return None
