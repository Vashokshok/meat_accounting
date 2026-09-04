from pydantic import BaseModel


class StockOut(BaseModel):
    """Текущие остатки в кг."""

    fillet: float
    skin: float
