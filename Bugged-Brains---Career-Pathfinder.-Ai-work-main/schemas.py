from typing import List, Dict, Optional, Literal
from pydantic import BaseModel, Field


class LearnerState(BaseModel):
    learner_id: str
    target_goal: str
    skills: Dict[str, float] = Field(
        default_factory=dict, 
        description="Skill name to continuous mastery probability [0.0 to 1.0]"
    )
    weekly_hours: int = Field(default=8, ge=1, le=80)
    preferred_learning_style: Literal["video", "project_based", "reading", "hybrid"] = "project_based"
    difficulty_tolerance: Literal["gentle", "standard", "accelerated"] = "standard"


class NodeRationale(BaseModel):
    goal_alignment_score: float = Field(ge=0.0, le=1.0, description="Score indicating alignment with target goal")
    skill_gap_addressed: str = Field(description="The specific deficiency or gap this node targets")
    prerequisite_context: str = Field(description="Explanation of upstream dependencies completed or required")
    why_now_explanation: str = Field(description="Concise natural language explanation of 'Why this resource at this exact stage?'")


class RoadmapStep(BaseModel):
    step_id: str
    title: str
    resource_type: Literal["course", "project", "assessment", "refresher", "capstone"]
    target_skill: str
    difficulty: Literal["beginner", "intermediate", "advanced"]
    estimated_hours: int
    is_completed: bool = False
    rationale: NodeRationale


class LearningRoadmap(BaseModel):
    learner_id: str
    target_goal: str
    total_estimated_weeks: int
    milestone_count: int
    steps: List[RoadmapStep]


class AssessmentSignal(BaseModel):
    step_id: str
    target_skill: str
    score_percentage: float = Field(ge=0.0, le=100.0, description="Assessment score from 0 to 100")
    assessment_difficulty: Literal["beginner", "intermediate", "advanced"] = "intermediate"
    user_feedback: Optional[str] = None  # e.g., "Pacing was too fast", "I already mastered this concept"