"""
app/services/skills_analysis.py

Business logic for GET /api/skills/analysis.

Calculates:
  - Per-skill gaps: required_score - proficiency_score
  - Category groupings: known / developing / recommended / future
  - Overall career readiness percentage

This is a pure computation layer — it reads from the DB via repositories
and returns structured data. No AI, no graph algorithms.
"""
from __future__ import annotations

from typing import Dict, List, Optional

import asyncpg

from app.database.repositories import learner_repo, skills_repo, careers_repo
from app.schemas.skills import SkillGapItem, SkillCategory, SkillAnalysisResponse

# Category thresholds (mirrors skillsData.js logic):
#   known       → proficiency >= required (no gap or surplus)
#   developing  → gap > 0 and learner has made some progress (proficiency > 0)
#   recommended → gap > 0 and proficiency is low but skill is in scope
#   future      → gap > 0 and proficiency is very low / skill not yet started
_CATEGORIES = [
    {"id": "known",       "label": "You already know",      "description": "Meets or exceeds the bar for your target role."},
    {"id": "developing",  "label": "Currently developing",  "description": "In active progress on your roadmap right now."},
    {"id": "recommended", "label": "Recommended next",      "description": "Highest-leverage skills to pick up next."},
    {"id": "future",      "label": "Future skills",         "description": "Scheduled later, once prerequisites are in place."},
]


def _classify_skill(
    proficiency: int,
    required: int,
    status: str,
) -> str:
    """
    Derive the display category from proficiency, required score, and status.
    Matches the logic implied by skillsData.js without storing the category.
    """
    gap = required - proficiency
    if gap <= 0:
        return "known"
    if status in ("current", "adapted"):
        return "developing"
    if status == "recommended" or (proficiency > 0 and gap <= 55):
        return "recommended"
    return "future"


async def compute_skill_analysis(
    pool: asyncpg.Pool,
    learner_id: str,
) -> SkillAnalysisResponse:
    """
    Main entry point: builds the full skill analysis response.
    """
    # 1. Load learner to get their target career
    learner = await learner_repo.get_learner_by_id(pool, learner_id)
    career_id = learner.get("target_career_id") if learner else None

    # 2. Load learner's skill proficiencies
    learner_skills = await skills_repo.get_learner_skills(pool, learner_id)
    learner_skill_map = {ls["skill_id"]: ls for ls in learner_skills}

    # 3. Load career requirements (if a career is set)
    career = None
    career_skill_map: dict[str, dict] = {}
    if career_id:
        career = await careers_repo.get_career_by_id(pool, career_id)
        career_skills = await skills_repo.get_career_skills(pool, career_id)
        career_skill_map = {cs["skill_id"]: cs for cs in career_skills}

    # 4. Build the union of all relevant skill IDs
    all_skill_ids = set(learner_skill_map.keys()) | set(career_skill_map.keys())

    # 5. Compute gap items
    gap_items: list[SkillGapItem] = []
    met_count = 0
    total_required = 0

    for skill_id in all_skill_ids:
        ls = learner_skill_map.get(skill_id, {})
        cs = career_skill_map.get(skill_id, {})

        proficiency = ls.get("proficiency_score", 0)
        required = cs.get("required_score", 0)
        gap = required - proficiency
        status = ls.get("status", "not-started")
        importance = cs.get("importance")
        name = ls.get("name") or cs.get("name", skill_id)

        gap_items.append(
            SkillGapItem(
                skill_id=skill_id,
                name=name,
                proficiency_score=proficiency,
                required_score=required,
                gap=gap,
                status=status,
                importance=importance,
            )
        )

        if required > 0:
            total_required += 1
            if proficiency >= required:
                met_count += 1

    # Sort: largest gap first within each category
    gap_items.sort(key=lambda x: (-x.gap, x.name))

    # 6. Group into categories
    category_buckets: dict[str, list[SkillGapItem]] = {
        "known": [], "developing": [], "recommended": [], "future": []
    }
    for item in gap_items:
        cat = _classify_skill(item.proficiency_score, item.required_score, item.status)
        category_buckets[cat].append(item)

    categories = [
        SkillCategory(
            id=c["id"],
            label=c["label"],
            description=c["description"],
            skills=category_buckets[c["id"]],
        )
        for c in _CATEGORIES
    ]

    # 7. Career readiness percentage
    career_readiness_pct = (
        round((met_count / total_required) * 100) if total_required > 0 else 0
    )

    return SkillAnalysisResponse(
        learner_id=learner_id,
        career_id=career_id,
        career_title=career.get("title") if career else None,
        categories=categories,
        all_gaps=gap_items,
        career_readiness_pct=career_readiness_pct,
    )
