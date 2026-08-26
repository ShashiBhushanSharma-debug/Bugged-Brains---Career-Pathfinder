"""
app/database/repositories/recommendations_repo.py

Database access layer for the recommendations table.
Recommendation SCORING is NOT implemented here (Phase 3).
This layer handles read/write of scored recommendations from the engine.
"""
from __future__ import annotations

from datetime import datetime

import asyncpg


async def get_active_recommendations(
    pool: asyncpg.Pool,
    learner_id: str,
) -> list[dict]:
    """
    Returns the current active recommendations for a learner,
    joined with resource and skill data for a complete response.
    Ordered by score descending (highest relevance first).
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                rec.id::text AS id,
                rec.learner_id,
                rec.resource_id,
                rec.score,
                rec.reasoning,
                rec.is_active,
                rec.generated_at,
                -- Resource fields
                r.title         AS resource_title,
                r.type          AS resource_type,
                r.difficulty,
                r.duration_text,
                r.url,
                -- Primary skill
                rs.skill_id     AS target_skill_id,
                s.name          AS target_skill_name
            FROM recommendations rec
            JOIN resources r ON r.id = rec.resource_id
            LEFT JOIN resource_skills rs
                ON rs.resource_id = rec.resource_id AND rs.is_primary = TRUE
            LEFT JOIN skills s ON s.id = rs.skill_id
            WHERE rec.learner_id = $1 AND rec.is_active = TRUE
            ORDER BY rec.score DESC
            """,
            learner_id,
        )
        return [dict(r) for r in rows]


async def deactivate_recommendations(
    pool: asyncpg.Pool,
    learner_id: str,
) -> None:
    """
    Soft-delete all active recommendations for a learner.
    Called before inserting a new engine-generated batch.
    """
    async with pool.acquire() as conn:
        await conn.execute(
            "UPDATE recommendations SET is_active = FALSE WHERE learner_id = $1 AND is_active = TRUE",
            learner_id,
        )


async def save_recommendations(
    pool: asyncpg.Pool,
    learner_id: str,
    recommendations: list[dict],  # [{resource_id, score, reasoning}]
) -> int:
    """
    Insert a new batch of recommendations.
    Caller should call deactivate_recommendations() first to invalidate the old set.
    Returns count of rows inserted.
    """
    count = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            for rec in recommendations:
                await conn.execute(
                    """
                    INSERT INTO recommendations (learner_id, resource_id, score, reasoning, is_active)
                    VALUES ($1, $2, $3, $4, TRUE)
                    """,
                    learner_id,
                    rec["resource_id"],
                    float(rec.get("score", 0.0)),
                    rec.get("reasoning"),
                )
                count += 1
    return count
