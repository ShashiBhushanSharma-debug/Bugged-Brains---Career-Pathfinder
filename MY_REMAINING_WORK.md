# MY_REMAINING_WORK.md
# Career Pathfinder - My Remaining Frontend/API Integration Work

---

## Already Complete (My Work)

- Backend Phase 2: Full DB/API layer (learner, skills, resources, recommendations, learning history, onboarding routes)
- Backend Phase 3: Recommendation Engine (recommendation_engine.py, GET /api/recommendations)
- Backend Phase 3.5: Integrated Member 1's LangGraph AI into backend (ai_adaptive_graph.py, POST /api/me/replan)

---

## Already Completed by Other Members

- Member 2: All frontend pages, components, CSS, and routing
- Member 1: Assessment.jsx already calls POST /api/me/replan and navigates to AdaptiveReplanning with the AI result

---

## Still Missing (My Responsibility)

### 1. Vite Dev Proxy
- vite.config.js needs a server.proxy so /api/* routes hit http://localhost:8000

### 2. Central API Client
- frontend/src/api/client.js
- Exports: apiFetch(path, options) with BASE_URL, JSON headers, error handling

### 3. Custom Hooks
- frontend/src/hooks/useLearner.js -> GET /api/me
- frontend/src/hooks/useActivity.js -> GET /api/me/activity
- frontend/src/hooks/useSkillAnalysis.js -> GET /api/skills/analysis
- frontend/src/hooks/useResources.js -> GET /api/resources
- frontend/src/hooks/useRecommendations.js -> GET /api/recommendations
- frontend/src/hooks/useLearningHistory.js -> GET /api/learning-history

### 4. Page Integrations

#### Dashboard.jsx
- Replace currentUser from userData.js with useLearner()
- Replace recentActivity from userData.js with useActivity()
- Keep roadmapData.js (no API), keep assessmentData.js (no API)
- Add loading and error states

#### SkillAnalysis.jsx
- Replace skills/skillCategories/targetRole from skillsData.js with useSkillAnalysis()
- Adapt field names: proficiency_score -> proficiency, required_score -> required, skill_id -> id
- Add loading and error states

#### Resources.jsx
- Replace resources from coursesData.js with useResources()
- Adapt API response field names (duration_text -> duration, primary_skill_name -> skill)
- Keep filter logic
- Add loading and error states

#### LearningHub.jsx
- Replace resources from coursesData.js with:
  - useLearningHistory() for in-progress items
  - useRecommendations() for recommended section
  - useResources() for Browse All section
- Add loading and error states

#### Profile.jsx
- Replace currentUser with useLearner()
- Replace skills with useSkillAnalysis()
- Replace currentUser.learningHistory with useLearningHistory()
- Add loading and error states

#### Progress.jsx
- Replace currentUser with useLearner()
- Replace skills with useSkillAnalysis()
- Keep roadmapData.js for roadmap node counts (no API)
- Add loading and error states

#### Settings.jsx
- Replace currentUser with useLearner()
- Wire handleSave to PATCH /api/me
- Add success/error feedback (already has toast)

#### Onboarding.jsx
- Wire final step (Generate My Learning Path button) to POST /api/onboarding
- Map form state to OnboardingRequest schema
- Navigate to /dashboard on success
- Add error handling

---

## Still Missing (Other Members' Responsibility)

### Member 3
- GET /api/roadmap endpoint
- Skill graph algorithm and prerequisite traversal
- Learning path ordering/generation

### Unassigned / Future Work
- GET /api/assessments endpoint
- GET /api/assessments/{id} endpoint
- POST /api/assessments/{id}/submit endpoint
- GET /api/graph/data endpoint (FC-004)
- Authentication system (FC-006, deferred)

---

## Mock Data - Intentionally Retained

| File | Reason |
|------|--------|
| roadmapData.js | No GET /api/roadmap exists - Member 3's scope |
| roadmapData.js - replanReason | No API equivalent - static placeholder |
| assessmentData.js - assessments | No GET /api/assessments endpoint |
| assessmentData.js - upcomingAssessment | No API endpoint |
| assessmentData.js - scoreAssessment() | Local scoring utility, no backend equivalent |

---

## Integration Rules Followed

- NO authentication implemented (out of scope)
- NO redesign of any UI
- NO rewrite of Member 2's components
- NO modification of recommendation_engine.py scoring logic
- NO modification of ai_adaptive_graph.py (Member 1's work)
- NO modification of database schema
- Dev learner ID u_1001 used throughout (same as backend DEV_LEARNER_ID)
- All API calls go through FastAPI only - no direct DB access from frontend
