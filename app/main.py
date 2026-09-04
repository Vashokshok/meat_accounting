from fastapi import FastAPI
from sqlalchemy import text

from app.api.routes.auth import router as auth_router
from app.core.database import engine
from app.core.exceptions import register_handlers

app = FastAPI(title="Meat accounting")
register_handlers(app)
app.include_router(auth_router)


@app.get("/api/v1/health")
async def health() -> dict:
    """Проверка API и связи с PostgreSQL."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}
