"""
app/api/routes/learning_history.py

GET   /api/learning-history         — list history items (optional ?status= filter)
POST  /api/learning-history         — start a resource / create a history item
PATCH /api/learning-history/{id}    — update progress on an existing item
GET   /api/learning-history/{id}    — single history item
"""
from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from asyncpg import Pool

from app.database.connection import get_pool
from app.api.auth import get_current_learner_id
from app.database.repositories import learning_history_repo
from app.schemas.learning_history import (
    LearningHistoryItem,
    LearningHistoryResponse,
    LearningHistoryCreateRequest,
    LearningHistoryUpdateRequest,
)

router = APIRouter(prefix="/api", tags=["Learning History"])





@router.get(
    "/learning-history",
    response_model=LearningHistoryResponse,
    summary="Get learning history",
    description=(
        "Returns the learner's resource progress history. "
        "Mirrors userData.js learningHistory[] and coursesData.js per-learner progress. "
        "Filter by status: completed | in-progress | not-started."
    ),
)
async def get_learning_history(
    status: Optional[str] = Query(default=None, description="Filter by status"),
    learner_id: str = Depends(get_current_learner_id),
    pool: Pool = Depends(get_pool),
) -> LearningHistoryResponse:
    rows = await learning_history_repo.get_learning_history(pool, learner_id, status=status)
    items = [LearningHistoryItem(**r) for r in rows]
    return LearningHistoryResponse(items=items, total=len(items))


@router.get(
    "/learning-history/{item_id}",
    response_model=LearningHistoryItem,
    summary="Get single history item",
)
async def get_history_item(
    item_id: str,
    learner_id: str = Depends(get_current_learner_id),
    pool: Pool = Depends(get_pool),
) -> LearningHistoryItem:
    row = await learning_history_repo.get_history_item_by_id(pool, learner_id, item_id)
    if not row:
        raise HTTPException(status_code=404, detail=f"History item '{item_id}' not found.")
    return LearningHistoryItem(**row)


@router.post(
    "/learning-history",
    response_model=LearningHistoryItem,
    status_code=201,
    summary="Start or track a resource",
    description="Create a new learning history entry when a learner starts a resource.",
)
async def create_history_item(
    body: LearningHistoryCreateRequest,
    learner_id: str = Depends(get_current_learner_id),
    pool: Pool = Depends(get_pool),
) -> LearningHistoryItem:
    # Check for duplicate
    if body.resource_id:
        existing = await learning_history_repo.get_history_by_resource(
            pool, learner_id, body.resource_id
        )
        if existing:
            raise HTTPException(
                status_code=409,
                detail=f"Resource '{body.resource_id}' is already tracked. Use PATCH to update progress.",
            )

    data = body.model_dump()
    row = await learning_history_repo.create_history_item(pool, learner_id, data)
    return LearningHistoryItem(**row)


@router.patch(
    "/learning-history/{item_id}",
    response_model=LearningHistoryItem,
    summary="Update resource progress",
    description="Update status and/or progress percentage on an existing history item.",
)
async def update_history_item(
    item_id: str,
    body: LearningHistoryUpdateRequest,
    learner_id: str = Depends(get_current_learner_id),
    pool: Pool = Depends(get_pool),
) -> LearningHistoryItem:
    updates = body.model_dump(exclude_none=True)
    if not updates:
        raise HTTPException(status_code=400, detail="No update fields provided.")

    row = await learning_history_repo.update_history_item(pool, learner_id, item_id, updates)
    if not row:
        raise HTTPException(status_code=404, detail=f"History item '{item_id}' not found.")

    # Log activity if completed
    if updates.get("status") == "completed":
        item = await learning_history_repo.get_history_item_by_id(pool, learner_id, item_id)
        if item:
            await learning_history_repo.log_activity(
                pool,
                learner_id=learner_id,
                event_type=item.get("type", "course"),
                label=f'Completed "{item["title"]}"',
                meta="100% complete",
                reference_id=item.get("resource_id"),
            )

    return LearningHistoryItem(**row)
