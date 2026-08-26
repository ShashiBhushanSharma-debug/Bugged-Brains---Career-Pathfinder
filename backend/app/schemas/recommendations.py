"""
app/schemas/recommendations.py

Pydantic schemas that define the DATA CONTRACT for the Recommendation Engine
(Phase 3). The engine is NOT implemented here — only the input/output types.
"""
from __future__ import annotations

from datetime import datetime
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ── Recommendation Engine INPUT contract ─────────────────────────────────────

class SkillGapForEngine(BaseModel):
    """Compact skill gap row passed to the engine."""
    skill_id: str
    skill_name: str
    proficiency_score: int
    required_score: int
    gap: int


class LearnerContextForEngine(BaseModel):
    """
    Full context the Recommendation Engine needs to score resources.
    Built by the backend from DB data; passed to the engine service in Phase 3.
    """
    learner_id: str
    target_career_id: Optional[str] = None
    target_career_title: Optional[str] = None
    weekly_learning_hours: int = 8
    interests: List[str] = []
    learning_style: Optional[str] = None
    preferred_session_length: Optional[str] = None
    # skill_id -> proficiency_score (0-100) — matches schemas.py LearnerState.skills format
    current_skills: Dict[str, int] = {}
    # Ordered by gap descending (biggest gaps first)
    skill_gaps: List[SkillGapForEngine] = []
    completed_resource_ids: List[str] = []
    in_progress_resource_ids: List[str] = []


# ── Recommendation Engine OUTPUT contract ─────────────────────────────────────

class RecommendationItem(BaseModel):
    """A single ranked recommendation returned by the engine."""
    resource_id: str
    resource_title: str
    resource_type: str
    target_skill_id: Optional[str] = None
    target_skill_name: Optional[str] = None
    score: float = Field(ge=0.0, description="Ranking score. Higher = more relevant.")
    reasoning: Optional[str] = None
    priority: int = Field(ge=1, description="1 = highest priority")
    difficulty: Optional[str] = None
    duration_text: Optional[str] = None
    # Phase 3: structured breakdown for Explainable AI (Member 1) integration.
    # Keys: skill_gap, career_importance, difficulty_fit, preference_fit,
    #       duration_fit, history_context, readiness_mult — all floats in [0, 1].
    score_breakdown: Optional[Dict[str, float]] = None


class RecommendationResponse(BaseModel):
    """GET /api/recommendations response."""
    learner_id: str
    recommendations: List[RecommendationItem]
    generated_at: Optional[datetime] = None
    is_engine_generated: bool = False


# ── POST /api/recommendations request (engine writes back) ────────────────────

class RecommendationWriteRequest(BaseModel):
    """Posted by the Recommendation Engine after it has scored resources."""
    learner_id: str
    recommendations: List[RecommendationItem]


# ── Stored recommendation row ─────────────────────────────────────────────────

class StoredRecommendation(BaseModel):
    """Row from the recommendations table."""
    id: str
    learner_id: str
    resource_id: str
    score: float
    reasoning: Optional[str] = None
    is_active: bool
    generated_at: datetime
