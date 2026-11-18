"""FastAPI application entry-point.

Creates the ``app`` instance, registers middleware, mounts routers, and
wires up startup / shutdown events.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes.auth import router as auth_router
from app.api.routes.onboarding import router as onboarding_router
from app.core.config import settings
from app.db.base import Base, engine

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Application instance
# ---------------------------------------------------------------------------

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    description=(
        "AI-Powered Compliance Tracker API — authentication and authorisation "
        "layer built with FastAPI, PostgreSQL, and SQLAlchemy (async)."
    ),
    docs_url="/docs",
    redoc_url="/redoc",
)

# ---------------------------------------------------------------------------
# CORS middleware
# ---------------------------------------------------------------------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # React dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------------------
# Startup event — create all tables if they do not exist yet
# ---------------------------------------------------------------------------


@app.on_event("startup")
async def on_startup() -> None:
    """Create database tables on first run (development convenience).

    In production, prefer running Alembic migrations explicitly.
    """
    # Import all model modules so their classes are registered on Base.metadata
    import app.models.user           # noqa: F401
    import app.models.company_profile  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    logger.info("Database tables verified / created.")


# ---------------------------------------------------------------------------
# Routers
# ---------------------------------------------------------------------------

app.include_router(auth_router)
app.include_router(onboarding_router)

# ---------------------------------------------------------------------------
# Root and health-check routes
# ---------------------------------------------------------------------------


@app.get("/", tags=["Meta"], summary="API root")
async def root() -> dict[str, str]:
    """Return a simple status payload to confirm the API is running."""
    return {"status": "ok", "app": settings.APP_NAME}


@app.get("/health", tags=["Meta"], summary="Health check")
async def health() -> dict[str, str]:
    """Lightweight liveness probe used by load-balancers and orchestrators."""
    return {"status": "healthy"}
