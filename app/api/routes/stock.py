from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.user import User
from app.schemas.stock import StockOut
from app.services import stock_service

router = APIRouter(prefix="/api/v1/stock", tags=["stock"])


@router.get("", response_model=StockOut)
async def current(
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
) -> StockOut:
    """Текущие остатки для главной."""
    stock = await stock_service.get_stock(db)
    return StockOut(fillet=float(stock["fillet"]), skin=float(stock["skin"]))
