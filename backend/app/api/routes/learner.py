"""
app/api/routes/learner.py

GET  /api/me     — return the current learner's profile
PATCH /api/me    — update learner profile fields
GET  /api/me/activity — return recent activity log
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from asyncpg import Pool

from app.database.connection import get_pool
from app.api.auth import get_current_learner_id
from app.database.repositories import learner_repo, learning_history_repo
from app.schemas.learner import LearnerProfileResponse, LearnerProfileUpdate
from app.schemas.learning_history import ActivityLogItem
from typing import Optional
import json
import logging
from pydantic import BaseModel
from app.services.ai_adaptive_graph import adaptive_graph_app

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api", tags=["Learner"])


# _get_learner_id has been replaced by the centralised get_current_learner_id
# dependency in app/api/auth.py — it verifies Supabase JWTs.

class AssessmentSignal(BaseModel):
    step_id: str
    target_skill_id: str
    score_percentage: float
    user_feedback: Optional[str] = None

@router.get(
    "/me",
    response_model=LearnerProfileResponse,
    summary="Get current learner profile",
    description=(
        "Returns the full learner profile for the authenticated user. "
        "In development mode, returns the profile for DEV_LEARNER_ID if unauthenticated. "
        "If a newly authenticated user (e.g. Google OAuth) does not have a profile yet, "
        "creates and links an initial profile automatically."
    ),
)
async def get_me(
    request: Request,
    learner_id: str = Depends(get_current_learner_id),
    pool: Pool = Depends(get_pool),
) -> LearnerProfileResponse:
    profile = await learner_repo.get_learner_by_id(pool, learner_id)
    if not profile:
        # Auto-create initial learner profile for newly authenticated user (e.g. Google OAuth)
        user_info = getattr(request.state, "user_info", {}) or {}
        raw_name = user_info.get("full_name") or (user_info.get("email") or "").split("@")[0] or "Learner"
        first_name = raw_name.split()[0] if raw_name else "Learner"
        starter_data = {
            "id": learner_id,
            "name": raw_name,
            "first_name": first_name,
            "target_career_id": None,
            "current_level": "Beginner",
            "weekly_learning_hours": 8,
            "interests": [],
            "learning_style": None,
            "preferred_session_length": "30-45 min",
            "learning_preferences": {
                "pace": "Steady (3-5 sessions / week)",
                "format": ["Interactive courses", "Hands-on projects"],
                "difficulty": "Push me slightly beyond current level",
            },
            "notification_settings": {
                "roadmapUpdates": True,
                "weeklyDigest": True,
                "assessmentReminders": True,
                "productNews": False,
            },
            "current_focus_skill_id": None,
        }
        profile = await learner_repo.create_learner(pool, starter_data)
    return LearnerProfileResponse(**profile)


@router.patch(
    "/me",
    response_model=LearnerProfileResponse,
    summary="Update learner profile",
    description="Partially update the learner's profile. Only provided fields are changed.",
)
async def update_me(
    body: LearnerProfileUpdate,
    learner_id: str = Depends(get_current_learner_id),
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
    learner_id: str = Depends(get_current_learner_id),
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
    learner_id: str = Depends(get_current_learner_id),
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

    # 5. Log activity and record assessment result in DB
    score_int = int(round(signal.score_percentage))
    assessment_title = signal.step_id.replace("as_", "").replace("_", " ").title()
    try:
        await learning_history_repo.log_activity(
            pool,
            learner_id=learner_id,
            event_type="assessment",
            label=f"Completed {assessment_title} check-in",
            meta=f"Scored {score_int}%",
            reference_id=signal.step_id,
        )
    except Exception as e:
        logger.warning(f"Could not log assessment activity: {e}")

    try:
        async with pool.acquire() as conn:
            await conn.execute(
                """
                INSERT INTO assessment_results (
                    learner_id, assessment_id, score_pct, correct_count, total_questions,
                    answers, skill_performance, strengths, weak_areas, recommended_next,
                    triggered_replan
                )
                VALUES ($1, $2, $3, $4, $5, $6::jsonb, $7::jsonb, $8, $9, $10, $11)
                """,
                learner_id,
                signal.step_id,
                score_int,
                max(1, int(round(score_int / 100.0 * 6))),
                6,
                json.dumps({}),
                json.dumps([{"skill": signal.target_skill_id, "percent": score_int}]),
                [signal.target_skill_id] if score_int >= 70 else [],
                [] if score_int >= 70 else [signal.target_skill_id],
                final_state.get("replan_status_message", ""),
                True,
            )
    except Exception as e:
        logger.warning(f"Could not persist assessment result: {e}")

    # 6. Return the LLM's structured output to the frontend
    return {
        "status": "success",
        "headline": final_state["replan_status_message"],
        "updated_mastery": final_state["new_mastery_score"],
        "roadmap": final_state["replan_output"],
    }

