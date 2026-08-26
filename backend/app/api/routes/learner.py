"""
app/api/routes/learner.py

GET  /api/me     — return the current learner's profile
PATCH /api/me    — update learner profile fields
GET  /api/me/activity — return recent activity log
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from asyncpg import Pool

from app.config import get_settings
from app.database.connection import get_pool
from app.database.repositories import learner_repo, learning_history_repo
from app.schemas.learner import LearnerProfileResponse, LearnerProfileUpdate
from app.schemas.learning_history import ActivityLogItem

router = APIRouter(prefix="/api", tags=["Learner"])


def _get_learner_id(
    # Phase 3: this will extract learner_id from the JWT token.
    # For now it falls back to the DEV_LEARNER_ID env variable.
    settings=Depends(get_settings),
) -> str:
    return settings.dev_learner_id


@router.get(
    "/me",
    response_model=LearnerProfileResponse,
    summary="Get current learner profile",
    description=(
        "Returns the full learner profile for the authenticated user. "
        "In development mode, returns the profile for DEV_LEARNER_ID. "
        "Mirrors the shape of userData.js `currentUser`."
    ),
)
async def get_me(
    learner_id: str = Depends(_get_learner_id),
    pool: Pool = Depends(get_pool),
) -> LearnerProfileResponse:
    profile = await learner_repo.get_learner_by_id(pool, learner_id)
    if not profile:
        raise HTTPException(status_code=404, detail=f"Learner '{learner_id}' not found.")
    return LearnerProfileResponse(**profile)


@router.patch(
    "/me",
    response_model=LearnerProfileResponse,
    summary="Update learner profile",
    description="Partially update the learner's profile. Only provided fields are changed.",
)
async def update_me(
    body: LearnerProfileUpdate,
    learner_id: str = Depends(_get_learner_id),
    pool: Pool = Depends(get_pool),
) -> LearnerProfileResponse:
    updates = body.model_dump(exclude_none=True)
    updated = await learner_repo.update_learner(pool, learner_id, updates)
    if not updated:
        raise HTTPException(status_code=404, detail=f"Learner '{learner_id}' not found.")
    return LearnerProfileResponse(**updated)


@router.get(
    "/me/activity",
    response_model=list[ActivityLogItem],
    summary="Get recent activity log",
    description="Returns the learner's recent activity feed, most recent first.",
)
async def get_activity(
    limit: int = Query(default=20, ge=1, le=100),
    learner_id: str = Depends(_get_learner_id),
    pool: Pool = Depends(get_pool),
) -> list[ActivityLogItem]:
    rows = await learning_history_repo.get_activity_log(pool, learner_id, limit=limit)
    return [ActivityLogItem(**r) for r in rows]
