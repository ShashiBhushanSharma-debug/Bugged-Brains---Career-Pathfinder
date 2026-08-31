"""
app/api/routes/onboarding.py

POST /api/onboarding

Persists initial learner data collected by the frontend Onboarding page into:
  - learner_profiles
  - learner_skills
  - learning_history
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from asyncpg import Pool

from app.database.connection import get_pool
from app.api.auth import get_current_learner_id
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
        "The learner_id is derived from the authenticated Supabase user. "
        "Idempotent — re-submitting will upsert."
    ),
)
async def submit_onboarding(
    body: OnboardingRequest,
    request: Request,
    learner_id: str = Depends(get_current_learner_id),
    pool: Pool = Depends(get_pool),
) -> OnboardingResponse:
    # Strictly enforce authenticated identity from token when authenticated
    is_authenticated = getattr(request.state, "is_authenticated", False)
    target_learner_id = learner_id if is_authenticated else (body.learner_id or learner_id)

    # 1. Upsert learner profile
    profile_data = {
        "id": target_learner_id,
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
        "onboarding_completed": True,
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
                pool, target_learner_id, skill_dicts
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
                pool, target_learner_id, history_items
            )
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Failed to save learning history: {e}")

    # 4. Initialize learner roadmap nodes if career is selected
    if body.target_career_id:
        try:
            async with pool.acquire() as conn:
                nodes = await conn.fetch(
                    "SELECT id, skill_id, stage FROM roadmap_nodes WHERE career_id = $1 ORDER BY stage ASC",
                    body.target_career_id
                )
                if nodes:
                    user_skill_scores = {s.skill_id: s.proficiency_score for s in (body.skills or [])}
                    first_uncompleted = False
                    for node in nodes:
                        n_id = node["id"]
                        s_id = node["skill_id"]
                        score = user_skill_scores.get(s_id, 0)
                        if score >= 70:
                            node_status = "completed"
                        elif not first_uncompleted:
                            node_status = "current"
                            first_uncompleted = True
                        elif score > 0:
                            node_status = "recommended"
                        else:
                            node_status = "locked"

                        await conn.execute(
                            """
                            INSERT INTO learner_roadmap_nodes (learner_id, node_id, status)
                            VALUES ($1, $2, $3)
                            ON CONFLICT (learner_id, node_id) DO UPDATE SET status = EXCLUDED.status
                            """,
                            target_learner_id, n_id, node_status
                        )
        except Exception:
            pass  # Non-fatal if roadmap templates don't exist for a custom career

    # 5. Log the onboarding activity
    try:
        await learning_history_repo.log_activity(
            pool,
            learner_id=target_learner_id,
            event_type="onboarding",
            label="Completed onboarding",
            meta=f"Target: {body.target_career_id or 'not set'}",
        )
    except Exception:
        pass  # Activity log failure is non-critical

    return OnboardingResponse(
        success=True,
        learner_id=target_learner_id,
        skills_saved=skills_saved,
        history_saved=history_saved,
        message=(
            f"Profile created for {body.name}. "
            f"{skills_saved} skills and {history_saved} history items saved."
        ),
    )
