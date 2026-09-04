from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.utils.enums import MeatType, OperationType


class OperationCreate(BaseModel):
    """Новая операция (дата может быть вчерашней)."""

    type: OperationType
    meat_type: MeatType
    quantity: Decimal = Field(gt=0, max_digits=10, decimal_places=3)
    operation_date: date
    franchise_id: int | None = None
    comment: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _franchise_rules(self) -> "OperationCreate":
        """FRANCHISE требует franchise_id, остальным он запрещён."""
        if self.type == OperationType.FRANCHISE and self.franchise_id is None:
            raise ValueError("Для франшизы укажите franchise_id")
        if self.type != OperationType.FRANCHISE and self.franchise_id is not None:
            raise ValueError("franchise_id только для типа FRANCHISE")
        return self


class OperationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    type: OperationType
    meat_type: MeatType
    quantity: Decimal
    franchise_id: int | None
    comment: str | None
    status: str
    operation_date: date
    created_by: int
    created_at: datetime
    updated_at: datetime


class OperationListOut(BaseModel):
    items: list[OperationOut]
    total: int


class OperationPatch(BaseModel):
    """Частичное изменение (status менять нельзя)."""

    type: OperationType | None = None
    meat_type: MeatType | None = None
    quantity: Decimal | None = Field(default=None, gt=0, max_digits=10, decimal_places=3)
    operation_date: date | None = None
    franchise_id: int | None = None
    comment: str | None = Field(default=None, max_length=500)


class OperationChangeOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    operation_id: int
    changed_by: int
    changed_at: datetime
    old_data: dict
    new_data: dict
