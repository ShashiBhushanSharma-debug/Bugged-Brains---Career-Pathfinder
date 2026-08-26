"""
app/schemas/onboarding.py

Pydantic schema for POST /api/onboarding.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class OnboardingSkillInput(BaseModel):
    """A single skill + proficiency submitted during onboarding."""
    skill_id: str
    proficiency_score: int = Field(ge=0, le=100)


class OnboardingHistoryItem(BaseModel):
    """A prior learning item the learner reports during onboarding."""
    title: str
    type: str  # course | project | video | article | practice | documentation
    resource_id: Optional[str] = None


class OnboardingRequest(BaseModel):
    """Body for POST /api/onboarding."""
    learner_id: str
    name: str
    first_name: Optional[str] = None
    target_career_id: Optional[str] = None
    current_level: Optional[str] = None
    weekly_learning_hours: int = Field(8, ge=1, le=80)
    interests: List[str] = []
    learning_style: Optional[str] = None
    preferred_session_length: Optional[str] = None
    learning_preferences: Optional[Dict[str, Any]] = None
    skills: List[OnboardingSkillInput] = []
    prior_learning: List[OnboardingHistoryItem] = []


class OnboardingResponse(BaseModel):
    """Response confirming what was persisted."""
    success: bool
    learner_id: str
    skills_saved: int
    history_saved: int
    message: str
