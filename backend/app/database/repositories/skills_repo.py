"""
app/database/repositories/skills_repo.py

Database access layer for skills, learner_skills, career_skills, and skill_prerequisites.
"""
from __future__ import annotations

from typing import List, Optional

import asyncpg


# ── Global skill catalog ──────────────────────────────────────────────────────

async def get_all_skills(pool: asyncpg.Pool) -> list[dict]:
    async with pool.acquire() as conn:
        rows = await conn.fetch("SELECT id, name, description, created_at FROM skills ORDER BY name")
        return [dict(r) for r in rows]


async def get_skill_by_id(pool: asyncpg.Pool, skill_id: str) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow("SELECT id, name, description FROM skills WHERE id = $1", skill_id)
        return dict(row) if row else None


# ── Per-learner skills ────────────────────────────────────────────────────────

async def get_learner_skills(pool: asyncpg.Pool, learner_id: str) -> list[dict]:
    """
    Returns all skills for a learner, joined with the skills catalog for the name.
    """
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                ls.id::text AS id,
                ls.skill_id,
                s.name,
                ls.proficiency_score,
                ls.status,
                ls.last_assessed_at,
                ls.updated_at
            FROM learner_skills ls
            JOIN skills s ON s.id = ls.skill_id
            WHERE ls.learner_id = $1
            ORDER BY ls.proficiency_score DESC
            """,
            learner_id,
        )
        return [dict(r) for r in rows]


async def upsert_learner_skill(
    pool: asyncpg.Pool,
    learner_id: str,
    skill_id: str,
    proficiency_score: int,
    status: str = "not-started",
    update_assessed_at: bool = False,
) -> dict:
    """
    Insert or update a single (learner, skill) row.
    Used by onboarding and by the adaptive engine after assessments.
    """
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            INSERT INTO learner_skills (learner_id, skill_id, proficiency_score, status, last_assessed_at)
            VALUES ($1, $2, $3, $4, CASE WHEN $5 THEN NOW() ELSE NULL END)
            ON CONFLICT (learner_id, skill_id) DO UPDATE SET
                proficiency_score = EXCLUDED.proficiency_score,
                status            = EXCLUDED.status,
                last_assessed_at  = CASE WHEN $5 THEN NOW() ELSE learner_skills.last_assessed_at END,
                updated_at        = NOW()
            RETURNING id::text AS id, learner_id, skill_id, proficiency_score, status, last_assessed_at
            """,
            learner_id,
            skill_id,
            proficiency_score,
            status,
            update_assessed_at,
        )
        return dict(row)


async def bulk_upsert_learner_skills(
    pool: asyncpg.Pool,
    learner_id: str,
    skills: list[dict],  # [{skill_id, proficiency_score, status?}]
) -> int:
    """
    Bulk upsert for onboarding — returns count of rows affected.
    """
    count = 0
    async with pool.acquire() as conn:
        async with conn.transaction():
            for s in skills:
                await conn.execute(
                    """
                    INSERT INTO learner_skills (learner_id, skill_id, proficiency_score, status)
                    VALUES ($1, $2, $3, $4)
                    ON CONFLICT (learner_id, skill_id) DO UPDATE SET
                        proficiency_score = EXCLUDED.proficiency_score,
                        status            = EXCLUDED.status,
                        updated_at        = NOW()
                    """,
                    learner_id,
                    s["skill_id"],
                    s["proficiency_score"],
                    s.get("status", "not-started"),
                )
                count += 1
    return count


# ── Career skills (requirements) ──────────────────────────────────────────────

async def get_career_skills(pool: asyncpg.Pool, career_id: str) -> list[dict]:
    """Returns required skills for a career with their required_score thresholds."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT
                cs.skill_id,
                s.name,
                cs.required_score,
                cs.importance
            FROM career_skills cs
            JOIN skills s ON s.id = cs.skill_id
            WHERE cs.career_id = $1
            ORDER BY cs.required_score DESC
            """,
            career_id,
        )
        return [dict(r) for r in rows]


# ── Skill prerequisites ───────────────────────────────────────────────────────

async def get_skill_prerequisites(pool: asyncpg.Pool, skill_id: str) -> List[str]:
    """Returns list of prerequisite skill IDs for a given skill."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT prerequisite_skill_id FROM skill_prerequisites WHERE skill_id = $1",
            skill_id,
        )
        return [r["prerequisite_skill_id"] for r in rows]


async def get_all_skill_prerequisites(pool: asyncpg.Pool) -> list[dict]:
    """Returns all prerequisite edges — used by Member 3's Skill Graph."""
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            "SELECT skill_id, prerequisite_skill_id FROM skill_prerequisites"
        )
        return [dict(r) for r in rows]
