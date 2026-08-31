"""
app/database/repositories/careers_repo.py

Database access layer for the careers catalog and career_skills.
"""
from __future__ import annotations

from typing import Optional

import asyncpg


async def get_all_careers(pool: asyncpg.Pool) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT id, title, description, created_at FROM careers ORDER BY title"
        )
        return [dict(r) for r in rows]


async def get_career_by_id(pool: asyncpg.Pool, career_id: str) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, title, description FROM careers WHERE id = $1",
            career_id,
        )
        return dict(row) if row else None


async def get_career_by_title(pool: asyncpg.Pool, title: str) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            "SELECT id, title, description FROM careers WHERE lower(title) = lower($1)",
            title,
        )
        return dict(row) if row else None
