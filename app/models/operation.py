from datetime import date as date_t
from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base
from app.utils.enums import OperationStatus


class Operation(Base):
    """Центральная сущность учёта."""

    __tablename__ = "operations"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_operations_quantity_pos"),
        Index("ix_operations_meat_status_date", "meat_type", "status", "operation_date"),
        Index("ix_operations_status_created", "status", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    type: Mapped[str] = mapped_column(String(20), nullable=False)
    meat_type: Mapped[str] = mapped_column(String(20), nullable=False)
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 3), nullable=False)
    franchise_id: Mapped[int | None] = mapped_column(
        ForeignKey("franchises.id", ondelete="RESTRICT"), nullable=True
    )
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(
        String(20), default=OperationStatus.ACTIVE.value, nullable=False
    )
    # Бизнес-дата (можно вчера), фильтры и отчёты по ней
    operation_date: Mapped[date_t] = mapped_column(Date, nullable=False)
    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Допустимые значения (хранение — строки из Enum)
