# INTEGRATION_NOTES.md
# Career Pathfinder - Integration Ambiguities and Required Contracts

---

## IN-001: Roadmap API - Required from Member 3

The frontend RoadmapPage.jsx, Dashboard.jsx, and Progress.jsx all render roadmap data
from the static roadmapData.js mock. Member 3 has not yet exposed a GET /api/roadmap endpoint.

Required endpoint:
  GET /api/roadmap

Expected response shape (matching roadmapData.js roadmapNodes[]):
  {
    "nodes": [
      {
        "id": "rm_react",
        "type": "course",
        "title": "React Fundamentals",
        "skill": "React",
        "stage": 2,
        "status": "current",        // completed | current | adapted | recommended | locked
        "difficulty": "Intermediate",
        "duration": "3 wks",
        "prerequisites": ["rm_js"],
        "skillsGained": [...],
        "description": "...",
        "why": [...],
        "resources": [...],
        "expectedOutcome": "..."
      }
    ]
  }

Action: Member 3 should implement GET /api/roadmap using the roadmap_nodes +
learner_roadmap_nodes tables that already exist in the DB.

Until this exists: roadmapData.js mock is retained. Do NOT reimplement in frontend.

---

## IN-002: Assessment Endpoints - Required from Backend (my future work)

The assessmentData.js mock data is currently used by:
- Assessments.jsx - lists available assessments
- Assessment.jsx - runs individual assessments
- Dashboard.jsx - shows upcoming assessment

Backend tables already exist: assessments, assessment_questions, assessment_results
No routes currently expose them.

Required endpoints (FC-005):
  GET  /api/assessments              - list available assessments
  GET  /api/assessments/{id}         - single assessment with questions
  POST /api/assessments/{id}/submit  - submit answers, get scored results

Action: These are my responsibility to build in a future sub-phase.
For now: assessmentData.js is retained. Assessment.jsx scoring is done locally.

---

## IN-003: API Field Name Mapping

The backend response field names differ from the mock data field names in several cases.
The integration hooks must adapt:

userData.js currentUser -> GET /api/me LearnerProfileResponse:
  targetRole    -> NOT directly in API (career_title from career endpoint lookup)
  firstName     -> first_name
  avatarInitials -> NOT in API (derive from name)
  careerReadiness -> career_readiness
  overallProgress -> overall_progress
  streakDays    -> streak_days
  weeklyLearningHours -> weekly_learning_hours
  totalLearningHours -> total_learning_hours
  learningStyle -> learning_style
  preferredSessionLength -> preferred_session_length
  learningPreferences -> learning_preferences
  notificationSettings -> notification_settings
  currentFocus.skillId -> current_focus_skill_id
  joinedAt -> joined_at
  learningHistory -> NOT in GET /api/me (use GET /api/learning-history)

skillsData.js skills[] -> GET /api/skills/analysis categories[].skills[]:
  id -> skill_id
  proficiency -> proficiency_score
  required -> required_score
  reasoning -> NOT in API response (static reasoning not stored in DB)
  category -> derived from parent category object

coursesData.js resources[] -> GET /api/resources ResourceResponse:
  skill -> primary_skill_name
  duration -> duration_text
  status -> NOT in catalog API (per-learner status is in learning-history)
  progress -> NOT in catalog API (in learning-history)
  recommended -> NOT in catalog API (from GET /api/recommendations)
  whyRecommended -> why_recommended_template (template) or reasoning (from recommendations)

GET /api/recommendations RecommendationItem:
  resource_id -> maps to resource id
  resource_title -> display title
  score -> relevance score
  reasoning -> "Why recommended" text
  priority -> display order
  target_skill_name -> "This will help with ___"
  score_breakdown -> for Explainable AI (Member 1 to consume)
  is_engine_generated -> should be true for all live results

---

## IN-004: Onboarding Skill ID Mapping

The Onboarding.jsx uses free-text skill names ('React', 'JavaScript', etc.)
but POST /api/onboarding requires skill_id (e.g. 'sk_react').

Resolution strategy for integration:
- Call GET /api/skills at component load to get the full skill catalog
- Build a name->id map: { 'React': 'sk_react', ... }
- When user selects a skill by name, look up the skill_id before sending to API
- If a skill name is not found in catalog, skip it (don't error)

---

## IN-005: Onboarding Career ID Mapping

Onboarding step 0 lets users pick a role by display name ('Frontend Developer').
POST /api/onboarding requires target_career_id (e.g. 'car_frontend').

Resolution strategy:
- Call GET /api/careers at component load to get the full career catalog
- Build a name->id map: { 'Frontend Developer': 'car_frontend', ... }

---

## IN-006: targetRole Display in Dashboard/SkillAnalysis

GET /api/me returns target_career_id but not the career title.
The Dashboard and SkillAnalysis pages display currentUser.targetRole.

Resolution options:
a) Accept that we show target_career_id as a fallback
b) Do a second fetch to GET /api/careers/{id} and include title in the hook result
c) Use targetRole from a combined hook that fetches both

Selected approach: Fetch career title in useLearner() hook alongside the learner profile.
This keeps the rest of the page code simple.

---

## IN-007: avatarInitials Not in API

The API returns name and first_name but not avatarInitials.
Derive it in the hook: initials from first two words of name.

---

## IN-008: Learning History vs. coursesData Resources

The Resources.jsx and LearningHub.jsx currently show status ('in-progress', 'completed')
and progress percentage from coursesData.js. These per-learner fields come from:
  GET /api/learning-history

The global resource catalog from GET /api/resources does NOT include per-learner status.

Integration approach:
- Fetch both GET /api/resources and GET /api/learning-history
- Merge: for each resource, find the matching history item by resource_id
- Use history item's status and progress_pct if found, else default to 'not-started' / 0

---

## IN-009: Graph Data Endpoint (FC-004)

For Member 3's Skill Graph algorithm to work without direct DB access:
  GET /api/graph/data

This should return:
  {
    "skill_prerequisites": [
      { "skill_id": "sk_react", "prerequisite_skill_id": "sk_js" }
    ],
    "roadmap_node_prerequisites": [
      { "node_id": "rm_react", "prerequisite_node_id": "rm_js" }
    ]
  }

Backend repositories already have skills_repo.get_all_skill_prerequisites(pool).
This endpoint would be a quick addition on my side once Member 3 requests it.

Action: Document for Member 3. Do not build until Member 3 confirms they need it.
