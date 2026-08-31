"""
app/database/repositories/learning_history_repo.py

Database access layer for learning_history and activity_log tables.
"""
from __future__ import annotations

import uuid
from typing import List, Optional

import asyncpg


# ── Learning history ──────────────────────────────────────────────────────────

async def get_learning_history(
    pool: asyncpg.Pool,
    learner_id: str,
    status: Optional[str] = None,
) -> list[dict]:
    """
    Returns learning history for a learner, ordered by most recently updated.
    Optionally filter by status (completed | in-progress | not-started).
    """
    conditions = ["lh.learner_id = $1"]
    params: list = [learner_id]
    idx = 2

    if status:
        conditions.append(f"lh.status = ${idx}")
        params.append(status)
        idx += 1

    where_clause = "WHERE " + " AND ".join(conditions)

    sql = f"""
        SELECT
            lh.id, lh.learner_id, lh.resource_id,
            lh.title, lh.type, lh.status,
            lh.progress_pct, lh.completed_at,
            lh.created_at, lh.updated_at
        FROM learning_history lh
        {where_clause}
        ORDER BY lh.updated_at DESC
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)
        return [dict(r) for r in rows]


async def get_history_item_by_id(
    pool: asyncpg.Pool, learner_id: str, item_id: str
) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, learner_id, resource_id, title, type, status,
                   progress_pct, completed_at, created_at, updated_at
            FROM learning_history WHERE id = $1 AND learner_id = $2
            """,
            item_id,
            learner_id,
        )
        return dict(row) if row else None


async def get_history_by_resource(
    pool: asyncpg.Pool, learner_id: str, resource_id: str
) -> Optional[dict]:
    """Check if a learner already has a history record for a specific resource."""
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT id, status, progress_pct
            FROM learning_history
            WHERE learner_id = $1 AND resource_id = $2
            """,
            learner_id,
            resource_id,
        )
        return dict(row) if row else None


async def create_history_item(
    pool: asyncpg.Pool,
    learner_id: str,
    data: dict,
) -> dict:
    """
    Create a new learning history entry.
    Uses a uuid string as ID for engine-generated rows.
    """
    item_id = data.get("id") or str(uuid.uuid4())
    status = data.get("status", "not-started")
    progress_pct = data.get("progress_pct", 0)
    completed_at_expr = "NOW()" if status == "completed" else "NULL"

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            f"""
            INSERT INTO learning_history
                (id, learner_id, resource_id, title, type, status, progress_pct, completed_at)
            VALUES ($1, $2, $3, $4, $5, $6, $7, {completed_at_expr})
            ON CONFLICT (id) DO UPDATE SET
                status       = EXCLUDED.status,
                progress_pct = EXCLUDED.progress_pct,
                completed_at = CASE WHEN EXCLUDED.status = 'completed' THEN NOW()
                                    ELSE learning_history.completed_at END,
                updated_at   = NOW()
            RETURNING *
            """,
            item_id,
            learner_id,
            data.get("resource_id"),
            data["title"],
            data["type"],
            status,
            progress_pct,
        )
        return dict(row)


async def update_history_item(
    pool: asyncpg.Pool,
    learner_id: str,
    item_id: str,
    updates: dict,
) -> Optional[dict]:
    """Update status and/or progress on an existing history item for the authenticated learner."""
    status = updates.get("status")
    progress_pct = updates.get("progress_pct")

    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            UPDATE learning_history SET
                status       = COALESCE($3, status),
                progress_pct = COALESCE($4, progress_pct),
                completed_at = CASE
                    WHEN $3 = 'completed' THEN NOW()
                    ELSE completed_at
                END,
                updated_at   = NOW()
            WHERE id = $1 AND learner_id = $2
            RETURNING *
            """,
            item_id,
            learner_id,
            status,
            progress_pct,
        )
        return dict(row) if row else None


async def bulk_create_history(
    pool: asyncpg.Pool,
    learner_id: str,
    items: list[dict],
) -> int:
    """Bulk insert prior learning from onboarding. Returns count."""
    count = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            for item in items:
                item_id = str(uuid.uuid4())
                await conn.execute(
                    """
                    INSERT INTO learning_history (id, learner_id, resource_id, title, type, status, progress_pct, completed_at)
                    VALUES ($1, $2, $3, $4, $5, 'completed', 100, NOW())
                    ON CONFLICT DO NOTHING
                    """,
                    item_id,
                    learner_id,
                    item.get("resource_id"),
                    item["title"],
                    item["type"],
                )
                count += 1
    return count


# ── Activity log ──────────────────────────────────────────────────────────────

async def get_activity_log(
    pool: asyncpg.Pool,
    learner_id: str,
    limit: int = 20,
) -> list[dict]:
    """Returns the most recent activity log entries for a learner."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT id::text AS id, learner_id, type, label, meta, reference_id, occurred_at
            FROM activity_log
            WHERE learner_id = $1
            ORDER BY occurred_at DESC
            LIMIT $2
            """,
            learner_id,
            limit,
        )
        return [dict(r) for r in rows]


async def log_activity(
    pool: asyncpg.Pool,
    learner_id: str,
    event_type: str,
    label: str,
    meta: Optional[str] = None,
    reference_id: Optional[str] = None,
) -> None:
    """Append a new event to the activity log."""
    async with pool.acquire() as conn:
        await conn.execute(
            """
            INSERT INTO activity_log (learner_id, type, label, meta, reference_id)
            VALUES ($1, $2, $3, $4, $5)
            """,
            learner_id,
            event_type,
            label,
            meta,
            reference_id,
        )
