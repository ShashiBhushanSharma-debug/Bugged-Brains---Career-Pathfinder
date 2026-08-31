"""
app/api/routes/skills.py

GET /api/skills/analysis  — per-skill gap analysis for the current learner
GET /api/skills           — global skill catalog
GET /api/careers          — career catalog
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from asyncpg import Pool

from app.database.connection import get_pool
from app.api.auth import get_current_learner_id
from app.database.repositories import skills_repo, careers_repo
from app.schemas.skills import SkillAnalysisResponse, LearnerSkillResponse
from app.services.skills_analysis import compute_skill_analysis

router = APIRouter(prefix="/api", tags=["Skills"])





@router.get(
    "/skills/analysis",
    response_model=SkillAnalysisResponse,
    summary="Skill gap analysis",
    description=(
        "Returns per-skill proficiency vs required scores grouped into categories "
        "(known / developing / recommended / future). "
        "Mirrors the data shape of skillsData.js so the frontend SkillAnalysis page "
        "can consume this directly."
    ),
)
async def get_skill_analysis(
    learner_id: str = Depends(get_current_learner_id),
    pool: Pool = Depends(get_pool),
) -> SkillAnalysisResponse:
    return await compute_skill_analysis(pool, learner_id)


@router.get(
    "/skills",
    summary="Global skill catalog",
    description="Returns all skills in the catalog.",
)
async def get_skills(pool: Pool = Depends(get_pool)) -> list[dict]:
    return await skills_repo.get_all_skills(pool)


@router.get(
    "/skills/{skill_id}",
    summary="Single skill",
)
async def get_skill(skill_id: str, pool: Pool = Depends(get_pool)) -> dict:
    skill = await skills_repo.get_skill_by_id(pool, skill_id)
    if not skill:
        raise HTTPException(status_code=404, detail=f"Skill '{skill_id}' not found.")
    return skill


@router.get(
    "/careers",
    summary="Career catalog",
    description="Returns all available target careers.",
)
async def get_careers(pool: Pool = Depends(get_pool)) -> list[dict]:
    return await careers_repo.get_all_careers(pool)


@router.get(
    "/careers/{career_id}",
    summary="Single career with required skills",
)
async def get_career(career_id: str, pool: Pool = Depends(get_pool)) -> dict:
    career = await careers_repo.get_career_by_id(pool, career_id)
    if not career:
        raise HTTPException(status_code=404, detail=f"Career '{career_id}' not found.")
    required_skills = await skills_repo.get_career_skills(pool, career_id)
    career["required_skills"] = required_skills
    return career
