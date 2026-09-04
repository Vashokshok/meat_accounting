from fastapi import FastAPI
from sqlalchemy import text

from app.core.database import engine
from app.core.exceptions import register_handlers

app = FastAPI(title="Meat accounting")
register_handlers(app)


@app.get("/api/v1/health")
async def health() -> dict:
    """Проверка API и связи с PostgreSQL."""
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}
