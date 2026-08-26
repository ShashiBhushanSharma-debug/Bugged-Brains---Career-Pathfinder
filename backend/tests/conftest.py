"""
tests/conftest.py

Shared pytest fixtures for the backend test suite.

Tests use a real PostgreSQL connection (local career_pathfinder_phase2 DB for CI,
or the Supabase DB via DATABASE_URL in .env for production testing).

The seeded learner DEV_LEARNER_ID (u_1001) must exist via 002_seed_data.sql.

Run tests from the backend/ directory:
    cd backend
    pytest -v
"""
from __future__ import annotations

import asyncio
import os

import asyncpg
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport

# Ensure .env is loaded from the backend/ directory
os.environ.setdefault("ENV_FILE", os.path.join(os.path.dirname(__file__), "..", ".env"))

from app.config import get_settings

settings = get_settings()


# ── Use function-scoped pool (avoids session-scope event loop issues on Py 3.9) ──

@pytest_asyncio.fixture()
async def db_pool():
    """Open a fresh DB pool for each test. Clean and loop-safe."""
    dsn = settings.database_url
    is_local = any(host in dsn for host in ("localhost", "127.0.0.1", "@/"))
    pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=1,
        max_size=3,
        statement_cache_size=0,
        ssl="disable" if is_local else "require",
    )
    yield pool
    await pool.close()


@pytest_asyncio.fixture()
async def client(db_pool):
    """
    Async HTTP client backed by the real app.
    Injects the test pool into the connection module so all route handlers
    use the same pool that the test controls.
    """
    import app.database.connection as conn_module
    conn_module._pool = db_pool

    # Also patch app lifespan: don't call create_pool/close_pool again
    from contextlib import asynccontextmanager
    from fastapi import FastAPI

    @asynccontextmanager
    async def noop_lifespan(application: FastAPI):
        yield  # pool already open

    from app.main import app as fastapi_app
    fastapi_app.router.lifespan_context = noop_lifespan

    transport = ASGITransport(app=fastapi_app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


@pytest.fixture()
def dev_learner_id() -> str:
    return settings.dev_learner_id
