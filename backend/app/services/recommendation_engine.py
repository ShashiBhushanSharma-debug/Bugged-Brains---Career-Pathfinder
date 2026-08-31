"""
app/services/recommendation_engine.py

Phase 3 — Personalized Recommendation Engine (GenAI & Vector Search Upgrade).

Algorithm: Multi-factor weighted ranking with semantic pgvector similarity.

Pipeline:
  1. Load learner context (profile, career, skills, history)
  2. Identify the learner's largest skill gap and fetch its vector embedding.
  3. Perform a semantic similarity search in Supabase (pgvector) to find candidate resources.
  4. Score candidates against 7 factors (now including semantic relevance).
  5. Apply diversity pass and assign priority ranks.
  6. Persist to recommendations table.
"""
from __future__ import annotations

import json
import re
from typing import Dict, List, Optional

import asyncpg

from app.database.repositories import (
    learner_repo,
    skills_repo,
    resources_repo,
    learning_history_repo,
    recommendations_repo,
)

# ── Weight configuration (Upgraded with Semantic Relevance) ────────────────────
WEIGHTS: Dict[str, float] = {
    "semantic_relevance": 0.25,   # NEW: AI Vector similarity score
    "skill_gap":          0.20,   # Adjusted to balance with semantics
    "career_importance":  0.18,
    "difficulty_fit":     0.15,
    "preference_fit":     0.12,
    "duration_fit":       0.05,
    "history_context":    0.05,
}

_LEVEL_ORDER: Dict[str, float] = {
    "Beginner":      1.0,
    "Intermediate":  2.0,
    "Advanced":      3.0,
    "Comprehensive": 3.5,
}

_PREREQ_MET_THRESHOLD = 50
_DIVERSITY_TYPE_LIMIT = 2
_DIVERSITY_PENALTY    = 0.90

# ==============================================================================
# Internal helper functions (Kept exactly as you wrote them)
# ==============================================================================

def _parse_learner_level(level_str: Optional[str]) -> float:
    if not level_str: return 1.5
    parts = level_str.split("-")
    vals = [
        val for p in parts for key, val in _LEVEL_ORDER.items() if key.lower() in p.lower()
    ]
    return sum(vals) / len(vals) if vals else 1.5

def _score_difficulty_fit(resource_difficulty: Optional[str], learner_level: Optional[str]) -> float:
    r_lvl = _LEVEL_ORDER.get(resource_difficulty or "Intermediate", 2.0)
    l_lvl = _parse_learner_level(learner_level)
    diff = r_lvl - l_lvl

    if diff == 0.0: return 1.00
    elif 0 < diff <= 0.5: return 0.95
    elif 0 < diff <= 1.0: return 0.85
    elif 0 < diff <= 1.5: return 0.60
    elif diff > 1.5: return 0.30
    elif -0.5 <= diff < 0: return 0.90
    elif -1.0 <= diff < -0.5: return 0.75
    elif -1.5 <= diff < -1.0: return 0.60
    else: return 0.45

def _score_preference_fit(resource_type: Optional[str], learner: dict) -> float:
    rtype = (resource_type or "").lower()
    learning_style = (learner.get("learning_style") or "").lower()
    prefs = learner.get("learning_preferences") or {}
    if isinstance(prefs, str):
        try: prefs = json.loads(prefs)
        except Exception: prefs = {}
    formats = [f.lower() for f in (prefs.get("format") or [])]

    _BASE = {"project": 0.65, "course": 0.65, "practice": 0.55, "video": 0.55, "documentation": 0.50, "article": 0.45}
    score = _BASE.get(rtype, 0.50)

    if "project" in learning_style and rtype in ("project", "practice"):
        score = min(1.0, score + (0.30 if rtype == "project" else 0.15))
    if "video" in learning_style and rtype == "video":
        score = min(1.0, score + 0.20)

    _FORMAT_BOOSTS = {"interactive courses": ("course",), "hands-on projects": ("project", "practice"), "short assessments": ("practice",)}
    for pref_key, boosted_types in _FORMAT_BOOSTS.items():
        if pref_key in formats and rtype in boosted_types:
            score = min(1.0, score + 0.15)
    return round(score, 4)

_DURATION_RE = re.compile(r"(\d+)\s*(min|hr|wk|week)", re.IGNORECASE)

def _parse_duration_bucket(duration_text: Optional[str]) -> str:
    if not duration_text: return "medium"
    m = _DURATION_RE.search(duration_text.lower())
    if not m: return "medium"
    val, unit = int(m.group(1)), m.group(2).lower()
    if unit.startswith("wk") or unit.startswith("week") or (unit == "hr" and val > 1): return "multi-session"
    if unit == "hr" or (val > 30 and val <= 60): return "medium"
    if val <= 30: return "short"
    return "multi-session"

def _score_duration_fit(duration_text: Optional[str], preferred_session: Optional[str]) -> float:
    bucket = _parse_duration_bucket(duration_text)
    preferred = (preferred_session or "").lower()
    _TABLE = {
        "15": {"short": 1.00, "medium": 0.75, "multi-session": 0.55},
        "20": {"short": 1.00, "medium": 0.75, "multi-session": 0.55},
        "30": {"short": 0.85, "medium": 1.00, "multi-session": 0.75},
        "45": {"short": 0.85, "medium": 1.00, "multi-session": 0.75},
        "60": {"short": 0.70, "medium": 0.90, "multi-session": 1.00},
    }
    for keyword, scores in _TABLE.items():
        if keyword in preferred: return scores[bucket]
    return {"short": 0.80, "medium": 0.90, "multi-session": 0.75}.get(bucket, 0.80)

def _score_history_context(resource_id: str, history_map: dict) -> float:
    hist = history_map.get(resource_id)
    if not hist: return 1.0
    status = hist.get("status", "not-started")
    if status == "completed": return -1.0
    if status == "in-progress": return 0.15
    return 1.0

def _compute_readiness_multiplier(primary_skill_id: Optional[str], learner_skill_status_map: dict, learner_prof_map: dict, prereq_map: dict) -> float:
    if not primary_skill_id: return 1.0
    if learner_skill_status_map.get(primary_skill_id, "not-started") in ("current", "adapted", "recommended"): return 1.0
    prereqs = prereq_map.get(primary_skill_id, [])
    if not prereqs: return 1.0
    ratio = sum(1 for p in prereqs if learner_prof_map.get(p, 0) >= _PREREQ_MET_THRESHOLD) / len(prereqs)
    if ratio >= 1.0: return 1.00
    elif ratio >= 0.5: return 0.80
    return 0.50

def _generate_reasoning(target_skill_name: Optional[str], skill_gap_pts: int, primary_importance: str, score_breakdown: dict) -> str:
    parts: List[str] = []
    
    # NEW: Acknowledge semantic connections in reasoning
    if score_breakdown.get("semantic_relevance", 0) >= 0.85:
        parts.append("Conceptually highly relevant to your current learning objectives.")

    if primary_importance == "core" and skill_gap_pts >= 30: parts.append(f"Core career skill with a {skill_gap_pts}-point gap to close.")
    elif primary_importance == "core" and skill_gap_pts > 0: parts.append("Core skill for your target role.")
    elif skill_gap_pts >= 40: parts.append(f"Significant {skill_gap_pts}-point gap in this skill area.")
    elif skill_gap_pts >= 20: parts.append(f"Notable {skill_gap_pts}-point gap to address.")
    elif skill_gap_pts == 0 and primary_importance == "core": parts.append("Reinforces a core skill you are actively developing.")
    else: parts.append("Relevant to your learning goals and target career.")

    if score_breakdown.get("preference_fit", 0) >= 0.85: parts.append("Matches your preferred learning format.")
    if score_breakdown.get("history_context", 1.0) <= 0.2: parts.append("You have already started this — continuing makes sense.")
    if score_breakdown.get("difficulty_fit", 0) >= 0.90: parts.append("Difficulty level is well-matched to where you are now.")
    if score_breakdown.get("readiness_mult", 1.0) < 0.8: parts.append("Some prerequisites still in progress — foundational material.")

    return " ".join(parts)


# ==============================================================================
# Core scoring function (Upgraded)
# ==============================================================================

def _score_resource(
    resource: dict,
    learner: dict,
    career_skill_map: dict,
    learner_prof_map: dict,
    learner_skill_status_map: dict,
    history_map: dict,
    prereq_map: dict,
) -> Optional[dict]:
    
    resource_id = resource.get("id", "")
    primary_skill_id = resource.get("primary_skill_id")
    skill_ids: List[str] = resource.get("skill_ids") or []
    if not isinstance(skill_ids, list): skill_ids = []

    history_ctx_score = _score_history_context(resource_id, history_map)
    if history_ctx_score < 0: return None  # Filter completed

    best_gap_score = 0.0
    target_skill_id = primary_skill_id
    target_skill_name = resource.get("primary_skill_name")

    for sid in skill_ids:
        if sid in career_skill_map:
            req  = career_skill_map[sid]["required_score"]
            prof = learner_prof_map.get(sid, 0)
            gs   = max(0, req - prof) / 100.0
            if gs > best_gap_score:
                best_gap_score = gs
                target_skill_id = sid

    if best_gap_score == 0.0 and primary_skill_id and primary_skill_id in career_skill_map:
        req  = career_skill_map[primary_skill_id]["required_score"]
        prof = learner_prof_map.get(primary_skill_id, 0)
        best_gap_score = max(0, req - prof) / 100.0

    primary_importance = career_skill_map.get(primary_skill_id or "", {}).get("importance", "")
    career_importance_score = 1.0 if primary_importance == "core" else (0.5 if primary_importance == "nice-to-have" else 0.2)
    difficulty_score = _score_difficulty_fit(resource.get("difficulty"), learner.get("current_level"))
    preference_score = _score_preference_fit(resource.get("type"), learner)
    duration_score = _score_duration_fit(resource.get("duration_text"), learner.get("preferred_session_length"))
    readiness_mult = _compute_readiness_multiplier(primary_skill_id, learner_skill_status_map, learner_prof_map, prereq_map)

    # NEW: Retrieve the semantic similarity score calculated by pgvector in the DB query
    semantic_score = float(resource.get("semantic_similarity", 0.5))

    raw_score = (
        WEIGHTS["semantic_relevance"] * semantic_score +
        WEIGHTS["skill_gap"]          * best_gap_score +
        WEIGHTS["career_importance"]  * career_importance_score +
        WEIGHTS["difficulty_fit"]     * difficulty_score +
        WEIGHTS["preference_fit"]     * preference_score +
        WEIGHTS["duration_fit"]       * duration_score +
        WEIGHTS["history_context"]    * history_ctx_score
    )
    final_score = min(1.0, max(0.0, raw_score * readiness_mult))

    breakdown: Dict[str, float] = {
        "semantic_relevance": round(semantic_score, 3),
        "skill_gap":          round(best_gap_score, 3),
        "career_importance":  round(career_importance_score, 3),
        "difficulty_fit":     round(difficulty_score, 3),
        "preference_fit":     round(preference_score, 3),
        "duration_fit":       round(duration_score, 3),
        "history_context":    round(history_ctx_score, 3),
        "readiness_mult":     round(readiness_mult, 3),
    }

    skill_gap_pts = max(0, career_skill_map[target_skill_id]["required_score"] - learner_prof_map.get(target_skill_id, 0)) if target_skill_id in career_skill_map else 0
    reasoning = _generate_reasoning(target_skill_name, skill_gap_pts, primary_importance, breakdown)

    return {
        "resource_id":       resource_id,
        "resource_title":    resource.get("title", ""),
        "resource_type":     resource.get("type", ""),
        "difficulty":        resource.get("difficulty"),
        "duration_text":     resource.get("duration_text"),
        "target_skill_id":   target_skill_id,
        "target_skill_name": target_skill_name,
        "score":             round(final_score, 4),
        "reasoning":         reasoning,
        "score_breakdown":   breakdown,
        "priority":          0,
    }


def _apply_diversity_pass(scored: List[dict]) -> List[dict]:
    type_counts: Dict[str, int] = {}
    for item in scored:
        rtype = item.get("resource_type", "")
        count = type_counts.get(rtype, 0)
        if count >= _DIVERSITY_TYPE_LIMIT:
            item["score"] = round(item["score"] * _DIVERSITY_PENALTY, 4)
        type_counts[rtype] = count + 1
    scored.sort(key=lambda x: x["score"], reverse=True)
    return scored


# ==============================================================================
# Main engine entry point (Upgraded)
# ==============================================================================

async def run_recommendation_engine(
    pool: asyncpg.Pool,
    learner_id: str,
    max_recommendations: int = 8,
    persist: bool = True,
) -> List[dict]:
    
    learner = await learner_repo.get_learner_by_id(pool, learner_id)
    if not learner: return []

    career_id = learner.get("target_career_id")
    career_skills_list = await skills_repo.get_career_skills(pool, career_id) if career_id else []
    career_skill_map = {cs["skill_id"]: cs for cs in career_skills_list}

    learner_skills_list = await skills_repo.get_learner_skills(pool, learner_id)
    learner_prof_map   = {ls["skill_id"]: ls["proficiency_score"] for ls in learner_skills_list}
    learner_status_map = {ls["skill_id"]: ls["status"] for ls in learner_skills_list}

    history_list = await learning_history_repo.get_learning_history(pool, learner_id)
    history_map  = {h["resource_id"]: h for h in history_list if h.get("resource_id")}

    all_prereq_rows = await skills_repo.get_all_skill_prerequisites(pool)
    prereq_map: Dict[str, List[str]] = {}
    for row in all_prereq_rows:
        prereq_map.setdefault(row["skill_id"], []).append(row["prerequisite_skill_id"])

    # ── NEW STEP: Identify largest skill gap to find target vector ──────────
    target_skill_id_for_vector = None
    largest_gap = -1
    for skill_id, req in career_skill_map.items():
        gap = req["required_score"] - learner_prof_map.get(skill_id, 0)
        if gap > largest_gap:
            largest_gap = gap
            target_skill_id_for_vector = skill_id

    # ── NEW STEP: Perform pgvector semantic search ──────────────────────────
    # Instead of fetching *all* resources, we use cosine distance (<=>) to find 
    # resources conceptually similar to the learner's most critical missing skill.
    candidate_resources = []
    async with pool.acquire() as conn:
        if target_skill_id_for_vector:
            # 1. Fetch the embedding of the skill the user needs most
            target_embedding_row = await conn.fetchrow(
                "SELECT embedding FROM skills WHERE id = $1", target_skill_id_for_vector
            )
            
            if target_embedding_row and target_embedding_row["embedding"]:
                # 2. Use pgvector to fetch top 30 most semantically similar resources.
                # '1 - (embedding <=> $1)' converts distance into a 0-1 similarity score.
                query = """
                    SELECT r.*, 
                           1 - (r.embedding <=> $1::vector) AS semantic_similarity
                    FROM resources r
                    ORDER BY r.embedding <=> $1::vector
                    LIMIT 30
                """
                candidate_resources = await conn.fetch(query, target_embedding_row["embedding"])
        
        # Fallback to standard fetch if no vectors are embedded yet
        if not candidate_resources:
            query = "SELECT r.*, 0.5 AS semantic_similarity FROM resources r"
            candidate_resources = await conn.fetch(query)

    # Convert asyncpg Record objects to dicts
    candidate_resources = [dict(r) for r in candidate_resources]

    # ── Score the vector-retrieved candidates ────────────────────────────────
    scored: List[dict] = []
    for resource in candidate_resources:
        result = _score_resource(
            resource=resource,
            learner=learner,
            career_skill_map=career_skill_map,
            learner_prof_map=learner_prof_map,
            learner_skill_status_map=learner_status_map,
            history_map=history_map,
            prereq_map=prereq_map,
        )
        if result is not None:
            scored.append(result)

    scored.sort(key=lambda x: x["score"], reverse=True)
    scored = _apply_diversity_pass(scored)

    top = scored[:max_recommendations]
    for i, item in enumerate(top, start=1):
        item["priority"] = i

    if persist and top:
        await recommendations_repo.deactivate_recommendations(pool, learner_id)
        recs_to_save = [{"resource_id": item["resource_id"], "score": item["score"], "reasoning": item["reasoning"]} for item in top]
        await recommendations_repo.save_recommendations(pool, learner_id, recs_to_save)

    return top