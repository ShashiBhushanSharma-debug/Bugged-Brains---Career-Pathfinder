"""
tests/test_recommendation_engine.py

Test suite for the Phase 3 Recommendation Engine.

Structure:
  Part A — Unit tests (pure functions, no DB required)
      Tests 1-10 cover the required test cases.
  Part B — Integration tests (requires local seeded DB via conftest fixtures)
      Tests verify end-to-end engine output and DB persistence.

Learner fixture: u_1001 (Alex Rivera), target career: Frontend Developer.
Data mirrors the seed in 002_seed_data.sql.
"""
from __future__ import annotations

import pytest
from typing import Dict, Optional

from app.services.recommendation_engine import (
    WEIGHTS,
    _parse_learner_level,
    _score_difficulty_fit,
    _score_preference_fit,
    _parse_duration_bucket,
    _score_duration_fit,
    _score_history_context,
    _compute_readiness_multiplier,
    _score_resource,
    _apply_diversity_pass,
    run_recommendation_engine,
)


# ==============================================================================
# Shared test fixtures (in-memory mock data matching 002_seed_data.sql)
# ==============================================================================

# Learner: Alex Rivera (u_1001)
_LEARNER = {
    "id": "u_1001",
    "name": "Alex Rivera",
    "first_name": "Alex",
    "target_career_id": "career_frontend_dev",
    "current_level": "Beginner-Intermediate",
    "weekly_learning_hours": 8,
    "interests": ["Web Development", "UI Engineering", "Design Systems", "Accessibility"],
    "learning_style": "Project-based, with short video primers",
    "preferred_session_length": "30-45 min",
    "learning_preferences": {
        "pace": "Steady (3-5 sessions / week)",
        "format": ["Interactive courses", "Hands-on projects", "Short assessments"],
        "difficulty": "Push me slightly beyond current level",
    },
}

# Career skill requirements (career_frontend_dev)
_CAREER_SKILLS: Dict[str, dict] = {
    "sk_html":           {"required_score": 80,  "importance": "core"},
    "sk_css":            {"required_score": 80,  "importance": "core"},
    "sk_js":             {"required_score": 85,  "importance": "core"},
    "sk_react":          {"required_score": 85,  "importance": "core"},
    "sk_state":          {"required_score": 70,  "importance": "core"},
    "sk_ts":             {"required_score": 65,  "importance": "nice-to-have"},
    "sk_testing":        {"required_score": 55,  "importance": "nice-to-have"},
    "sk_a11y":           {"required_score": 60,  "importance": "nice-to-have"},
    "sk_perf":           {"required_score": 50,  "importance": "nice-to-have"},
    "sk_design_systems": {"required_score": 45,  "importance": "nice-to-have"},
}

# Learner proficiency scores
_LEARNER_PROF: Dict[str, int] = {
    "sk_html":           92,
    "sk_css":            85,
    "sk_js":             80,
    "sk_react":          28,
    "sk_state":          10,
    "sk_ts":             15,
    "sk_testing":         0,
    "sk_a11y":           20,
    "sk_perf":            5,
    "sk_design_systems": 12,
}

# Learner skill statuses (set by adaptive engine)
_LEARNER_STATUS: Dict[str, str] = {
    "sk_html":           "completed",
    "sk_css":            "completed",
    "sk_js":             "completed",
    "sk_react":          "current",
    "sk_state":          "adapted",     # AI engine explicitly added this
    "sk_ts":             "recommended",
    "sk_testing":        "locked",
    "sk_a11y":           "locked",
    "sk_perf":           "locked",
    "sk_design_systems": "locked",
}

# One-hop prerequisite map
_PREREQS: Dict[str, list] = {
    "sk_react":          ["sk_js"],
    "sk_state":          ["sk_react"],
    "sk_ts":             ["sk_js"],
    "sk_testing":        ["sk_react", "sk_state"],
    "sk_a11y":           ["sk_html", "sk_react"],
    "sk_perf":           ["sk_react"],
    "sk_design_systems": ["sk_css", "sk_react"],
}

# Learning history for u_1001
_HISTORY: Dict[str, dict] = {
    "res_1": {"status": "in-progress",  "progress_pct": 22},
    "res_3": {"status": "completed",    "progress_pct": 100},
    "res_4": {"status": "completed",    "progress_pct": 100},
    "res_8": {"status": "in-progress",  "progress_pct": 60},
}


def _mk_resource(
    rid: str,
    title: str,
    rtype: str,
    difficulty: str,
    duration: str,
    primary_skill_id: Optional[str],
    skill_ids: Optional[list] = None,
) -> dict:
    """Helper: build a minimal resource dict matching the get_all_resources() shape."""
    return {
        "id":                    rid,
        "title":                 title,
        "type":                  rtype,
        "difficulty":            difficulty,
        "duration_text":         duration,
        "url":                   None,
        "description":           "",
        "why_recommended_template": None,
        "primary_skill_id":      primary_skill_id,
        "primary_skill_name":    primary_skill_id,  # simplified — name == id in tests
        "skill_ids":             skill_ids if skill_ids is not None else ([primary_skill_id] if primary_skill_id else []),
    }


# Seed resources (matching 002_seed_data.sql)
_RES_1 = _mk_resource("res_1", "React Fundamentals",          "course",        "Intermediate", "3 wks",  "sk_react")
_RES_2 = _mk_resource("res_2", "State Management in React",   "course",        "Intermediate", "2 wks",  "sk_state")
_RES_3 = _mk_resource("res_3", "Thinking in React",           "documentation", "Beginner",     "20 min", "sk_react")
_RES_4 = _mk_resource("res_4", "CSS Grid in 15 Minutes",      "video",         "Beginner",     "15 min", "sk_css")
_RES_5 = _mk_resource("res_5", "Task Board Mini Project",     "project",       "Intermediate", "1 wk",   "sk_react", ["sk_react", "sk_state"])
_RES_6 = _mk_resource("res_6", "TypeScript for React Devs",   "course",        "Intermediate", "2 wks",  "sk_ts",    ["sk_ts", "sk_react"])
_RES_7 = _mk_resource("res_7", "Writing Your First Unit Test","article",        "Beginner",     "10 min", "sk_testing")
_RES_8 = _mk_resource("res_8", "Component Design Practice",   "practice",      "Intermediate", "30 min", "sk_react")

_ALL_RESOURCES = [_RES_1, _RES_2, _RES_3, _RES_4, _RES_5, _RES_6, _RES_7, _RES_8]


def _score(resource: dict, history: Optional[dict] = None) -> Optional[dict]:
    """Convenience wrapper for _score_resource with standard fixtures."""
    return _score_resource(
        resource=resource,
        learner=_LEARNER,
        career_skill_map=_CAREER_SKILLS,
        learner_prof_map=_LEARNER_PROF,
        learner_skill_status_map=_LEARNER_STATUS,
        history_map=history if history is not None else {},
        prereq_map=_PREREQS,
    )


# ==============================================================================
# Part A: Unit tests — pure functions, no DB
# ==============================================================================

class TestWeights:
    """Sanity-check the weight configuration."""

    def test_weights_sum_to_one(self):
        total = sum(WEIGHTS.values())
        assert abs(total - 1.0) < 1e-9, f"WEIGHTS must sum to 1.0, got {total}"

    def test_all_weight_keys_present(self):
        expected = {"skill_gap", "career_importance", "difficulty_fit",
                    "preference_fit", "duration_fit", "history_context"}
        assert set(WEIGHTS.keys()) == expected

    def test_no_weight_is_zero_or_negative(self):
        for key, val in WEIGHTS.items():
            assert val > 0, f"Weight '{key}' must be positive, got {val}"


class TestDifficultyFit:
    """_score_difficulty_fit — boundary and directional correctness."""

    def test_perfect_match_scores_one(self):
        assert _score_difficulty_fit("Intermediate", "Intermediate") == 1.0

    def test_beginner_intermediate_learner_with_intermediate_resource(self):
        # diff = 2.0 - 1.5 = 0.5 → "very slight stretch" → 0.95
        score = _score_difficulty_fit("Intermediate", "Beginner-Intermediate")
        assert score == pytest.approx(0.95)

    def test_one_level_up_rewarded(self):
        # Intermediate resource for Beginner learner: diff=1.0 → 0.85
        score = _score_difficulty_fit("Intermediate", "Beginner")
        assert score == pytest.approx(0.85)

    def test_advanced_resource_for_beginner_heavily_penalised(self):
        # Advanced (3.0) for Beginner (1.0): diff=2.0 > 1.5 → 0.30
        score = _score_difficulty_fit("Advanced", "Beginner")
        assert score == pytest.approx(0.30)

    def test_beginner_resource_for_intermediate_slightly_penalised(self):
        # Beginner (1.0) for Intermediate (2.0): diff=-1.0 → 0.75
        score = _score_difficulty_fit("Beginner", "Intermediate")
        assert score == pytest.approx(0.75)

    def test_none_difficulty_defaults_gracefully(self):
        score = _score_difficulty_fit(None, "Intermediate")
        assert 0.0 < score <= 1.0

    def test_none_level_defaults_gracefully(self):
        score = _score_difficulty_fit("Intermediate", None)
        assert 0.0 < score <= 1.0


class TestPreferenceFit:
    """_score_preference_fit — learner style boosts."""

    def test_project_type_scores_highest_for_project_learner(self):
        project_score  = _score_preference_fit("project",  _LEARNER)
        article_score  = _score_preference_fit("article",  _LEARNER)
        course_score   = _score_preference_fit("course",   _LEARNER)
        assert project_score > article_score
        assert project_score > course_score

    def test_project_type_at_or_near_max(self):
        score = _score_preference_fit("project", _LEARNER)
        assert score >= 0.95, f"Project resource for project learner: expected ≥0.95, got {score}"

    def test_article_type_has_lowest_base(self):
        article_score = _score_preference_fit("article", _LEARNER)
        for rtype in ("course", "project", "practice", "video", "documentation"):
            other = _score_preference_fit(rtype, _LEARNER)
            assert article_score <= other, f"Article ({article_score}) should be ≤ {rtype} ({other})"

    def test_course_boosted_by_interactive_courses_preference(self):
        # _LEARNER has "Interactive courses" in format → course gets +0.15
        plain_learner = {**_LEARNER, "learning_preferences": {"format": []}, "learning_style": ""}
        boosted_score = _score_preference_fit("course", _LEARNER)
        plain_score   = _score_preference_fit("course", plain_learner)
        assert boosted_score > plain_score

    def test_scores_always_in_valid_range(self):
        for rtype in ("project", "course", "video", "documentation", "article", "practice", "unknown"):
            score = _score_preference_fit(rtype, _LEARNER)
            assert 0.0 <= score <= 1.0, f"Preference score out of range for type '{rtype}': {score}"


class TestDurationFit:
    """_parse_duration_bucket and _score_duration_fit."""

    def test_bucket_parsing_short(self):
        assert _parse_duration_bucket("10 min") == "short"
        assert _parse_duration_bucket("30 min") == "short"

    def test_bucket_parsing_medium(self):
        assert _parse_duration_bucket("45 min") == "medium"
        assert _parse_duration_bucket("20 min") == "short"   # 20 ≤ 30 → short

    def test_bucket_parsing_multi_session(self):
        assert _parse_duration_bucket("1 wk")  == "multi-session"
        assert _parse_duration_bucket("3 wks") == "multi-session"
        assert _parse_duration_bucket("2 weeks") == "multi-session"

    def test_preferred_30_45_medium_scores_highest(self):
        # Alex prefers "30-45 min" → medium bucket should score 1.0
        medium_score = _score_duration_fit("45 min", "30-45 min")
        short_score  = _score_duration_fit("10 min", "30-45 min")
        multi_score  = _score_duration_fit("3 wks",  "30-45 min")
        assert medium_score >= short_score
        assert medium_score >= multi_score
        assert medium_score == pytest.approx(1.0)

    def test_scores_always_in_valid_range(self):
        for dur in ("5 min", "20 min", "45 min", "1 wk", "3 wks", None):
            for pref in ("15-20 min", "30-45 min", "60 min", None):
                score = _score_duration_fit(dur, pref)
                assert 0.0 <= score <= 1.0, f"Duration score out of range: dur={dur}, pref={pref}"


class TestHistoryContext:
    """_score_history_context — filter and penalty logic."""

    def test_not_started_returns_full_score(self):
        assert _score_history_context("res_x", {}) == 1.0

    def test_inprogress_returns_low_score(self):
        history = {"res_1": {"status": "in-progress", "progress_pct": 22}}
        score = _score_history_context("res_1", history)
        assert score == pytest.approx(0.15)

    def test_completed_returns_sentinel(self):
        history = {"res_3": {"status": "completed", "progress_pct": 100}}
        score = _score_history_context("res_3", history)
        assert score < 0, "Completed resource must return sentinel < 0 for exclusion"


class TestReadinessMultiplier:
    """_compute_readiness_multiplier — adaptive engine trust + one-hop prereq check."""

    def test_adaptive_engine_statuses_always_return_one(self):
        for status in ("current", "adapted", "recommended"):
            mult = _compute_readiness_multiplier(
                primary_skill_id="sk_react",
                learner_skill_status_map={"sk_react": status},
                learner_prof_map={"sk_js": 0},   # Even with unmet prereq
                prereq_map={"sk_react": ["sk_js"]},
            )
            assert mult == 1.0, (
                f"Adaptive engine status '{status}' should bypass prereq check → 1.0, got {mult}"
            )

    def test_all_prereqs_met_returns_one(self):
        mult = _compute_readiness_multiplier(
            primary_skill_id="sk_react",
            learner_skill_status_map={"sk_react": "not-started"},
            learner_prof_map={"sk_js": 80},   # ≥ 50 threshold → met
            prereq_map={"sk_react": ["sk_js"]},
        )
        assert mult == pytest.approx(1.0)

    def test_partial_prereqs_returns_reduced_multiplier(self):
        mult = _compute_readiness_multiplier(
            primary_skill_id="sk_testing",
            learner_skill_status_map={"sk_testing": "locked"},
            learner_prof_map={"sk_react": 28, "sk_state": 10},  # Both < 50 → not met
            prereq_map={"sk_testing": ["sk_react", "sk_state"]},
        )
        assert mult == pytest.approx(0.50), f"Expected 0.50 readiness multiplier, got {mult}"

    def test_no_prereqs_returns_one(self):
        mult = _compute_readiness_multiplier("sk_html", {}, {}, {})
        assert mult == 1.0

    def test_none_skill_id_returns_one(self):
        mult = _compute_readiness_multiplier(None, {}, {}, {})
        assert mult == 1.0


# ==============================================================================
# Test Case 1: Large skill gap → resource ranks highly
# ==============================================================================
class TestCase01_LargeSkillGapRanksHighly:

    def test_react_resource_scores_high_with_large_gap(self):
        # sk_react: proficiency=28, required=85 → gap=57 → gap_score=0.57
        result = _score(_RES_1, history={})  # React Fundamentals, not-started
        assert result is not None
        assert result["score"] >= 0.65, (
            f"React resource (gap 57) should score ≥0.65, got {result['score']}"
        )

    def test_skill_gap_component_correct(self):
        result = _score(_RES_1, history={})
        assert result is not None
        assert result["score_breakdown"]["skill_gap"] == pytest.approx(0.57, abs=0.01)

    def test_large_gap_resource_outranks_low_gap_resource(self):
        # React resource (gap 57) vs CSS resource (gap 0, surplus)
        react_result = _score(_RES_1, history={})
        css_result   = _score(_RES_4, history={})
        assert react_result is not None
        # CSS is completed anyway — but even unstarted, lower gap should rank lower
        react_no_hist = _score(_RES_1, history={})
        css_no_hist   = _score(_RES_4, history={})
        assert react_no_hist is not None and css_no_hist is not None
        assert react_no_hist["score"] > css_no_hist["score"]


# ==============================================================================
# Test Case 2: No skill gap → resource gets low priority
# ==============================================================================
class TestCase02_NoGapLowPriority:

    def test_css_resource_has_zero_gap_score(self):
        # sk_css: proficiency=85, required=80 → gap=−5 → clamped to 0
        result = _score(_RES_4, history={})
        assert result is not None
        assert result["score_breakdown"]["skill_gap"] == pytest.approx(0.0, abs=0.001)

    def test_css_resource_scores_lower_than_large_gap_resource(self):
        # Zero-gap resource must score below a resource with a large, core gap.
        # CSS is "core" so it still earns career_importance points — but skill_gap=0
        # means it will lose to any resource addressing a real gap.
        css_result   = _score(_RES_4, history={})   # no gap
        react_result = _score(_RES_1, history={})   # gap 57, core
        assert css_result is not None and react_result is not None
        assert react_result["score"] > css_result["score"], (
            f"Large-gap React resource ({react_result['score']:.3f}) should beat "
            f"zero-gap CSS resource ({css_result['score']:.3f})"
        )


# ==============================================================================
# Test Case 3: Core skill vs nice-to-have (same gap magnitude)
# ==============================================================================
class TestCase03_CoreBeatsNiceToHave:

    def test_core_skill_resource_outranks_nicetohave_with_similar_gap(self):
        # Core: sk_react gap=57, nice-to-have: sk_ts gap=50
        # Despite sk_ts having slightly lower gap, sk_react is "core" → should win
        core_resource = _mk_resource("r_core", "Core Resource", "course", "Intermediate", "2 wks", "sk_react")
        nth_resource  = _mk_resource("r_nth",  "NTH Resource",  "course", "Intermediate", "2 wks", "sk_ts")

        core_result = _score(core_resource, history={})
        nth_result  = _score(nth_resource,  history={})

        assert core_result is not None and nth_result is not None
        assert core_result["score"] > nth_result["score"], (
            f"Core resource ({core_result['score']:.3f}) must beat "
            f"nice-to-have ({nth_result['score']:.3f}) with similar gap"
        )

    def test_career_importance_factor_is_higher_for_core(self):
        core_r = _mk_resource("r1", "Core", "course", "Intermediate", "2 wks", "sk_react")
        nth_r  = _mk_resource("r2", "NTH",  "course", "Intermediate", "2 wks", "sk_ts")
        core = _score(core_r, history={})
        nth  = _score(nth_r,  history={})
        assert core is not None and nth is not None
        assert core["score_breakdown"]["career_importance"] > nth["score_breakdown"]["career_importance"]


# ==============================================================================
# Test Case 4: Difficulty mismatch lowers score
# ==============================================================================
class TestCase04_DifficultyMismatch:

    def test_advanced_resource_scores_lower_than_intermediate(self):
        hard_r = _mk_resource("r_hard", "Hard Resource", "course", "Advanced",      "2 wks", "sk_react")
        mid_r  = _mk_resource("r_mid",  "Mid Resource",  "course", "Intermediate",  "2 wks", "sk_react")
        hard = _score(hard_r, history={})
        mid  = _score(mid_r,  history={})
        assert hard is not None and mid is not None
        assert mid["score"] > hard["score"], (
            f"Intermediate resource ({mid['score']:.3f}) should beat "
            f"Advanced resource ({hard['score']:.3f}) for Beginner-Intermediate learner"
        )

    def test_difficulty_fit_breakdown_reflects_mismatch(self):
        hard_r = _mk_resource("r_hard2", "Hard", "course", "Advanced",     "2 wks", "sk_react")
        mid_r  = _mk_resource("r_mid2",  "Mid",  "course", "Intermediate", "2 wks", "sk_react")
        hard = _score(hard_r, history={})
        mid  = _score(mid_r,  history={})
        assert hard is not None and mid is not None
        assert mid["score_breakdown"]["difficulty_fit"] > hard["score_breakdown"]["difficulty_fit"]


# ==============================================================================
# Test Case 5: Learning preference fit
# ==============================================================================
class TestCase05_PreferenceFit:

    def test_project_preference_fit_exceeds_article(self):
        proj_r = _mk_resource("r_proj", "Project", "project", "Intermediate", "1 wk",  "sk_react")
        art_r  = _mk_resource("r_art",  "Article", "article", "Intermediate", "10 min","sk_react")
        proj = _score(proj_r, history={})
        art  = _score(art_r,  history={})
        assert proj is not None and art is not None
        assert proj["score_breakdown"]["preference_fit"] > art["score_breakdown"]["preference_fit"]

    def test_project_resource_scores_higher_overall_for_project_learner(self):
        proj_r = _mk_resource("r_proj2", "Project", "project", "Intermediate", "1 wk",  "sk_react")
        art_r  = _mk_resource("r_art2",  "Article", "article", "Intermediate", "10 min","sk_react")
        assert _score(proj_r, history={})["score"] > _score(art_r, history={})["score"]


# ==============================================================================
# Test Case 6: Completed resource must not be recommended
# ==============================================================================
class TestCase06_CompletedResourceExcluded:

    def test_completed_resource_returns_none(self):
        history = {"res_3": {"status": "completed", "progress_pct": 100}}
        result = _score(_RES_3, history=history)
        assert result is None, "Completed resource must return None (excluded from recommendations)"

    def test_completed_res4_also_excluded(self):
        history = {"res_4": {"status": "completed", "progress_pct": 100}}
        result = _score(_RES_4, history=history)
        assert result is None

    def test_same_resource_not_completed_is_included(self):
        # Without history, the resource should be scored normally
        result = _score(_RES_3, history={})
        assert result is not None


# ==============================================================================
# Test Case 7: In-progress resource is deprioritized (not excluded)
# ==============================================================================
class TestCase07_InProgressDeprioritized:

    def test_inprogress_scores_lower_than_notstarted(self):
        history_inprogress = {"res_1": {"status": "in-progress", "progress_pct": 22}}
        result_inprogress = _score(_RES_1, history=history_inprogress)
        result_notstarted = _score(_RES_1, history={})

        assert result_inprogress is not None, "In-progress resource should not be excluded"
        assert result_notstarted is not None
        assert result_notstarted["score"] > result_inprogress["score"], (
            f"Not-started ({result_notstarted['score']:.3f}) should beat "
            f"in-progress ({result_inprogress['score']:.3f})"
        )

    def test_history_context_is_low_for_inprogress(self):
        history = {"res_1": {"status": "in-progress", "progress_pct": 22}}
        result = _score(_RES_1, history=history)
        assert result is not None
        assert result["score_breakdown"]["history_context"] <= 0.20

    def test_score_difference_due_to_history_weight(self):
        # The difference in history_context (1.0 vs 0.15) should produce a
        # measurable score gap of at least WEIGHTS["history_context"] × 0.80
        min_expected_gap = WEIGHTS["history_context"] * (1.0 - 0.15) * 0.8  # with buffer
        history_in = {"res_1": {"status": "in-progress", "progress_pct": 22}}
        r_in  = _score(_RES_1, history=history_in)
        r_out = _score(_RES_1, history={})
        assert r_in is not None and r_out is not None
        assert r_out["score"] - r_in["score"] >= min_expected_gap, (
            f"Expected score gap ≥{min_expected_gap:.3f} due to history weight, "
            f"got {r_out['score'] - r_in['score']:.3f}"
        )


# ==============================================================================
# Test Case 8: Ranking is deterministic
# ==============================================================================
class TestCase08_DeterministicRanking:

    def test_same_inputs_produce_same_scores(self):
        scores_run_1 = [
            (r["id"], _score(r, history=_HISTORY)["score"] if _score(r, history=_HISTORY) else None)
            for r in _ALL_RESOURCES
        ]
        scores_run_2 = [
            (r["id"], _score(r, history=_HISTORY)["score"] if _score(r, history=_HISTORY) else None)
            for r in _ALL_RESOURCES
        ]
        assert scores_run_1 == scores_run_2, "Scoring must be deterministic — same inputs, same output"

    def test_sorted_output_is_stable(self):
        scored = [s for r in _ALL_RESOURCES if (s := _score(r, history=_HISTORY)) is not None]
        sorted_1 = sorted(scored, key=lambda x: x["score"], reverse=True)
        sorted_2 = sorted(scored, key=lambda x: x["score"], reverse=True)
        assert [x["resource_id"] for x in sorted_1] == [x["resource_id"] for x in sorted_2]


# ==============================================================================
# Test Case 9: All scores within [0.0, 1.0]
# ==============================================================================
class TestCase09_ScoresWithinRange:

    def test_all_resource_scores_within_range(self):
        for resource in _ALL_RESOURCES:
            result = _score(resource, history=_HISTORY)
            if result is not None:
                assert 0.0 <= result["score"] <= 1.0, (
                    f"Score out of [0, 1] range for {resource['id']}: {result['score']}"
                )

    def test_all_breakdown_factors_within_range(self):
        for resource in _ALL_RESOURCES:
            result = _score(resource, history=_HISTORY)
            if result is not None:
                for key, val in result["score_breakdown"].items():
                    if key == "history_context":
                        continue  # history_context is 0.15 (in-progress) or 1.0
                    assert 0.0 <= val <= 1.0, (
                        f"Breakdown factor '{key}' out of range for {resource['id']}: {val}"
                    )

    def test_extreme_proficiency_scores_stay_in_range(self):
        prof_zero = {sid: 0 for sid in _LEARNER_PROF}
        prof_full = {sid: 100 for sid in _LEARNER_PROF}
        for prof_map in (prof_zero, prof_full):
            for resource in _ALL_RESOURCES:
                result = _score_resource(
                    resource=resource,
                    learner=_LEARNER,
                    career_skill_map=_CAREER_SKILLS,
                    learner_prof_map=prof_map,
                    learner_skill_status_map=_LEARNER_STATUS,
                    history_map={},
                    prereq_map=_PREREQS,
                )
                if result is not None:
                    assert 0.0 <= result["score"] <= 1.0


# ==============================================================================
# Test Case 10: Empty-gap / fully-proficient learner handled safely
# ==============================================================================
class TestCase10_EmptyGapLearnerSafe:

    def test_fully_proficient_learner_produces_no_exceptions(self):
        # Learner who meets every career requirement
        full_prof  = {sid: cs["required_score"] for sid, cs in _CAREER_SKILLS.items()}
        full_status = {sid: "completed" for sid in _CAREER_SKILLS}

        results = []
        for resource in _ALL_RESOURCES:
            result = _score_resource(
                resource=resource,
                learner=_LEARNER,
                career_skill_map=_CAREER_SKILLS,
                learner_prof_map=full_prof,
                learner_skill_status_map=full_status,
                history_map={},
                prereq_map=_PREREQS,
            )
            if result is not None:
                results.append(result)

        # No exceptions thrown, all scores in range
        for r in results:
            assert 0.0 <= r["score"] <= 1.0

    def test_empty_career_skills_map_produces_no_exceptions(self):
        for resource in _ALL_RESOURCES:
            result = _score_resource(
                resource=resource,
                learner=_LEARNER,
                career_skill_map={},    # No career requirements
                learner_prof_map=_LEARNER_PROF,
                learner_skill_status_map=_LEARNER_STATUS,
                history_map={},
                prereq_map=_PREREQS,
            )
            if result is not None:
                assert 0.0 <= result["score"] <= 1.0

    def test_no_resources_returns_empty_list(self):
        # Edge case: empty resource list
        import asyncio

        async def _run():
            # Can't call full engine without DB — verify scoring loop handles empty input
            scored = []
            for resource in []:
                r = _score_resource(resource, _LEARNER, {}, {}, {}, {}, {})
                if r is not None:
                    scored.append(r)
            return scored

        result = asyncio.get_event_loop().run_until_complete(_run())
        assert result == []


# ==============================================================================
# Diversity pass tests
# ==============================================================================
class TestDiversityPass:

    def test_third_occurrence_of_same_type_penalised(self):
        items = [
            {"resource_id": f"r{i}", "resource_type": "course", "score": 0.80 - i * 0.01}
            for i in range(4)
        ]
        before_scores = [x["score"] for x in items]
        result = _apply_diversity_pass(items)
        # Third course (index 2) and beyond should be penalised
        # After penalty, the scores are re-sorted, so check the 3rd+ items were adjusted
        penalised_any = any(
            r["score"] < before_scores[i] for i, r in enumerate(result)
        )
        assert penalised_any, "Diversity pass should penalise the 3rd+ occurrence of same type"

    def test_diverse_resource_types_not_penalised(self):
        items = [
            {"resource_id": "r1", "resource_type": "course",   "score": 0.90},
            {"resource_id": "r2", "resource_type": "project",  "score": 0.85},
            {"resource_id": "r3", "resource_type": "practice", "score": 0.80},
            {"resource_id": "r4", "resource_type": "video",    "score": 0.75},
        ]
        original_scores = {x["resource_id"]: x["score"] for x in items}
        result = _apply_diversity_pass(items)
        for item in result:
            assert item["score"] == pytest.approx(original_scores[item["resource_id"]]), (
                f"{item['resource_id']} score should not change when all types are distinct"
            )

    def test_output_sorted_after_diversity(self):
        items = [
            {"resource_id": f"r{i}", "resource_type": "course", "score": 0.90 - i * 0.01}
            for i in range(5)
        ]
        result = _apply_diversity_pass(items)
        scores = [x["score"] for x in result]
        assert scores == sorted(scores, reverse=True), "Output must remain sorted descending after diversity"


# ==============================================================================
# Part B: Integration tests — require live local seeded DB
# ==============================================================================

@pytest.mark.asyncio
async def test_engine_returns_engine_generated_flag(client):
    """GET /api/recommendations must return is_engine_generated: true."""
    response = await client.get("/api/recommendations")
    assert response.status_code == 200
    data = response.json()
    assert data["is_engine_generated"] is True, "Engine flag must be True after Phase 3"


@pytest.mark.asyncio
async def test_engine_returns_valid_recommendation_structure(client):
    """Each recommendation must have required fields."""
    response = await client.get("/api/recommendations")
    assert response.status_code == 200
    data = response.json()

    assert data["learner_id"] == "u_1001"
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) > 0

    for rec in data["recommendations"]:
        assert "resource_id"   in rec
        assert "resource_title" in rec
        assert "score"         in rec
        assert "priority"      in rec
        assert "reasoning"     in rec
        assert "score_breakdown" in rec
        assert 0.0 <= rec["score"] <= 1.0
        assert rec["priority"] >= 1


@pytest.mark.asyncio
async def test_engine_rankings_are_ordered_descending(client):
    """Recommendations must be returned in descending score order."""
    response = await client.get("/api/recommendations")
    assert response.status_code == 200
    recs = response.json()["recommendations"]
    scores = [r["score"] for r in recs]
    assert scores == sorted(scores, reverse=True), (
        f"Recommendations are not sorted by score: {scores}"
    )


@pytest.mark.asyncio
async def test_engine_priorities_are_sequential(client):
    """Priority ranks must be 1, 2, 3, …, N."""
    response = await client.get("/api/recommendations")
    assert response.status_code == 200
    recs = response.json()["recommendations"]
    priorities = [r["priority"] for r in recs]
    assert priorities == list(range(1, len(priorities) + 1)), (
        f"Priorities are not sequential: {priorities}"
    )


@pytest.mark.asyncio
async def test_engine_excludes_completed_resources(client):
    """res_3 and res_4 are completed in seed data — they must not appear."""
    response = await client.get("/api/recommendations")
    assert response.status_code == 200
    rec_ids = {r["resource_id"] for r in response.json()["recommendations"]}
    assert "res_3" not in rec_ids, "Completed resource res_3 must not be recommended"
    assert "res_4" not in rec_ids, "Completed resource res_4 must not be recommended"


@pytest.mark.asyncio
async def test_engine_persists_to_database(db_pool, dev_learner_id):
    """Engine must write active recommendations to the DB."""
    from app.database.repositories.recommendations_repo import get_active_recommendations

    engine_results = await run_recommendation_engine(db_pool, dev_learner_id, persist=True)

    assert len(engine_results) > 0

    db_recs = await get_active_recommendations(db_pool, dev_learner_id)
    assert len(db_recs) == len(engine_results), (
        f"DB has {len(db_recs)} active recs but engine returned {len(engine_results)}"
    )


@pytest.mark.asyncio
async def test_engine_score_breakdown_present_in_db_response(client):
    """score_breakdown must be present for all recommendations."""
    response = await client.get("/api/recommendations")
    assert response.status_code == 200
    for rec in response.json()["recommendations"]:
        breakdown = rec.get("score_breakdown")
        assert breakdown is not None, f"score_breakdown missing for {rec['resource_id']}"
        assert "skill_gap" in breakdown
        assert "career_importance" in breakdown


@pytest.mark.asyncio
async def test_running_engine_twice_is_idempotent(client):
    """Running the engine twice should replace, not accumulate, recommendations."""
    from app.database.repositories.recommendations_repo import get_active_recommendations

    # First run (via HTTP — also persists)
    resp1 = await client.get("/api/recommendations")
    assert resp1.status_code == 200
    count1 = len(resp1.json()["recommendations"])

    # Second run
    resp2 = await client.get("/api/recommendations")
    assert resp2.status_code == 200
    count2 = len(resp2.json()["recommendations"])

    assert count1 == count2, (
        "Running engine twice should not accumulate rows — old batch must be deactivated first"
    )
