from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.security import create_token, verify_password
from app.models.user import User
from app.schemas.auth import LoginIn, MeOut, TokenOut

router = APIRouter(prefix="/api/v1/auth", tags=["auth"])


@router.post("/login", response_model=TokenOut)
async def login(data: LoginIn, db: AsyncSession = Depends(get_db)) -> TokenOut:
    """Вход по логину и паролю."""
    user = (
        await db.execute(select(User).where(User.username == data.username))
    ).scalar_one_or_none()
    if user is None or not verify_password(data.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Неверный логин или пароль")
    if not user.is_active:
        raise HTTPException(status_code=401, detail="Пользователь отключён")
    return TokenOut(access_token=create_token(user.id))


@router.get("/me", response_model=MeOut)
async def me(user: User = Depends(get_current_user)) -> MeOut:
    """Текущий пользователь."""
    return MeOut(id=user.id, username=user.username)
