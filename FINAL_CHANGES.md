# FINAL_CHANGES.md
# Career Pathfinder — Required Cross-Module Integration Changes

This file records changes that are needed in OTHER team members' modules
for final integration. These changes have NOT been made yet.

We will review this file together before final submission and apply them at that time.

---

## FC-001 — Frontend: Replace mock data with API calls

### Required Change
The frontend currently reads all data from static mock files:
- `frontend/src/data/userData.js`
- `frontend/src/data/skillsData.js`
- `frontend/src/data/coursesData.js`
- `frontend/src/data/roadmapData.js`
- `frontend/src/data/assessmentData.js`

These need to be replaced with `fetch()` / `axios` calls to the FastAPI backend.

### Why
The backend now exposes the same data via REST APIs. The frontend cannot read
from a real database without going through the API.

### Which Module
Member 2 — Frontend

### When It Should Be Done
After Phase 3 (auth) is complete and the backend is deployed.
Authentication must be in place before replacing mock data so the
frontend can send a real user token with each request.

### Suggested Implementation
Replace each mock import with a React hook (e.g., `useSWR` or `useQuery`):
```js
// Before
import { currentUser } from '../data/userData.js';

// After
const { data: currentUser } = useSWR('/api/me', fetcher);
```

Mapping:
| Mock file | API endpoint |
|---|---|
| `userData.js` | `GET /api/me`, `GET /api/me/activity` |
| `skillsData.js` | `GET /api/skills/analysis` |
| `coursesData.js` | `GET /api/resources`, `GET /api/learning-history` |
| `roadmapData.js` | `GET /api/roadmap` (Phase 3 endpoint) |
| `assessmentData.js` | `GET /api/assessments/{id}` (Phase 3 endpoint) |

---

## FC-002 — Frontend: Onboarding form POST to backend

### Required Change
The `/onboarding` page currently saves data nowhere. It needs to POST to
`POST /api/onboarding` on submission.

### Why
Without this, learner preferences, skills, and history from onboarding are
never persisted to the database.

### Which Module
Member 2 — Frontend

### When It Should Be Done
Can be done now (Phase 2 is live). Does not require auth since
`DEV_LEARNER_ID` is used during development.

### Suggested Implementation
```js
const handleSubmit = async (formData) => {
  await fetch('/api/onboarding', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      learner_id: 'u_1001',  // replaced by auth.uid() in Phase 3
      name: formData.name,
      target_career_id: formData.targetCareer,
      weekly_learning_hours: formData.weeklyHours,
      skills: formData.skills,
      prior_learning: formData.priorLearning,
    })
  });
};
```

---

## FC-003 — Member 1 (AI Engine): LearnerState skill format alignment

### Required Change
The AI engine's `LearnerState` in `schemas.py` uses:
```python
skills: Dict[str, float]  # skill name -> mastery probability 0.0-1.0
```

The database uses:
```sql
learner_skills.proficiency_score  -- INT 0-100
```

When the backend passes learner data to the AI engine, it converts:
```python
proficiency_int / 100.0  # e.g. 85 -> 0.85
```

The engine's output (updated mastery float) must be converted back:
```python
round(mastery_float * 100)  # e.g. 0.72 -> 72
```

This conversion is the backend's responsibility (in the service layer).

### Why
The two representations are incompatible. The backend is the integration
point and must own the translation.

### Which Module
Backend (me) + Member 1 (AI engine interface)

### When It Should Be Done
Phase 3 — when the recommendation/adaptive engine is wired to the backend.

### Suggested Implementation
```python
# backend/app/services/engine_bridge.py  (to be created in Phase 3)
def learner_skills_to_engine(learner_skills: list[dict]) -> dict[str, float]:
    return {ls["name"]: ls["proficiency_score"] / 100.0 for ls in learner_skills}

def engine_output_to_db(mastery: dict[str, float]) -> dict[str, int]:
    return {name: round(prob * 100) for name, prob in mastery.items()}
```

---

## FC-004 — Member 3 (Skill Graph): Prerequisite data API endpoint

### Required Change
Member 3's Skill Graph and Learning Path Generator needs access to:
- All skill prerequisite edges (`skill_prerequisites` table)
- All roadmap node prerequisite edges (`roadmap_node_prerequisites` table)

The backend should expose a dedicated endpoint for this:
```
GET /api/graph/data
```

This endpoint already has underlying DB functions ready:
- `skills_repo.get_all_skill_prerequisites(pool)`
- Query `roadmap_node_prerequisites` directly

### Why
Member 3 should not connect to the database directly. The backend owns the
DB layer and should expose clean data for the graph algorithm.

### Which Module
Backend (me) — adding one endpoint
Member 3 — consuming the endpoint

### When It Should Be Done
Phase 3. Can be a quick addition alongside the recommendation engine work.

### Suggested Implementation
```python
@router.get("/api/graph/data")
async def get_graph_data(pool=Depends(get_pool)):
    skill_prereqs = await skills_repo.get_all_skill_prerequisites(pool)
    # also fetch roadmap_node_prerequisites
    return {
        "skill_prerequisites": skill_prereqs,
        "roadmap_node_prerequisites": node_prereqs,
    }
```

---

## FC-005 — Backend: Roadmap and Assessment endpoints (Phase 3 additions)

### Required Change
The frontend has pages for `/roadmap` and `/assessments/:id` that currently
read from mock data. The backend needs these endpoints:
```
GET  /api/roadmap              — learner's current roadmap nodes with status
GET  /api/assessments          — available assessments
GET  /api/assessments/{id}     — single assessment with questions
POST /api/assessments/{id}/submit — submit answers, get results
```

### Why
These tables exist in the DB (`roadmap_nodes`, `assessments`, `assessment_questions`,
`assessment_results`, `learner_roadmap_nodes`) but no routes were built in Phase 2
since the priority was the core learner+skills+resources layer.

### Which Module
Backend (me)

### When It Should Be Done
Phase 3 — implement alongside the recommendation engine and auth.

### Suggested Implementation
Add `app/api/routes/roadmap.py` and `app/api/routes/assessments.py`.
The repositories layer already has the DB structure to support these.

---

## FC-006 — Auth: learner_id source swap

### Required Change
Every route currently gets `learner_id` from `DEV_LEARNER_ID` env var:
```python
def _get_learner_id(settings=Depends(get_settings)) -> str:
    return settings.dev_learner_id
```

In Phase 3, this must be replaced with JWT token extraction:
```python
async def _get_learner_id(token: str = Depends(oauth2_scheme)) -> str:
    payload = verify_supabase_jwt(token)
    return payload["sub"]  # auth.uid()
```

### Why
Without real auth, any caller can read/write any learner's data.

### Which Module
Backend (me) — one-line change per route dependency
Member 2 — Frontend sends the JWT in Authorization header

### When It Should Be Done
Phase 3 — after Supabase Auth is configured.

### Suggested Implementation
Replace the `_get_learner_id` dependency in each route file.
The `learner_profiles.id = auth.uid()::text` mapping is already correct.
No DB schema changes needed.

---

*Last updated: 2026-08-26 | Phase 2 complete*

---

## FC-007 — Member 1 (Explainable AI): score_breakdown field in recommendations

### What is available now (Phase 3)
Every `GET /api/recommendations` response now includes a `score_breakdown` dict
in each `RecommendationItem`:

```json
{
  "resource_id": "res_5",
  "resource_title": "Task Board — Mini Project",
  "score": 0.8371,
  "reasoning": "Core career skill with a 60-point gap to close. Matches your preferred learning format.",
  "target_skill_id": "sk_state",
  "score_breakdown": {
    "skill_gap":          0.60,
    "career_importance":  1.0,
    "difficulty_fit":     0.95,
    "preference_fit":     1.0,
    "duration_fit":       0.75,
    "history_context":    1.0,
    "readiness_mult":     1.0
  }
}
```

### Required Change
Member 1's Explainable AI module should consume `score_breakdown` to generate
richer natural language explanations rather than computing its own scoring.

The `reasoning` field in the response is a deterministic baseline string
generated by the Recommendation Engine. Member 1's LLM can use this as a
starter prompt or replace it entirely with a richer explanation.

### Which Module
Member 1 — Explainable AI

### When It Should Be Done
Whenever Member 1 integrates their Explainable AI with the backend API.

### Backward Compatibility
`score_breakdown` is a new **optional** field. Clients that don't use it
will not break. No schema changes required.

---

## FC-008 — Member 3 (Skill Graph / Learning Path): target_skill_id in recommendations

### What is available now (Phase 3)
Every recommendation now includes `target_skill_id` — the specific skill
with the largest gap that the resource addresses:

```json
{
  "resource_id": "res_5",
  "target_skill_id": "sk_state",
  "target_skill_name": "sk_state"
}
```

For multi-skill resources (e.g. Task Board covers React + State Management),
`target_skill_id` is the skill with the **highest gap** that the resource teaches.

### Required Change
Member 3's Learning Path Generator can use `target_skill_id` from each
recommendation to determine where to insert the resource in the learning path
relative to the Skill Graph node order.

```
GET /api/recommendations
→ [{resource_id, target_skill_id, score, priority}, ...]
→ Feed into Skill Graph ordering to determine prerequisite-respecting sequence
```

### Which Module
Member 3 — Skill Graph / Learning Path Generator

### When It Should Be Done
When Member 3 integrates the Skill Graph output with the Recommendation Engine
output.

---

## FC-009 — Frontend: Replace coursesData.js recommended flag with GET /api/recommendations

### What is available now (Phase 3)
`GET /api/recommendations` now returns **engine-generated** personalized
recommendations (`is_engine_generated: true`), replacing the static seeded
recommendations from Phase 2.

### Required Change
The frontend currently determines which courses to highlight using the
static `recommended: true` flag in `coursesData.js`.

This should be replaced with a real API call:

```js
// Before (static mock)
import { courses } from '../data/coursesData.js';
const recommended = courses.filter(c => c.recommended);

// After (real engine output)
const { data } = useSWR('/api/recommendations', fetcher);
const recommended = data?.recommendations ?? [];
```

Response fields to use:
- `resource_id` → maps to existing course IDs
- `resource_title` → display name
- `reasoning` → "Why recommended" text
- `score` → can be used to show a relevance indicator
- `priority` → display order (1 = most important)
- `target_skill_name` → "This will help with ___" label

### Which Module
Member 2 — Frontend

### When It Should Be Done
After auth is integrated (FC-006), so the correct learner's recommendations
are returned. Can be done now for the dev learner `u_1001`.

---

## Summary of Pre-existing Test Failures (Pre-Phase 3)

Two pre-existing Phase 2 tests fail due to test ordering — not Phase 3 regressions:

| Test | Root cause |
|---|---|
| `test_seed_learner_exists` | `test_onboarding_creates_learner` runs first and overwrites learner name to "Sanchit Test" |
| `test_get_me_shape` | Same root cause — name assertion fails after onboarding test |

**Fix**: These pre-existing tests need isolation (e.g., a teardown/restore fixture
or a unique test learner ID for the onboarding test). This is a Phase 2 cleanup
task, not a Phase 3 concern.

---

*Last updated: 2026-08-26 | Phase 3 complete — Recommendation Engine implemented and tested*
