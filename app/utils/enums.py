from enum import StrEnum


class MeatType(StrEnum):
    """Вид мяса: филе / с кожей."""

    FILLET = "FILLET"
    SKIN = "SKIN"


class OperationType(StrEnum):
    """Тип операции учёта."""

    INCOMING = "INCOMING"
    SPIT = "SPIT"
    WRITE_OFF = "WRITE_OFF"
    CONVECTION = "CONVECTION"
    FRANCHISE = "FRANCHISE"


class OperationStatus(StrEnum):
    """Статус: только ACTIVE учитывается в остатках."""

    ACTIVE = "ACTIVE"
    CANCELLED = "CANCELLED"


# Расходные типы уменьшают склад
EXPENSE_TYPES: frozenset[OperationType] = frozenset(
    {
        OperationType.SPIT,
        OperationType.WRITE_OFF,
        OperationType.CONVECTION,
        OperationType.FRANCHISE,
    }
)
