"""
app/services/recommendation_engine.py

Phase 3 — Personalized Recommendation Engine.

Algorithm: Multi-factor weighted ranking with readiness multiplier.

Pipeline:
  1. Load learner context (profile, career, skills, history, prerequisites)
  2. Score every resource candidate against 6 interpretable factors
  3. Filter completed resources; penalise in-progress resources
  4. Sort by final score descending
  5. Apply a light diversity pass (avoid all-same-type output)
  6. Assign priority ranks (1 = best)
  7. Persist batch to recommendations table
  8. Return structured list for the API response

Scoring factors and weights:
  skill_gap         0.28  — gap between learner proficiency and career requirement
  career_importance 0.22  — core vs nice-to-have skill classification
  difficulty_fit    0.15  — resource difficulty vs learner level
  preference_fit    0.15  — resource type vs learner's stated format preferences
  duration_fit      0.08  — resource duration vs preferred session length
  history_context   0.12  — penalty for in-progress / exclude completed

Plus a readiness_multiplier [0.5, 1.0] for one-hop prerequisite check.

Scope:
  This module does NOT implement:
    - Skill Graph traversal (Member 3)
    - LLM/explainability text (Member 1)
    - Auth (Phase 3 auth integration)
    - Learning Path ordering (Member 3)
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

# ── Weight configuration ───────────────────────────────────────────────────────
WEIGHTS: Dict[str, float] = {
    "skill_gap":          0.28,
    "career_importance":  0.22,
    "difficulty_fit":     0.15,
    "preference_fit":     0.15,
    "duration_fit":       0.08,
    "history_context":    0.12,
}

# ── Level scale used for difficulty matching ───────────────────────────────────
_LEVEL_ORDER: Dict[str, float] = {
    "Beginner":      1.0,
    "Intermediate":  2.0,
    "Advanced":      3.0,
    "Comprehensive": 3.5,
}

# ── Prerequisite proficiency threshold ────────────────────────────────────────
_PREREQ_MET_THRESHOLD = 50   # Proficiency score >= this → prerequisite is "met"

# ── Diversity: max same-type appearances before penalty applies ────────────────
_DIVERSITY_TYPE_LIMIT = 2    # 3rd+ occurrence of same type → −10% score
_DIVERSITY_PENALTY     = 0.90


# ==============================================================================
# Internal helper functions
# ==============================================================================

def _parse_learner_level(level_str: Optional[str]) -> float:
    """
    Parse a compound learner level string into a float on the _LEVEL_ORDER scale.

    Examples:
        "Beginner"               → 1.0
        "Intermediate"           → 2.0
        "Beginner-Intermediate"  → 1.5
        "Advanced"               → 3.0
        None / unknown           → 1.5  (safe Beginner-Intermediate default)
    """
    if not level_str:
        return 1.5
    parts = level_str.split("-")
    vals: List[float] = []
    for p in parts:
        p = p.strip()
        matched = False
        for key, val in _LEVEL_ORDER.items():
            if key.lower() in p.lower():
                vals.append(val)
                matched = True
                break
        if not matched:
            vals.append(1.5)
    return sum(vals) / len(vals) if vals else 1.5


def _score_difficulty_fit(resource_difficulty: Optional[str], learner_level: Optional[str]) -> float:
    """
    Score [0.3, 1.0] how well resource difficulty matches learner level.

    Slight positive stretch (diff ∈ (0, 0.5]) is rewarded because the seed
    learner preference is "Push me slightly beyond current level".

    diff = resource_level_num - learner_level_num
    """
    r_lvl = _LEVEL_ORDER.get(resource_difficulty or "Intermediate", 2.0)
    l_lvl = _parse_learner_level(learner_level)
    diff = r_lvl - l_lvl

    if diff == 0.0:
        return 1.00
    elif 0 < diff <= 0.5:
        return 0.95   # Very slight stretch — ideal
    elif 0 < diff <= 1.0:
        return 0.85   # One level up: beneficial
    elif 0 < diff <= 1.5:
        return 0.60   # Likely too hard
    elif diff > 1.5:
        return 0.30   # Way too hard
    elif -0.5 <= diff < 0:
        return 0.90   # Very slightly too easy — acceptable
    elif -1.0 <= diff < -0.5:
        return 0.75   # A bit easy
    elif -1.5 <= diff < -1.0:
        return 0.60   # Too easy
    else:
        return 0.45   # Way too easy


def _score_preference_fit(resource_type: Optional[str], learner: dict) -> float:
    """
    Score [0.45, 1.0] how well resource type matches learner's stated learning
    preferences (learning_style and learning_preferences.format).
    """
    rtype = (resource_type or "").lower()
    learning_style = (learner.get("learning_style") or "").lower()

    # Parse learning_preferences safely
    prefs = learner.get("learning_preferences") or {}
    if isinstance(prefs, str):
        try:
            prefs = json.loads(prefs)
        except Exception:
            prefs = {}
    formats = [f.lower() for f in (prefs.get("format") or [])]

    # Base score by resource type
    _BASE = {
        "project":       0.65,
        "course":        0.65,
        "practice":      0.55,
        "video":         0.55,
        "documentation": 0.50,
        "article":       0.45,
    }
    score = _BASE.get(rtype, 0.50)

    # Boost for "Project-based" learning style
    if "project" in learning_style:
        if rtype == "project":
            score = min(1.0, score + 0.30)
        elif rtype == "practice":
            score = min(1.0, score + 0.15)

    # Boost for short video primers in learning style
    if "video" in learning_style and rtype == "video":
        score = min(1.0, score + 0.20)

    # Boost from explicit format preferences
    _FORMAT_BOOSTS = {
        "interactive courses": ("course",),
        "hands-on projects":   ("project", "practice"),
        "short assessments":   ("practice",),
    }
    for pref_key, boosted_types in _FORMAT_BOOSTS.items():
        if pref_key in formats and rtype in boosted_types:
            score = min(1.0, score + 0.15)

    return round(score, 4)


_DURATION_RE = re.compile(r"(\d+)\s*(min|hr|wk|week)", re.IGNORECASE)


def _parse_duration_bucket(duration_text: Optional[str]) -> str:
    """
    Classify resource duration into: 'short' | 'medium' | 'multi-session'.

    short        : ≤ 30 min
    medium       : 31 min – 1 hr
    multi-session: multi-week (contains 'wk' / 'week')
    """
    if not duration_text:
        return "medium"
    m = _DURATION_RE.search(duration_text.lower())
    if not m:
        return "medium"
    val = int(m.group(1))
    unit = m.group(2).lower()

    if unit.startswith("wk") or unit.startswith("week"):
        return "multi-session"
    if unit == "hr":
        return "medium" if val <= 1 else "multi-session"
    # minutes
    if val <= 30:
        return "short"
    if val <= 60:
        return "medium"
    return "multi-session"


def _score_duration_fit(duration_text: Optional[str], preferred_session: Optional[str]) -> float:
    """
    Score [0.55, 1.0] how well resource duration matches preferred session length.
    """
    bucket = _parse_duration_bucket(duration_text)
    preferred = (preferred_session or "").lower()

    _TABLE = {
        # preferred_keyword → {bucket: score}
        "15": {"short": 1.00, "medium": 0.75, "multi-session": 0.55},
        "20": {"short": 1.00, "medium": 0.75, "multi-session": 0.55},
        "30": {"short": 0.85, "medium": 1.00, "multi-session": 0.75},
        "45": {"short": 0.85, "medium": 1.00, "multi-session": 0.75},
        "60": {"short": 0.70, "medium": 0.90, "multi-session": 1.00},
    }
    for keyword, scores in _TABLE.items():
        if keyword in preferred:
            return scores[bucket]

    # Unknown preference → neutral
    return {"short": 0.80, "medium": 0.90, "multi-session": 0.75}.get(bucket, 0.80)


def _score_history_context(resource_id: str, history_map: dict) -> float:
    """
    Score based on learning history:
      not started   → 1.0
      in-progress   → 0.15  (heavy penalty — already doing this)
      completed     → -1.0  (sentinel: caller must filter out)
    """
    hist = history_map.get(resource_id)
    if not hist:
        return 1.0
    status = hist.get("status", "not-started")
    if status == "completed":
        return -1.0   # Sentinel
    if status == "in-progress":
        return 0.15
    return 1.0


def _compute_readiness_multiplier(
    primary_skill_id: Optional[str],
    learner_skill_status_map: dict,
    learner_prof_map: dict,
    prereq_map: dict,
) -> float:
    """
    Readiness multiplier [0.5, 1.0].

    Rule 1 — Trust the adaptive engine:
      If the learner's status for this skill is 'current', 'adapted', or
      'recommended', the replanning engine has already decided this skill is
      appropriate for the learner now. Return 1.0 unconditionally.

    Rule 2 — One-hop prerequisite check (for other statuses):
      Check whether direct prerequisite skills have been sufficiently learned
      (proficiency >= PREREQ_MET_THRESHOLD). Return a multiplier based on the
      fraction of prerequisites met.

    This is NOT a full graph traversal.
    """
    if not primary_skill_id:
        return 1.0

    # Trust adaptive engine
    skill_status = learner_skill_status_map.get(primary_skill_id, "not-started")
    if skill_status in ("current", "adapted", "recommended"):
        return 1.0

    prereqs = prereq_map.get(primary_skill_id, [])
    if not prereqs:
        return 1.0

    met = sum(1 for p in prereqs if learner_prof_map.get(p, 0) >= _PREREQ_MET_THRESHOLD)
    ratio = met / len(prereqs)

    if ratio >= 1.0:
        return 1.00
    elif ratio >= 0.5:
        return 0.80
    else:
        return 0.50


def _generate_reasoning(
    target_skill_name: Optional[str],
    skill_gap_pts: int,
    primary_importance: str,
    score_breakdown: dict,
) -> str:
    """
    Produce a deterministic, human-readable reasoning string.
    Structured to be consumable by Member 1's Explainable AI module later.
    Does NOT call any LLM — purely rule-based.
    """
    parts: List[str] = []

    if primary_importance == "core" and skill_gap_pts >= 30:
        parts.append(f"Core career skill with a {skill_gap_pts}-point gap to close.")
    elif primary_importance == "core" and skill_gap_pts > 0:
        parts.append("Core skill for your target role.")
    elif skill_gap_pts >= 40:
        parts.append(f"Significant {skill_gap_pts}-point gap in this skill area.")
    elif skill_gap_pts >= 20:
        parts.append(f"Notable {skill_gap_pts}-point gap to address.")
    elif skill_gap_pts == 0 and primary_importance == "core":
        parts.append("Reinforces a core skill you are actively developing.")
    else:
        parts.append("Relevant to your learning goals and target career.")

    if score_breakdown.get("preference_fit", 0) >= 0.85:
        parts.append("Matches your preferred learning format.")

    if score_breakdown.get("history_context", 1.0) <= 0.2:
        parts.append("You have already started this — continuing makes sense.")

    if score_breakdown.get("difficulty_fit", 0) >= 0.90:
        parts.append("Difficulty level is well-matched to where you are now.")

    if score_breakdown.get("readiness_mult", 1.0) < 0.8:
        parts.append("Some prerequisites still in progress — foundational material.")

    return " ".join(parts)


# ==============================================================================
# Core scoring function
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
    """
    Score a single resource. Returns None if the resource should be excluded.

    Args:
        resource: Row dict from get_all_resources() — includes id, title, type,
                  difficulty, duration_text, primary_skill_id, skill_ids (list).
        learner: Row dict from get_learner_by_id().
        career_skill_map: {skill_id: {required_score, importance}} for the career.
        learner_prof_map: {skill_id: proficiency_score} for the learner.
        learner_skill_status_map: {skill_id: status} for the learner.
        history_map: {resource_id: {status, progress_pct}} for the learner.
        prereq_map: {skill_id: [prerequisite_skill_ids]} from skill_prerequisites.

    Returns:
        dict with scored recommendation metadata, or None if excluded.
    """
    resource_id = resource.get("id", "")
    primary_skill_id = resource.get("primary_skill_id")
    skill_ids: List[str] = resource.get("skill_ids") or []
    if not isinstance(skill_ids, list):
        skill_ids = []

    # ── Filter: exclude completed resources ────────────────────────────────────
    history_ctx_score = _score_history_context(resource_id, history_map)
    if history_ctx_score < 0:
        return None  # Sentinel: resource is completed → excluded

    # ── Factor 1: Best skill gap score across all skills resource teaches ──────
    # Use the highest gap among all skills this resource addresses as the signal.
    # This ensures multi-skill resources (e.g. a project covering React + State)
    # receive credit for the most impactful gap they close.
    best_gap_score = 0.0
    target_skill_id = primary_skill_id   # Will be overridden if a better match found
    target_skill_name = resource.get("primary_skill_name")

    for sid in skill_ids:
        if sid in career_skill_map:
            req  = career_skill_map[sid]["required_score"]
            prof = learner_prof_map.get(sid, 0)
            gap  = max(0, req - prof)
            gs   = gap / 100.0
            if gs > best_gap_score:
                best_gap_score = gs
                target_skill_id = sid
                # Note: name lookup from in-memory data limited to primary skill.
                # Other skill names resolved in the DB query if needed.

    # Edge case: primary skill in career but already satisfied
    if best_gap_score == 0.0 and primary_skill_id and primary_skill_id in career_skill_map:
        req  = career_skill_map[primary_skill_id]["required_score"]
        prof = learner_prof_map.get(primary_skill_id, 0)
        best_gap_score = max(0, req - prof) / 100.0

    # ── Factor 2: Career importance of primary skill ───────────────────────────
    # Importance is based on the primary (main subject) skill of the resource,
    # not the best-gap skill. A React course should get "core" importance even
    # if we score it based on a State Management gap.
    primary_importance = career_skill_map.get(primary_skill_id or "", {}).get("importance", "")
    if primary_importance == "core":
        career_importance_score = 1.0
    elif primary_importance == "nice-to-have":
        career_importance_score = 0.5
    else:
        career_importance_score = 0.2

    # ── Factor 3: Difficulty fit ───────────────────────────────────────────────
    difficulty_score = _score_difficulty_fit(
        resource.get("difficulty"), learner.get("current_level")
    )

    # ── Factor 4: Preference fit ───────────────────────────────────────────────
    preference_score = _score_preference_fit(resource.get("type"), learner)

    # ── Factor 5: Duration fit ─────────────────────────────────────────────────
    duration_score = _score_duration_fit(
        resource.get("duration_text"), learner.get("preferred_session_length")
    )

    # ── Prerequisite readiness multiplier ─────────────────────────────────────
    readiness_mult = _compute_readiness_multiplier(
        primary_skill_id,
        learner_skill_status_map,
        learner_prof_map,
        prereq_map,
    )

    # ── Weighted raw score ─────────────────────────────────────────────────────
    raw_score = (
        WEIGHTS["skill_gap"]         * best_gap_score +
        WEIGHTS["career_importance"]  * career_importance_score +
        WEIGHTS["difficulty_fit"]     * difficulty_score +
        WEIGHTS["preference_fit"]     * preference_score +
        WEIGHTS["duration_fit"]       * duration_score +
        WEIGHTS["history_context"]    * history_ctx_score
    )
    final_score = min(1.0, max(0.0, raw_score * readiness_mult))

    # ── Score breakdown (for Explainable AI / debugging) ──────────────────────
    breakdown: Dict[str, float] = {
        "skill_gap":          round(best_gap_score, 3),
        "career_importance":  round(career_importance_score, 3),
        "difficulty_fit":     round(difficulty_score, 3),
        "preference_fit":     round(preference_score, 3),
        "duration_fit":       round(duration_score, 3),
        "history_context":    round(history_ctx_score, 3),
        "readiness_mult":     round(readiness_mult, 3),
    }

    # ── Reasoning text ─────────────────────────────────────────────────────────
    skill_gap_pts = 0
    if target_skill_id and target_skill_id in career_skill_map:
        req = career_skill_map[target_skill_id]["required_score"]
        prof = learner_prof_map.get(target_skill_id, 0)
        skill_gap_pts = max(0, req - prof)

    reasoning = _generate_reasoning(
        target_skill_name=target_skill_name,
        skill_gap_pts=skill_gap_pts,
        primary_importance=primary_importance,
        score_breakdown=breakdown,
    )

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
        "priority":          0,   # Assigned after ranking
    }


def _apply_diversity_pass(scored: List[dict]) -> List[dict]:
    """
    Light diversity adjustment: once a resource type appears ≥ DIVERSITY_TYPE_LIMIT
    times, subsequent resources of that type receive a DIVERSITY_PENALTY multiplier.

    The list is re-sorted after adjustment so the priority ranks remain meaningful.
    Relevance is always more important than diversity.
    """
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
# Main engine entry point
# ==============================================================================

async def run_recommendation_engine(
    pool: asyncpg.Pool,
    learner_id: str,
    max_recommendations: int = 8,
    persist: bool = True,
) -> List[dict]:
    """
    Run the full recommendation pipeline for a learner.

    Args:
        pool: Active asyncpg connection pool.
        learner_id: ID of the learner to generate recommendations for.
        max_recommendations: Maximum recommendations to return (default: 8).
        persist: If True, deactivate old recommendations and save new batch to DB.
                 Set to False in unit tests that don't want DB side effects.

    Returns:
        List of scored recommendation dicts, ordered by score descending.
        Each dict has: resource_id, resource_title, resource_type, target_skill_id,
        target_skill_name, score, reasoning, score_breakdown, priority, difficulty,
        duration_text.
    """
    # ── Step 1: Load learner profile ──────────────────────────────────────────
    learner = await learner_repo.get_learner_by_id(pool, learner_id)
    if not learner:
        return []

    # ── Step 2: Load career requirements ──────────────────────────────────────
    career_id = learner.get("target_career_id")
    career_skills_list = []
    if career_id:
        career_skills_list = await skills_repo.get_career_skills(pool, career_id)
    career_skill_map = {cs["skill_id"]: cs for cs in career_skills_list}

    # ── Step 3: Load learner skills ───────────────────────────────────────────
    learner_skills_list = await skills_repo.get_learner_skills(pool, learner_id)
    learner_prof_map   = {ls["skill_id"]: ls["proficiency_score"] for ls in learner_skills_list}
    learner_status_map = {ls["skill_id"]: ls["status"]            for ls in learner_skills_list}

    # ── Step 4: Load all candidate resources ──────────────────────────────────
    # No pre-filtering: scoring is the filter.
    all_resources = await resources_repo.get_all_resources(pool)

    # ── Step 5: Load learning history ─────────────────────────────────────────
    history_list = await learning_history_repo.get_learning_history(pool, learner_id)
    history_map  = {
        h["resource_id"]: h
        for h in history_list
        if h.get("resource_id")
    }

    # ── Step 6: Load skill prerequisites (one-hop readiness check) ────────────
    all_prereq_rows = await skills_repo.get_all_skill_prerequisites(pool)
    prereq_map: Dict[str, List[str]] = {}
    for row in all_prereq_rows:
        prereq_map.setdefault(row["skill_id"], []).append(row["prerequisite_skill_id"])

    # ── Step 7: Score every candidate ────────────────────────────────────────
    scored: List[dict] = []
    for resource in all_resources:
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

    # ── Step 8: Sort by score descending ─────────────────────────────────────
    scored.sort(key=lambda x: x["score"], reverse=True)

    # ── Step 9: Diversity pass ────────────────────────────────────────────────
    scored = _apply_diversity_pass(scored)

    # ── Step 10: Trim and assign priority ranks ───────────────────────────────
    top = scored[:max_recommendations]
    for i, item in enumerate(top, start=1):
        item["priority"] = i

    # ── Step 11: Persist to DB ────────────────────────────────────────────────
    if persist and top:
        await recommendations_repo.deactivate_recommendations(pool, learner_id)
        recs_to_save = [
            {
                "resource_id": item["resource_id"],
                "score":       item["score"],
                "reasoning":   item["reasoning"],
            }
            for item in top
        ]
        await recommendations_repo.save_recommendations(pool, learner_id, recs_to_save)

    return top
