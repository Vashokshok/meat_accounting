from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class InsufficientStockError(Exception):
    """Расход превышает доступный остаток."""

    def __init__(self, available: str = ""):
        self.available = available
        super().__init__(f"Недостаточно мяса: доступно {available} кг")


class AlreadyCancelledError(Exception):
    """Повторная отмена операции."""


def register_handlers(app: FastAPI) -> None:
    """Единый формат ошибок на русском."""

    @app.exception_handler(InsufficientStockError)
    async def _stock(_: Request, exc: InsufficientStockError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"code": "INSUFFICIENT_STOCK", "detail": str(exc)},
        )

    @app.exception_handler(AlreadyCancelledError)
    async def _cancel(_: Request, __: AlreadyCancelledError) -> JSONResponse:
        return JSONResponse(
            status_code=409,
            content={"code": "ALREADY_CANCELLED", "detail": "Операция уже отменена"},
        )
