import logging
import logging.config
import sys
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, PlainTextResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.api.routes.auth import router as auth_router
from app.api.routes.exports import router as exports_router
from app.api.routes.franchises import router as franchises_router
from app.api.routes.operations import router as operations_router
from app.api.routes.reports import router as reports_router
from app.api.routes.stock import router as stock_router
from app.core.config import settings
from app.core.database import engine
from app.core.exceptions import register_handlers

logger = logging.getLogger(__name__)


def setup_logging() -> None:
    """Настройка структурированного логирования."""
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "json": {
                "()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
            },
            "standard": {
                "format": "%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            },
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "stream": sys.stdout,
                "formatter": "json" if settings.log_json else "standard",
            },
        },
        "root": {
            "level": settings.log_level,
            "handlers": ["console"],
        },
        "loggers": {
            "uvicorn": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "uvicorn.error": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "uvicorn.access": {"level": "INFO", "handlers": ["console"], "propagate": False},
            "sqlalchemy.engine": {"level": "WARNING", "handlers": ["console"], "propagate": False},
        },
    }
    logging.config.dictConfig(log_config)


setup_logging()

BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_PUBLIC_DIR = BASE_DIR / "frontend" / "public"

app = FastAPI(title="Meat accounting", debug=settings.debug)

# CORS
cors_origins = settings.cors_origins
if cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

register_handlers(app)

app.include_router(auth_router)
app.include_router(operations_router)
app.include_router(stock_router)
app.include_router(franchises_router)
app.include_router(reports_router)
app.include_router(exports_router)


# Статика (public папка фронтенда)
if FRONTEND_PUBLIC_DIR.exists():
    app.mount(
        "/static",
        StaticFiles(directory=FRONTEND_PUBLIC_DIR),
        name="static",
    )


# Health checks
@app.get("/health/live", include_in_schema=False)
async def liveness() -> PlainTextResponse:
    """Liveness probe — процесс жив."""
    return PlainTextResponse("ok")


@app.get("/health/ready", include_in_schema=False)
async def readiness() -> dict:
    """Readiness probe — готово к трафику (БД доступна)."""
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "ready", "database": "connected"}
    except SQLAlchemyError:
        logger.exception("Database readiness check failed")
        return {"status": "not ready", "database": "disconnected"}


# Старый health для совместимости
@app.get("/api/v1/health")
async def health() -> dict:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}


# Фронтенд маршруты (SPA fallback)
@app.get("/", include_in_schema=False)
async def frontend_login() -> FileResponse:
    return FileResponse(FRONTEND_PUBLIC_DIR / "login.html")


@app.get("/login", include_in_schema=False)
async def login_page() -> FileResponse:
    return FileResponse(FRONTEND_PUBLIC_DIR / "login.html")


@app.get("/dashboard", include_in_schema=False)
async def dashboard_page() -> FileResponse:
    return FileResponse(FRONTEND_PUBLIC_DIR / "dashboard.html")


@app.get("/profile", include_in_schema=False)
async def profile_page() -> FileResponse:
    return FileResponse(FRONTEND_PUBLIC_DIR / "profile.html")


@app.get("/new-operation", include_in_schema=False)
async def new_operation_page() -> FileResponse:
    return FileResponse(FRONTEND_PUBLIC_DIR / "new_operation.html")


@app.get("/history", include_in_schema=False)
async def history_page() -> FileResponse:
    return FileResponse(FRONTEND_PUBLIC_DIR / "history.html")


@app.get("/reports", include_in_schema=False)
async def reports_page() -> FileResponse:
    return FileResponse(FRONTEND_PUBLIC_DIR / "reports.html")