"""
app/database/connection.py

asyncpg connection pool lifecycle.
The pool is created once at app startup and closed at shutdown.
All repositories receive a pool reference via FastAPI dependency injection.
"""
from __future__ import annotations

from typing import Optional

import asyncpg
from asyncpg import Pool

from app.config import get_settings

# Module-level pool reference (set by lifespan events in main.py)
_pool: Optional[Pool] = None


async def create_pool() -> Pool:
    """
    Open an asyncpg connection pool to Supabase PostgreSQL.
    Called once in the FastAPI lifespan startup handler.
    """
    settings = get_settings()
    dsn = settings.database_url

    # Disable SSL for local connections (localhost / 127.0.0.1).
    # Supabase (*.supabase.co) requires SSL — asyncpg handles it automatically
    # via the sslmode=require parameter in the DSN or the ssl kwarg.
    is_local = any(host in dsn for host in ("localhost", "127.0.0.1", "@/"))

    pool = await asyncpg.create_pool(
        dsn=dsn,
        min_size=settings.db_min_connections,
        max_size=settings.db_max_connections,
        command_timeout=30,
        statement_cache_size=0,
        ssl="disable" if is_local else "require",
    )
    global _pool
    _pool = pool
    return pool


async def close_pool() -> None:
    """Close the pool gracefully. Called in the FastAPI lifespan shutdown handler."""
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def get_pool() -> Pool:
    """
    FastAPI dependency: returns the active pool.
    Raises RuntimeError if called before startup.
    """
    if _pool is None:
        raise RuntimeError(
            "Database pool is not initialised. "
            "Ensure create_pool() was called during app startup."
        )
    return _pool
