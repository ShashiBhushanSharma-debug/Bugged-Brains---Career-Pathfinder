# Career Pathfinder — Backend

FastAPI backend for the Career Pathfinder app.
Connects the React frontend to Supabase PostgreSQL.

**Phase 2**: Database read/write layer. No auth yet.

---

## Setup

```bash
cd backend

# 1. Create virtual environment
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Configure environment
cp .env.example .env
# Edit .env and set DATABASE_URL from Supabase Dashboard
# Project Settings > Database > Connection string > URI (port 5432)

# 4. Run the dev server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Open http://localhost:8000/docs for the interactive API explorer.

---

## API Endpoints

| Method | Path | Description |
|---|---|---|
| GET | `/health` | Health check |
| GET | `/api/me` | Current learner profile |
| PATCH | `/api/me` | Update learner profile |
| GET | `/api/me/activity` | Recent activity log |
| POST | `/api/onboarding` | Save onboarding data |
| GET | `/api/skills` | Global skill catalog |
| GET | `/api/skills/{id}` | Single skill |
| GET | `/api/skills/analysis` | Skill gap analysis |
| GET | `/api/careers` | Career catalog |
| GET | `/api/careers/{id}` | Career + required skills |
| GET | `/api/resources` | Resource catalog (filterable) |
| GET | `/api/resources/{id}` | Single resource |
| GET | `/api/learning-history` | Learner resource progress |
| POST | `/api/learning-history` | Start tracking a resource |
| PATCH | `/api/learning-history/{id}` | Update progress |
| GET | `/api/recommendations` | Active recommendations |
| POST | `/api/recommendations` | Save engine recommendations |

### Query Parameters

- `GET /api/resources?skill_id=sk_react&type=course`
- `GET /api/learning-history?status=completed`
- `GET /api/me/activity?limit=10`

---

## Project Structure

```
backend/
├── app/
│   ├── main.py              # FastAPI app factory + lifespan
│   ├── config.py            # Settings from .env
│   ├── api/
│   │   ├── router.py        # Central router
│   │   └── routes/
│   │       ├── learner.py
│   │       ├── onboarding.py
│   │       ├── skills.py
│   │       ├── resources.py
│   │       ├── recommendations.py
│   │       └── learning_history.py
│   ├── database/
│   │   ├── connection.py    # asyncpg pool lifecycle
│   │   └── repositories/
│   │       ├── learner_repo.py
│   │       ├── skills_repo.py
│   │       ├── careers_repo.py
│   │       ├── resources_repo.py
│   │       ├── learning_history_repo.py
│   │       └── recommendations_repo.py
│   ├── schemas/             # Pydantic request/response types
│   │   ├── learner.py
│   │   ├── skills.py
│   │   ├── resources.py
│   │   ├── recommendations.py
│   │   ├── onboarding.py
│   │   └── learning_history.py
│   └── services/
│       └── skills_analysis.py  # Gap computation logic
├── tests/
│   ├── conftest.py
│   ├── test_connection.py
│   ├── test_learner.py
│   ├── test_skills.py
│   └── test_resources.py
├── requirements.txt
├── pyproject.toml
└── .env.example
```

---

## Running Tests

```bash
cd backend

# Requires DATABASE_URL set in .env and seed data applied
pytest -v
```

Tests use a real Supabase connection with the seeded data (u_1001).

---

## Auth Note (Phase 3)

Authentication is out of scope for Phase 2.

Every route has a `_get_learner_id()` dependency that currently returns
`DEV_LEARNER_ID` from `.env`. In Phase 3, this will be replaced with a JWT
token extractor that calls `auth.uid()`.

No structural changes to the routes will be needed.

---

## Phase 3 — Recommendation Engine

The recommendation engine schemas are already defined in:
`app/schemas/recommendations.py`

The `LearnerContextForEngine` and `RecommendationItem` types define the
exact input/output contract. Phase 3 plugs the scoring algorithm into
`app/services/` and calls `POST /api/recommendations` to write back results.
