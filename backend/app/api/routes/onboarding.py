"""
app/api/routes/onboarding.py

POST /api/onboarding

Persists initial learner data collected by the frontend Onboarding page into:
  - learner_profiles
  - learner_skills
  - learning_history
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Pool

from app.database.connection import get_pool
from app.database.repositories import learner_repo, skills_repo, learning_history_repo
from app.schemas.onboarding import OnboardingRequest, OnboardingResponse

router = APIRouter(prefix="/api", tags=["Onboarding"])


@router.post(
    "/onboarding",
    response_model=OnboardingResponse,
    status_code=201,
    summary="Save onboarding data",
    description=(
        "Accepts the full onboarding form submission and persists it into "
        "learner_profiles, learner_skills, and learning_history. "
        "Idempotent — re-submitting with the same learner_id will upsert."
    ),
)
async def submit_onboarding(
    body: OnboardingRequest,
    pool: Pool = Depends(get_pool),
) -> OnboardingResponse:
    # 1. Upsert learner profile
    profile_data = {
        "id": body.learner_id,
        "name": body.name,
        "first_name": body.first_name,
        "target_career_id": body.target_career_id,
        "current_level": body.current_level,
        "weekly_learning_hours": body.weekly_learning_hours,
        "interests": body.interests or None,
        "learning_style": body.learning_style,
        "preferred_session_length": body.preferred_session_length,
        "learning_preferences": body.learning_preferences,
        "notification_settings": None,
    }
    try:
        await learner_repo.create_learner(pool, profile_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save learner profile: {e}")

    # 2. Bulk upsert skills
    skills_saved = 0
    if body.skills:
        skill_dicts = [
            {"skill_id": s.skill_id, "proficiency_score": s.proficiency_score}
            for s in body.skills
        ]
        try:
            skills_saved = await skills_repo.bulk_upsert_learner_skills(
                pool, body.learner_id, skill_dicts
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save skills: {e}")

    # 3. Bulk insert prior learning history
    history_saved = 0
    if body.prior_learning:
        history_items = [
            {"title": h.title, "type": h.type, "resource_id": h.resource_id}
            for h in body.prior_learning
        ]
        try:
            history_saved = await learning_history_repo.bulk_create_history(
                pool, body.learner_id, history_items
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save learning history: {e}")

    # 4. Log the onboarding activity
    try:
        await learning_history_repo.log_activity(
            pool,
            learner_id=body.learner_id,
            event_type="onboarding",
            label="Completed onboarding",
            meta=f"Target: {body.target_career_id or 'not set'}",
        )
    except Exception:
        pass  # Activity log failure is non-critical

    return OnboardingResponse(
        success=True,
        learner_id=body.learner_id,
        skills_saved=skills_saved,
        history_saved=history_saved,
        message=(
            f"Profile created for {body.name}. "
            f"{skills_saved} skills and {history_saved} history items saved."
        ),
    )
