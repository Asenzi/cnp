from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import RedirectResponse
from fastapi.staticfiles import StaticFiles

from app.admin.service import ensure_default_admin_user
from app.api.router import api_router
from app.core.config import settings
from app.core.exceptions import register_exception_handlers
from app.core.logger import logger, setup_logging
from app.core.redis import close_redis, init_redis
from app.payment import ensure_default_payment_configs
from app.points import ensure_default_points_configs

setup_logging(settings.DEBUG)

app = FastAPI(
    title=settings.APP_NAME,
    version="0.1.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
    debug=settings.DEBUG,
)

static_dir = Path(__file__).resolve().parents[1] / "static"
static_dir.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

# Development-friendly CORS config for local front-back integration.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

register_exception_handlers(app)
app.include_router(api_router, prefix=settings.API_V1_PREFIX)


@app.on_event("startup")
async def on_startup() -> None:
    ensure_default_admin_user()
    ensure_default_points_configs()
    ensure_default_payment_configs()
    await init_redis()
    logger.info("service started")


@app.on_event("shutdown")
async def on_shutdown() -> None:
    await close_redis()
    logger.info("service stopped")


@app.get("/", tags=["Root"], summary="Root endpoint")
def root() -> dict[str, str]:
    return {
        "name": settings.APP_NAME,
        "env": settings.APP_ENV,
        "version": "0.1.0",
        "message": "service is running",
    }


@app.get("/admin-console", include_in_schema=False)
def admin_console_entry() -> RedirectResponse:
    return RedirectResponse(url="/static/admin/index.html")
