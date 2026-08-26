"""
app/database/repositories/learner_repo.py

Database access layer for learner_profiles.
All queries use asyncpg directly — no ORM.
"""
from __future__ import annotations

import json
from typing import Any, Optional

import asyncpg


async def get_learner_by_id(pool: asyncpg.Pool, learner_id: str) -> Optional[dict]:
    """
    Fetch a single learner profile by ID.
    Returns a plain dict or None if not found.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                id, name, first_name,
                target_career_id, current_level,
                career_readiness, overall_progress,
                streak_days, weekly_learning_hours, total_learning_hours,
                interests, learning_style, preferred_session_length,
                learning_preferences, notification_settings,
                current_focus_skill_id,
                joined_at, created_at, updated_at
            FROM learner_profiles
            WHERE id = $1
            """,
            learner_id,
        )
        if row is None:
            return None
        return _row_to_dict(row)


async def create_learner(pool: asyncpg.Pool, data: dict[str, Any]) -> dict:
    """
    Insert a new learner profile. Returns the created row.
    Used by POST /api/onboarding for new learners.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO learner_profiles (
                id, name, first_name,
                target_career_id, current_level,
                weekly_learning_hours,
                interests, learning_style, preferred_session_length,
                learning_preferences, notification_settings,
                current_focus_skill_id, joined_at
            )
            VALUES ($1,$2,$3,$4,$5,$6,$7,$8,$9,$10,$11,$12, NOW())
            ON CONFLICT (id) DO UPDATE SET
                name                    = EXCLUDED.name,
                first_name              = EXCLUDED.first_name,
                target_career_id        = EXCLUDED.target_career_id,
                current_level           = EXCLUDED.current_level,
                weekly_learning_hours   = EXCLUDED.weekly_learning_hours,
                interests               = EXCLUDED.interests,
                learning_style          = EXCLUDED.learning_style,
                preferred_session_length = EXCLUDED.preferred_session_length,
                learning_preferences    = EXCLUDED.learning_preferences,
                notification_settings   = EXCLUDED.notification_settings,
                current_focus_skill_id  = EXCLUDED.current_focus_skill_id,
                updated_at              = NOW()
            RETURNING *
            """,
            data["id"],
            data["name"],
            data.get("first_name"),
            data.get("target_career_id"),
            data.get("current_level"),
            data.get("weekly_learning_hours", 8),
            data.get("interests"),
            data.get("learning_style"),
            data.get("preferred_session_length"),
            json.dumps(data["learning_preferences"]) if data.get("learning_preferences") else None,
            json.dumps(data["notification_settings"]) if data.get("notification_settings") else None,
            data.get("current_focus_skill_id"),
        )
        return _row_to_dict(row)


async def update_learner(pool: asyncpg.Pool, learner_id: str, updates: dict) -> Optional[dict]:
    """
    Partial update — only updates fields that are explicitly provided.
    Returns updated row or None if learner not found.
    """
    if not updates:
        return await get_learner_by_id(pool, learner_id)

    # Build dynamic SET clause
    set_clauses = []
    values: list[Any] = []
    param_idx = 1

    allowed_fields = {
        "name", "first_name", "target_career_id", "current_level",
        "career_readiness", "overall_progress", "streak_days",
        "weekly_learning_hours", "total_learning_hours",
        "interests", "learning_style", "preferred_session_length",
        "learning_preferences", "notification_settings",
        "current_focus_skill_id",
    }

    for field, value in updates.items():
        if field not in allowed_fields:
            continue
        if field in ("learning_preferences", "notification_settings") and value is not None:
            value = json.dumps(value)
        set_clauses.append(f"{field} = ${param_idx}")
        values.append(value)
        param_idx += 1

    if not set_clauses:
        return await get_learner_by_id(pool, learner_id)

    set_clauses.append(f"updated_at = NOW()")
    values.append(learner_id)

    sql = f"""
        UPDATE learner_profiles
        SET {', '.join(set_clauses)}
        WHERE id = ${param_idx}
        RETURNING *
    """

    async with pool.acquire() as conn:
        row = await conn.fetchrow(sql, *values)
        if row is None:
            return None
        return _row_to_dict(row)


def _row_to_dict(row: asyncpg.Record) -> dict:
    """Convert asyncpg Record to a plain dict, parsing JSONB strings if present."""
    d = dict(row)
    for key in ("learning_preferences", "notification_settings"):
        if key in d and isinstance(d[key], str):
            try:
                d[key] = json.loads(d[key])
            except (json.JSONDecodeError, TypeError):
                pass
    return d
