"""
app/schemas/learning_history.py

Pydantic schemas for GET/POST /api/learning-history.
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class LearningHistoryItem(BaseModel):
    """Single row from the learning_history table."""
    id: str
    learner_id: str
    resource_id: Optional[str] = None
    title: str
    type: str
    status: str
    progress_pct: int = Field(ge=0, le=100)
    completed_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class LearningHistoryResponse(BaseModel):
    items: List[LearningHistoryItem]
    total: int


class LearningHistoryCreateRequest(BaseModel):
    """POST /api/learning-history — start or update a resource for the learner."""
    resource_id: Optional[str] = None
    title: str
    type: str
    status: str = "not-started"
    progress_pct: int = Field(0, ge=0, le=100)


class LearningHistoryUpdateRequest(BaseModel):
    """PATCH /api/learning-history/{id} — update progress on an existing item."""
    status: Optional[str] = None
    progress_pct: Optional[int] = Field(None, ge=0, le=100)


class ActivityLogItem(BaseModel):
    """Single row from the activity_log table."""
    id: str
    type: str
    label: str
    meta: Optional[str] = None
    reference_id: Optional[str] = None
    occurred_at: datetime
