"""
app/api/routes/roadmap.py

GET /api/roadmap — Returns the authenticated learner's personalised roadmap nodes,
prerequisite graph, statuses (completed/current/adapted/recommended/locked),
and latest AI replanning reason.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional
from fastapi import APIRouter, Depends
from asyncpg import Pool
from pydantic import BaseModel

from app.database.connection import get_pool
from app.api.auth import get_current_learner_id
from app.database.repositories import learner_repo

router = APIRouter(prefix="/api", tags=["Roadmap"])


class RoadmapReplanInfo(BaseModel):
    headline: str
    reason: str
    changes: List[Dict[str, Any]] = []
    triggered_at: Optional[str] = None


class RoadmapNodeItem(BaseModel):
    id: str
    title: str
    type: str  # skill | course | project | assessment
    skill_id: Optional[str] = None
    stage: int
    difficulty: Optional[str] = None
    duration: Optional[str] = None
    description: Optional[str] = None
    expectedOutcome: Optional[str] = None
    skillsGained: List[str] = []
    why: List[str] = []
    resources: List[str] = []
    prerequisites: List[str] = []
    status: str = "locked"  # completed | current | adapted | recommended | locked
    adapted_at: Optional[str] = None


class RoadmapResponse(BaseModel):
    career_id: Optional[str] = None
    nodes: List[RoadmapNodeItem] = []
    replan_reason: Optional[RoadmapReplanInfo] = None


@router.get(
    "/roadmap",
    response_model=RoadmapResponse,
    summary="Get learner's personalised roadmap",
    description=(
        "Returns the full ordered roadmap nodes for the authenticated learner's target career, "
        "including per-learner node statuses and the latest AI adaptation rationale."
    ),
)
async def get_roadmap(
    learner_id: str = Depends(get_current_learner_id),
    pool: Pool = Depends(get_pool),
) -> RoadmapResponse:
    # 1. Fetch learner profile to identify target career
    profile = await learner_repo.get_learner_by_id(pool, learner_id)
    if not profile or not profile.get("target_career_id"):
        return RoadmapResponse(career_id=None, nodes=[], replan_reason=None)

    career_id = profile["target_career_id"]

    async with pool.acquire() as conn:
        # 2. Fetch roadmap nodes joined with learner progress
        node_rows = await conn.fetch(
            """
            SELECT
                rn.id, rn.title, rn.type, rn.skill_id, rn.stage,
                rn.difficulty, rn.duration_text, rn.description,
                rn.expected_outcome, rn.skills_gained, rn.why,
                rn.resources_display,
                COALESCE(lrn.status, 'locked') AS status,
                lrn.adapted_at
            FROM roadmap_nodes rn
            LEFT JOIN learner_roadmap_nodes lrn
                ON rn.id = lrn.node_id AND lrn.learner_id = $1
            WHERE rn.career_id = $2
            ORDER BY rn.stage ASC, rn.id ASC
            """,
            learner_id, career_id
        )

        # 3. Fetch all prerequisite edges for these nodes
        prereq_rows = await conn.fetch(
            """
            SELECT node_id, prerequisite_node_id
            FROM roadmap_node_prerequisites
            """
        )
        prereq_map: Dict[str, List[str]] = {}
        for r in prereq_rows:
            prereq_map.setdefault(r["node_id"], []).append(r["prerequisite_node_id"])

        # 4. Fetch latest replan for this learner
        replan_row = await conn.fetchrow(
            """
            SELECT headline, reason, changes, triggered_at
            FROM roadmap_replans
            WHERE learner_id = $1
            ORDER BY triggered_at DESC
            LIMIT 1
            """,
            learner_id
        )

    # 5. Build nodes list
    nodes: List[RoadmapNodeItem] = []
    for r in node_rows:
        skills_gained = r["skills_gained"]
        if isinstance(skills_gained, str):
            try:
                skills_gained = json.loads(skills_gained)
            except Exception:
                skills_gained = []
        elif not skills_gained:
            skills_gained = []

        why = r["why"]
        if isinstance(why, str):
            try:
                why = json.loads(why)
            except Exception:
                why = []
        elif not why:
            why = []

        resources_display = r["resources_display"]
        if isinstance(resources_display, str):
            try:
                resources_display = json.loads(resources_display)
            except Exception:
                resources_display = []
        elif not resources_display:
            resources_display = []

        nodes.append(
            RoadmapNodeItem(
                id=r["id"],
                title=r["title"],
                type=r["type"],
                skill_id=r["skill_id"],
                stage=r["stage"],
                difficulty=r["difficulty"],
                duration=r["duration_text"],
                description=r["description"],
                expectedOutcome=r["expected_outcome"],
                skillsGained=skills_gained,
                why=why,
                resources=resources_display,
                prerequisites=prereq_map.get(r["id"], []),
                status=r["status"],
                adapted_at=r["adapted_at"].isoformat() if r["adapted_at"] else None,
            )
        )

    replan_reason = None
    if replan_row:
        changes = replan_row["changes"]
        if isinstance(changes, str):
            try:
                changes = json.loads(changes)
            except Exception:
                changes = []
        elif not changes:
            changes = []

        replan_reason = RoadmapReplanInfo(
            headline=replan_row["headline"],
            reason=replan_row["reason"],
            changes=changes,
            triggered_at=replan_row["triggered_at"].isoformat() if replan_row["triggered_at"] else None,
        )

    return RoadmapResponse(
        career_id=career_id,
        nodes=nodes,
        replan_reason=replan_reason,
    )
