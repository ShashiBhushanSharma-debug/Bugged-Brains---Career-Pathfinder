"""
app/main.py

FastAPI application entry point.

Architecture:
  Frontend → FastAPI (this file) → Supabase PostgreSQL

Startup: opens asyncpg connection pool
Shutdown: closes pool gracefully
"""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import get_settings
from app.database.connection import create_pool, close_pool
from app.api.router import api_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage the asyncpg pool lifecycle."""
    settings = get_settings()
    await create_pool()
    print(f"[Career Pathfinder] DB pool open | env={settings.app_env}")
    yield
    await close_pool()
    print("[Career Pathfinder] DB pool closed")


def create_app() -> FastAPI:
    settings = get_settings()

    app = FastAPI(
        title="Career Pathfinder API",
        description=(
            "Backend API for the Career Pathfinder application. "
            "Connects the React frontend to Supabase PostgreSQL. "
            "Phase 2: Database read/write layer. No auth yet."
        ),
        version="0.2.0",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )

    # ── CORS ──────────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Routes ────────────────────────────────────────────────────────────────
    app.include_router(api_router)

    # ── Root & Health check ───────────────────────────────────────────────────
    @app.get("/", tags=["Health"])
    async def root() -> dict:
        return {
            "status": "ok",
            "message": "Career Pathfinder API is running",
            "version": "0.2.0",
            "env": settings.app_env,
            "docs": "/docs",
            "health": "/health",
        }

    @app.get("/health", tags=["Health"])
    async def health() -> dict:
        return {"status": "ok", "version": "0.2.0", "env": settings.app_env}

    return app


app = create_app()

# ── Dev entrypoint ────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "app.main:app",
        host=settings.app_host,
        port=settings.app_port,
        reload=settings.is_development,
    )
