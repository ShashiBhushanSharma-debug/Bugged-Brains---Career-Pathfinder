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
from pydantic import BaseModel
from app.services.ai_adaptive_graph import adaptive_graph_app

router = APIRouter(prefix="/api", tags=["Learner"])


def _get_learner_id(
    # Phase 3: this will extract learner_id from the JWT token.
    # For now it falls back to the DEV_LEARNER_ID env variable.
    settings=Depends(get_settings),
) -> str:
    return settings.dev_learner_id

class AssessmentSignal(BaseModel):
    step_id: str
    target_skill_id: str
    score_percentage: float
    user_feedback: str | None = None

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

@router.post(
    "/me/replan",
    summary="Trigger AI Adaptive Replanning",
    description="Runs Bayesian Knowledge Tracing and a LangGraph LLM agent to dynamically adjust the learner's roadmap based on assessment results.",
)
async def trigger_adaptive_replan(
    signal: AssessmentSignal,
    learner_id: str = Depends(_get_learner_id),
    pool: Pool = Depends(get_pool),
) -> dict:
    # 1. Fetch current learner state
    profile = await learner_repo.get_learner_by_id(pool, learner_id)
    if not profile or not profile.get("target_career_id"):
        raise HTTPException(status_code=400, detail="Learner profile or target career not found.")
        
    # 2. Fetch current skill proficiencies
    async with pool.acquire() as conn:
        skill_rows = await conn.fetch(
            "SELECT skill_id, proficiency_score FROM learner_skills WHERE learner_id = $1", 
            learner_id
        )
    current_skills = {r["skill_id"]: float(r["proficiency_score"]) / 100.0 for r in skill_rows}

    # 3. Construct the initial state for LangGraph
    initial_state = {
        "pool": pool,
        "learner_id": learner_id,
        "target_career_id": profile["target_career_id"],
        "assessment_signal": signal.model_dump(),
        "current_skills": current_skills,
        "career_requirements": {},
        "skill_gaps": [],
        "current_roadmap_nodes": [],
        "new_mastery_score": None,
        "replan_output": None,
        "replan_status_message": ""
    }

    # 4. Execute the Async LangGraph Workflow
    final_state = await adaptive_graph_app.ainvoke(initial_state)

    # 5. Return the LLM's structured output to the frontend
    return {
        "status": "success",
        "headline": final_state["replan_status_message"],
        "updated_mastery": final_state["new_mastery_score"],
        "roadmap": final_state["replan_output"]
    }
