from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.routes.auth import router as auth_router
from app.api.routes.exports import router as exports_router
from app.api.routes.franchises import router as franchises_router
from app.api.routes.operations import router as operations_router
from app.api.routes.reports import router as reports_router
from app.api.routes.stock import router as stock_router
from app.core.database import engine
from app.core.exceptions import register_handlers


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(title="Meat accounting")

register_handlers(app)

app.include_router(auth_router)
app.include_router(stock_router)
app.include_router(franchises_router)
app.include_router(reports_router)
app.include_router(exports_router)
app.include_router(operations_router)

app.mount(
    "/static",
    StaticFiles(directory=FRONTEND_DIR),
    name="static",
)


@app.get("/", include_in_schema=False)
async def frontend_login() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "login.html")


@app.get("/login", include_in_schema=False)
async def login_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "login.html")

@app.get("/dashboard", include_in_schema=False)
async def dashboard_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "dashboard.html")

@app.get("/new-operation", include_in_schema=False)
async def new_operation_page() -> FileResponse:
    return FileResponse(FRONTEND_DIR / "new-operation.html")

@app.get("/api/v1/health")
async def health() -> dict:
    async with engine.connect() as conn:
        await conn.execute(text("SELECT 1"))
    return {"status": "ok"}