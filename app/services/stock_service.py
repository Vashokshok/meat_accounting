from decimal import Decimal

from sqlalchemy import case, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import text

from app.models.operation import Operation
from app.utils.enums import EXPENSE_TYPES, MeatType, OperationStatus, OperationType


def sign(op_type: str) -> int:
    """+1 приход, −1 любой расход."""
    return -1 if op_type in {t.value for t in EXPENSE_TYPES} else 1


async def lock_meat(db: AsyncSession, meat: str) -> None:
    """Сериализация расходов по виду мяса."""
    await db.execute(
        text("SELECT pg_advisory_xact_lock(hashtext(:mt))"), {"mt": meat}
    )


async def get_stock_for(db: AsyncSession, meat: MeatType | str) -> Decimal:
    """Остаток одного вида мяса из ACTIVE-операций."""
    mt = meat.value if isinstance(meat, MeatType) else meat
    total = await db.scalar(
        select(
            func.coalesce(
                func.sum(
                    Operation.quantity
                    * case(
                        (
                            Operation.type == OperationType.INCOMING.value,
                            1,
                        ),
                        else_=-1,
                    )
                ),
                0,
            )
        ).where(
            Operation.meat_type == mt,
            Operation.status == OperationStatus.ACTIVE.value,
        )
    )
    return Decimal(total or 0)


async def get_stock(db: AsyncSession) -> dict[str, Decimal]:
    """Остатки обоих видов мяса."""
    return {
        "fillet": await get_stock_for(db, MeatType.FILLET),
        "skin": await get_stock_for(db, MeatType.SKIN),
    }
