"""
app/api/routes/recommendations.py

GET  /api/recommendations  — run the Recommendation Engine, persist batch, return results
POST /api/recommendations  — manual write-back (kept for backward compatibility / testing)

Phase 3: GET now calls recommendation_engine.run_recommendation_engine() every
request to produce fresh, personalised recommendations. The previous seeded-data
return has been replaced.
"""
from __future__ import annotations

from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Pool

from app.config import get_settings
from app.database.connection import get_pool
from app.database.repositories import recommendations_repo
from app.schemas.recommendations import (
    RecommendationResponse,
    RecommendationItem,
    RecommendationWriteRequest,
)
from app.services.recommendation_engine import run_recommendation_engine

router = APIRouter(prefix="/api", tags=["Recommendations"])


def _get_learner_id(settings=Depends(get_settings)) -> str:
    """
    Returns the active learner ID.
    Phase 3 (auth): replace with JWT extraction — recorded in FINAL_CHANGES.md (FC-006).
    """
    return settings.dev_learner_id


@router.get(
    "/recommendations",
    response_model=RecommendationResponse,
    summary="Get personalised recommendations (engine-generated)",
    description=(
        "Runs the Phase 3 Recommendation Engine for the current learner. "
        "Scores all candidate resources against 6 personalisation factors "
        "(skill gap, career importance, difficulty fit, preference fit, "
        "duration fit, history context) and a prerequisite readiness multiplier. "
        "Persists the new batch to the recommendations table and returns the "
        "ranked list with score_breakdown for Explainable AI integration."
    ),
)
async def get_recommendations(
    learner_id: str = Depends(_get_learner_id),
    pool: Pool = Depends(get_pool),
) -> RecommendationResponse:
    """
    Pipeline (all steps run on every request for fresh, up-to-date results):
      1. Load learner context
      2. Compute skill gaps vs career requirements
      3. Retrieve all candidate resources
      4. Score each candidate (6 factors + readiness multiplier)
      5. Filter completed; penalise in-progress
      6. Sort, apply diversity pass, assign priority ranks
      7. Persist batch to DB (deactivate old → insert new)
      8. Return RecommendationResponse (is_engine_generated: true)
    """
    engine_results = await run_recommendation_engine(pool, learner_id, persist=True)

    items = [
        RecommendationItem(
            resource_id=r["resource_id"],
            resource_title=r["resource_title"],
            resource_type=r["resource_type"],
            target_skill_id=r.get("target_skill_id"),
            target_skill_name=r.get("target_skill_name"),
            score=r["score"],
            reasoning=r.get("reasoning"),
            priority=r["priority"],
            difficulty=r.get("difficulty"),
            duration_text=r.get("duration_text"),
            score_breakdown=r.get("score_breakdown"),
        )
        for r in engine_results
    ]

    return RecommendationResponse(
        learner_id=learner_id,
        recommendations=items,
        generated_at=datetime.now(timezone.utc),
        is_engine_generated=True,
    )


@router.post(
    "/recommendations",
    response_model=dict,
    status_code=201,
    summary="Save recommendation batch (manual / engine write-back)",
    description=(
        "Manually post a recommendation batch. Kept for backward compatibility "
        "and testing. The GET endpoint now runs the engine automatically, so this "
        "endpoint is mainly used by integration tests and future engine variants."
    ),
)
async def save_recommendations(
    body: RecommendationWriteRequest,
    pool: Pool = Depends(get_pool),
) -> dict:
    # Deactivate old batch
    await recommendations_repo.deactivate_recommendations(pool, body.learner_id)

    # Save new batch
    recs_to_save = [
        {
            "resource_id": item.resource_id,
            "score": item.score,
            "reasoning": item.reasoning,
        }
        for item in body.recommendations
    ]
    count = await recommendations_repo.save_recommendations(pool, body.learner_id, recs_to_save)

    return {
        "success": True,
        "learner_id": body.learner_id,
        "saved": count,
        "message": f"{count} recommendations saved for learner {body.learner_id}.",
    }
