from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class FranchiseCreate(BaseModel):
    """Новая франшиза."""

    name: str = Field(min_length=1, max_length=100)


class FranchisePatch(BaseModel):
    """Переименование / отключение."""

    name: str | None = Field(default=None, min_length=1, max_length=100)
    is_active: bool | None = None


class FranchiseOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    is_active: bool
    created_at: datetime
