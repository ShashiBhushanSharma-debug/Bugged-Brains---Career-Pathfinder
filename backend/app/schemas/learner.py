"""
app/schemas/learner.py

Pydantic request/response schemas for learner profiles.
These mirror the shape of userData.js and the GET /api/me response contract.
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


# ── Response ──────────────────────────────────────────────────────────────────

class LearnerProfileResponse(BaseModel):
    """
    Full learner profile returned by GET /api/me.
    Matches the shape of userData.js `currentUser` so the frontend
    can swap from mock data to this response without structural changes.
    """
    id: str
    name: str
    first_name: Optional[str] = None
    target_career_id: Optional[str] = None
    current_level: Optional[str] = None
    career_readiness: Optional[int] = None
    overall_progress: Optional[int] = None
    streak_days: int = 0
    weekly_learning_hours: int = 8
    total_learning_hours: int = 0
    interests: Optional[List[str]] = None
    learning_style: Optional[str] = None
    preferred_session_length: Optional[str] = None
    learning_preferences: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None
    current_focus_skill_id: Optional[str] = None
    joined_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ── Update ────────────────────────────────────────────────────────────────────

class LearnerProfileUpdate(BaseModel):
    """
    Fields the learner can update on their profile (PATCH /api/me).
    All fields are optional — only provided fields are updated.
    """
    name: Optional[str] = None
    first_name: Optional[str] = None
    target_career_id: Optional[str] = None
    current_level: Optional[str] = None
    weekly_learning_hours: Optional[int] = Field(None, ge=1, le=80)
    interests: Optional[List[str]] = None
    learning_style: Optional[str] = None
    preferred_session_length: Optional[str] = None
    learning_preferences: Optional[Dict[str, Any]] = None
    notification_settings: Optional[Dict[str, Any]] = None
    current_focus_skill_id: Optional[str] = None
