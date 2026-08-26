"""
app/schemas/resources.py

Pydantic schemas for the resource catalog.
Mirrors coursesData.js resources[] shape.
"""
from __future__ import annotations

from typing import List, Optional

from pydantic import BaseModel


class ResourceResponse(BaseModel):
    """
    Single resource row from the global catalog.
    Mirrors coursesData.js resources[] shape (minus per-learner progress).
    """
    id: str
    title: str
    description: Optional[str] = None
    type: str                            # course | video | article | documentation | project | practice
    difficulty: Optional[str] = None     # Beginner | Intermediate | Advanced
    duration_text: Optional[str] = None  # '3 wks', '20 min'
    url: Optional[str] = None
    why_recommended_template: Optional[str] = None
    # Primary skill this resource teaches (from resource_skills)
    primary_skill_id: Optional[str] = None
    primary_skill_name: Optional[str] = None
    # All skill IDs this resource covers
    skill_ids: List[str] = []


class ResourceListResponse(BaseModel):
    resources: List[ResourceResponse]
    total: int
