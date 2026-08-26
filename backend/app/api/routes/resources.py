"""
app/api/routes/resources.py

GET /api/resources            — list all resources (optional ?skill_id=&type= filters)
GET /api/resources/{id}       — single resource detail
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from asyncpg import Pool

from app.database.connection import get_pool
from app.database.repositories import resources_repo
from app.schemas.resources import ResourceResponse, ResourceListResponse

router = APIRouter(prefix="/api", tags=["Resources"])


@router.get(
    "/resources",
    response_model=ResourceListResponse,
    summary="List learning resources",
    description=(
        "Returns the resource catalog with optional filters. "
        "Mirrors the data shape of coursesData.js resources[] (without per-learner progress). "
        "Filter by skill_id to get resources for a specific skill. "
        "Filter by type (course|video|article|documentation|project|practice)."
    ),
)
async def list_resources(
    skill_id: Optional[str] = Query(default=None, description="Filter by skill ID, e.g. sk_react"),
    type: Optional[str] = Query(default=None, description="Filter by resource type"),
    pool: Pool = Depends(get_pool),
) -> ResourceListResponse:
    rows = await resources_repo.get_all_resources(pool, skill_id=skill_id, resource_type=type)
    resources = []
    for r in rows:
        skill_ids = r.get("skill_ids") or []
        resources.append(
            ResourceResponse(
                id=r["id"],
                title=r["title"],
                description=r.get("description"),
                type=r["type"],
                difficulty=r.get("difficulty"),
                duration_text=r.get("duration_text"),
                url=r.get("url"),
                why_recommended_template=r.get("why_recommended_template"),
                primary_skill_id=r.get("primary_skill_id"),
                primary_skill_name=r.get("primary_skill_name"),
                skill_ids=list(skill_ids) if skill_ids else [],
            )
        )
    return ResourceListResponse(resources=resources, total=len(resources))


@router.get(
    "/resources/{resource_id}",
    response_model=ResourceResponse,
    summary="Get single resource",
)
async def get_resource(
    resource_id: str,
    pool: Pool = Depends(get_pool),
) -> ResourceResponse:
    row = await resources_repo.get_resource_by_id(pool, resource_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"Resource '{resource_id}' not found.")
    return ResourceResponse(**row)
