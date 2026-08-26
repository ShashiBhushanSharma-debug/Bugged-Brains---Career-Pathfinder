"""
app/schemas/skills.py

Pydantic schemas for skill analysis.
The GET /api/skills/analysis response mirrors skillsData.js shape.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel, Field


class SkillGapItem(BaseModel):
    """
    A single skill's gap analysis row.
    Mirrors the fields in skillsData.js skills[] plus the computed gap.
    """
    skill_id: str
    name: str
    proficiency_score: int = Field(ge=0, le=100)
    required_score: int = Field(ge=0, le=100)
    gap: int                          # required_score - proficiency_score (can be negative = surplus)
    status: str                       # completed | current | adapted | recommended | locked | not-started
    importance: Optional[str] = None  # core | nice-to-have


class SkillCategory(BaseModel):
    """Matches skillsData.js skillCategories[]"""
    id: str
    label: str
    description: str
    skills: List[SkillGapItem]


class SkillAnalysisResponse(BaseModel):
    """
    Full response for GET /api/skills/analysis.
    Groups skills by category (known / developing / recommended / future)
    so the frontend SkillAnalysis page can render them directly.
    """
    learner_id: str
    career_id: Optional[str] = None
    career_title: Optional[str] = None
    categories: List[SkillCategory]
    # Flat list for the recommendation engine to consume without re-grouping
    all_gaps: List[SkillGapItem]
    # Aggregate readiness: % of career-required skills meeting threshold
    career_readiness_pct: int


class LearnerSkillResponse(BaseModel):
    """Single learner skill row."""
    id: str
    skill_id: str
    name: str
    proficiency_score: int
    status: str
    last_assessed_at: Optional[str] = None


class LearnerSkillUpdate(BaseModel):
    """Used by engine to update proficiency after an assessment."""
    proficiency_score: int = Field(ge=0, le=100)
    status: Optional[str] = None
