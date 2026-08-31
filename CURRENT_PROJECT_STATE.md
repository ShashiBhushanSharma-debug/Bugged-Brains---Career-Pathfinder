# CURRENT_PROJECT_STATE.md
# Career Pathfinder — Full Repository Audit
# Audited: 2026-08-30 | Branch: feature/frontend-integration

---

## 1. Git State

Branch:  feature/frontend-integration
Status:  nothing to commit, working tree clean

Recent commits:
- d17f7ac  Merge PR #4 - feature/adaptive_skillgraph
- 39ac11e  feat(Adaptive Skill Graph): Added the adaptive test learner and server settings
- 7bccd32  feat(Adaptive Skill Graph): Added the core feature of adaptive skill graph
- 413c392  Merge PR #3 - feature/recommendation-engine
- 878df85  feat: implement personalized recommendation engine
- f7c1e97  Merge PR #2 - feature/frontend
- db20426  Add Career Pathfinder frontend

---

## 2. What Each Member Has Contributed

### Member 1 (Explainable AI / Adaptive Engine)
- Bugged-Brains---Career-Pathfinder.-Ai-work-main/ - standalone AI module
  - adaptive_engine.py - Bayesian Knowledge Tracing implementation
  - path_explainer.py - path explanation generator
  - assistant.py - conversational assistant
  - schemas.py - LearnerState, LearningPath schemas
- Integrated into backend:
  - backend/app/services/ai_adaptive_graph.py - LangGraph workflow
  - backend/app/api/routes/learner.py - POST /api/me/replan endpoint
- Frontend integration: Assessment.jsx already calls POST /api/me/replan [COMPLETE]

### Member 2 (Frontend/UI)
- Full React frontend in frontend/src/ - all pages, components, and CSS
- Assessment -> Adaptive Replan flow already wired to real backend in Assessment.jsx

### Member 3 (Skill Graph / Learning Path)
- No separate Skill Graph module found in the repository
- No GET /api/roadmap endpoint in the backend
- Roadmap currently renders from roadmapData.js (static mock)

### Me (Backend / DB / Recommendation Engine)
- Complete FastAPI application in backend/
  - Phase 2: DB connection, repositories, 6 route files, 6 schema files, skills_analysis service
  - Phase 3: recommendation_engine.py, GET /api/recommendations with is_engine_generated=true
  - ai_adaptive_graph.py - LangGraph AI engine integrated
  - POST /api/me/replan endpoint

---

## 3. Existing Backend API Endpoints

LIVE:
- GET    /health
- GET    /api/me
- PATCH  /api/me
- GET    /api/me/activity
- POST   /api/me/replan
- POST   /api/onboarding
- GET    /api/skills/analysis
- GET    /api/skills
- GET    /api/skills/{id}
- GET    /api/careers
- GET    /api/careers/{id}
- GET    /api/resources
- GET    /api/resources/{id}
- GET    /api/recommendations
- POST   /api/recommendations
- GET    /api/learning-history
- POST   /api/learning-history
- PATCH  /api/learning-history/{id}
- GET    /api/learning-history/{id}

MISSING (no implementation):
- GET    /api/roadmap                  (FC-005)
- GET    /api/assessments              (FC-005)
- GET    /api/assessments/{id}         (FC-005)
- POST   /api/assessments/{id}/submit  (FC-005)
- GET    /api/graph/data               (FC-004)

---

## 4. Frontend Data Source Audit

userData.js - currentUser:
  Pages: Dashboard, SkillAnalysis, Profile, Progress, Settings
  Real API: GET /api/me (EXISTS)
  Status: NOT integrated

userData.js - recentActivity:
  Pages: Dashboard
  Real API: GET /api/me/activity (EXISTS)
  Status: NOT integrated

skillsData.js - skills, skillCategories, targetRole:
  Pages: SkillAnalysis, Profile, Progress
  Real API: GET /api/skills/analysis (EXISTS)
  Status: NOT integrated

coursesData.js - resources:
  Pages: LearningHub, Resources
  Real API: GET /api/resources + GET /api/recommendations (EXIST)
  Status: NOT integrated

roadmapData.js - roadmapNodes:
  Pages: Dashboard, RoadmapPage, Progress
  Real API: NONE
  Status: RETAIN (Member 3 scope)

roadmapData.js - replanReason:
  Pages: Dashboard
  Real API: NONE
  Status: RETAIN

assessmentData.js - all exports:
  Pages: Assessment, Assessments, Dashboard
  Real API: NONE
  Status: RETAIN (no backend endpoint)

---

## 5. Frontend API Calls Currently Made

- Assessment.jsx -> POST /api/me/replan [INTEGRATED by Member 1]
- All other pages: ZERO API calls - 100% mock data

---

## 6. Pending Work

### My Responsibility
1. Vite proxy config (/api/* -> http://localhost:8000)
2. src/api/client.js - central API client
3. GET /api/me -> Dashboard, SkillAnalysis, Profile, Progress, Settings
4. GET /api/me/activity -> Dashboard
5. GET /api/skills/analysis -> SkillAnalysis, Progress, Profile
6. GET /api/resources -> Resources page
7. GET /api/recommendations -> LearningHub
8. GET /api/learning-history -> LearningHub + Profile
9. POST /api/onboarding -> Onboarding page
10. PATCH /api/me -> Settings page

### Other Members' Remaining Work
- GET /api/roadmap endpoint (Member 3)
- GET /api/assessments endpoint (unassigned / future)
- Member 1 standalone AI module full integration

---

## 7. Security

- Backend .env has DB credentials - correctly gitignored
- Frontend has NO backend credentials - correct
- Dev learner ID = u_1001 used via _get_learner_id dependency on all routes
