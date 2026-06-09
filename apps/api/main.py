from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

import agents.email_outreach.agent  # noqa: F401 — register agents
from api.v1.router import router as v1_router
from config import settings
from database import engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    if "YOUR_DB_PASSWORD" in settings.database_url or "YOUR_ACTUAL_PASSWORD" in settings.database_url:
        logger.warning(
            "DATABASE_URL still contains a placeholder password — set it in .env or apps/api/.env"
        )
    if (
        "db." in settings.database_url
        and ".supabase.co" in settings.database_url
        and "pooler" not in settings.database_url
    ):
        logger.warning(
            "Using direct Supabase host (db.*.supabase.co, IPv6-only). "
            "If signup fails with Connection refused, switch DATABASE_URL to the "
            "Session pooler URI from Supabase Dashboard → Connect."
        )

    from sqlalchemy import text
    from database import async_session_factory

    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
        logger.info("Database connection verified at startup")
    except Exception as exc:
        logger.error("Database not reachable at startup: %s", exc)

    yield
    await engine.dispose()


app = FastAPI(
    title="KatalyzU Agent Platform API",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origin_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(IntegrityError)
async def integrity_error_handler(request: Request, exc: IntegrityError):
    logger.warning("Integrity error on %s: %s", request.url.path, exc.orig)
    return JSONResponse(
        status_code=409,
        content={"detail": "Resource already exists or constraint violation"},
    )


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s", request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/ready")
async def ready():
    from sqlalchemy import text
    from database import async_session_factory

    try:
        async with async_session_factory() as db:
            await db.execute(text("SELECT 1"))
        return {"status": "ready"}
    except Exception as e:
        return JSONResponse(
            status_code=503,
            content={"status": "not_ready", "error": str(e)},
        )


app.include_router(v1_router, prefix="/api")
