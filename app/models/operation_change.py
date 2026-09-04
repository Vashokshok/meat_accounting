from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, ForeignKey, Index, Integer
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.core.database import Base


class OperationChange(Base):
    """Аудит: что было → что стало."""

    __tablename__ = "operation_changes"
    __table_args__ = (Index("ix_changes_operation_id", "operation_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    operation_id: Mapped[int] = mapped_column(
        ForeignKey("operations.id", ondelete="RESTRICT"), nullable=False
    )
    changed_by: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="RESTRICT"), nullable=False
    )
    changed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    old_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    new_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
