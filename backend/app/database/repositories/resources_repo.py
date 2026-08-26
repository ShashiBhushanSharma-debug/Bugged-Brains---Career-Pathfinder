"""
app/database/repositories/resources_repo.py

Database access layer for the resources catalog and resource_skills mapping.
"""
from __future__ import annotations

from typing import List, Optional

import asyncpg


async def get_all_resources(
    pool: asyncpg.Pool,
    skill_id: Optional[str] = None,
    resource_type: Optional[str] = None,
) -> list:
    """
    Fetch resources from catalog with optional filters.
    Returns resources with their primary skill joined in.
    """
    conditions = []
    params: list = []
    idx = 1

    if skill_id:
        conditions.append(
            f"EXISTS (SELECT 1 FROM resource_skills rs WHERE rs.resource_id = r.id AND rs.skill_id = ${idx})"
        )
        params.append(skill_id)
        idx += 1

    if resource_type:
        conditions.append(f"r.type = ${idx}")
        params.append(resource_type)
        idx += 1

    where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

    sql = f"""
        SELECT
            r.id,
            r.title,
            r.description,
            r.type,
            r.difficulty,
            r.duration_text,
            r.url,
            r.why_recommended_template,
            -- Primary skill
            primary_rs.skill_id   AS primary_skill_id,
            s.name                AS primary_skill_name,
            -- All skill IDs (aggregated)
            COALESCE(
                ARRAY_AGG(all_rs.skill_id ORDER BY all_rs.is_primary DESC) FILTER (WHERE all_rs.skill_id IS NOT NULL),
                ARRAY[]::text[]
            ) AS skill_ids
        FROM resources r
        LEFT JOIN resource_skills primary_rs
            ON primary_rs.resource_id = r.id AND primary_rs.is_primary = TRUE
        LEFT JOIN skills s ON s.id = primary_rs.skill_id
        LEFT JOIN resource_skills all_rs ON all_rs.resource_id = r.id
        {where_clause}
        GROUP BY r.id, r.title, r.description, r.type, r.difficulty,
                 r.duration_text, r.url, r.why_recommended_template,
                 primary_rs.skill_id, s.name
        ORDER BY r.title
    """

    async with pool.acquire() as conn:
        rows = await conn.fetch(sql, *params)
        return [dict(r) for r in rows]


async def get_resource_by_id(pool: asyncpg.Pool, resource_id: str) -> Optional[dict]:
    async with pool.acquire() as conn:
        row = await conn.fetchrow(
            """
            SELECT
                r.id, r.title, r.description, r.type, r.difficulty,
                r.duration_text, r.url, r.why_recommended_template
            FROM resources r
            WHERE r.id = $1
            """,
            resource_id,
        )
        return dict(row) if row else None


async def get_resources_by_skill_ids(
    pool: asyncpg.Pool,
    skill_ids: List[str],
) -> list[dict]:
    """
    Returns resources that teach any of the given skills (primary or supplementary).
    Used by the Recommendation Engine to find candidate resources for a set of skill gaps.
    """
    if not skill_ids:
        return []
    async with pool.acquire() as conn:
        rows = await conn.fetch(
            """
            SELECT DISTINCT
                r.id, r.title, r.description, r.type, r.difficulty,
                r.duration_text, r.why_recommended_template,
                rs.skill_id AS primary_skill_id,
                rs.is_primary
            FROM resources r
            JOIN resource_skills rs ON rs.resource_id = r.id
            WHERE rs.skill_id = ANY($1::text[])
            ORDER BY r.id
            """,
            skill_ids,
        )
        return [dict(r) for r in rows]
