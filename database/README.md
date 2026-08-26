# Career Pathfinder — Database

Supabase PostgreSQL schema for the Career Pathfinder app.

## Phase 1 Scope

- ✅ Schema design (`001_initial_schema.sql`)
- ✅ Seed data from mock files (`002_seed_data.sql`)
- ✅ Validated locally with PostgreSQL 18
- ❌ Supabase Auth (Phase 3)
- ❌ FastAPI backend (Phase 2)
- ❌ Recommendation Engine (Phase 2)

---

## Table Inventory (18 tables)

| # | Table | Purpose | Rows (seed) |
|---|---|---|---|
| 1 | `skills` | Global skill catalog | 10 |
| 2 | `careers` | Target career/role catalog | 1 |
| 3 | `career_skills` | Required skills per career with proficiency thresholds | 10 |
| 4 | `skill_prerequisites` | Directed prerequisite edges between skills | 10 |
| 5 | `learner_profiles` | Core learner record (maps to `auth.uid()` in Phase 3) | 1 |
| 6 | `learner_skills` | Per-learner skill proficiency + status | 10 |
| 7 | `resources` | Learning resource catalog (courses, videos, projects…) | 8 |
| 8 | `resource_skills` | Many-to-many: resources ↔ skills | 10 |
| 9 | `roadmap_nodes` | Roadmap node templates (global, not per-learner) | 10 |
| 10 | `roadmap_node_prerequisites` | Directed prerequisite edges between roadmap nodes | 9 |
| 11 | `learner_roadmap_nodes` | Per-learner status for each roadmap node | 10 |
| 12 | `assessments` | Assessment definitions | 1 |
| 13 | `assessment_questions` | Individual MCQ questions | 6 |
| 14 | `assessment_results` | Completed submissions with scores + diagnostics | 0 |
| 15 | `learning_history` | Per-learner resource progress | 8 |
| 16 | `recommendations` | Per-learner ranked recommendations (engine output) | 4 |
| 17 | `activity_log` | Append-only event log (Recent Activity feed) | 4 |
| 18 | `roadmap_replans` | Audit log of AI roadmap adaptations | 1 |

---

## Applying Migrations in Supabase

### Option A — Supabase Dashboard (recommended for hackathon)

1. Open your Supabase project → **SQL Editor**
2. Paste the contents of `001_initial_schema.sql` → **Run**
3. Paste the contents of `002_seed_data.sql` → **Run**

### Option B — Supabase CLI

```bash
supabase db push  # if using supabase link + local migration folder
```

### Option C — Local psql (for testing)

```bash
createdb career_pathfinder_test
psql -d career_pathfinder_test -f database/migrations/001_initial_schema.sql
psql -d career_pathfinder_test -f database/migrations/002_seed_data.sql
```

---

## Core Query Pattern (for Recommendation Engine — Phase 2)

The schema is designed so the engine can always run:

```
Learner → learner_skills → skill gap →  career_skills → candidate skills
                                      ↘ resource_skills → resources → recommendations
```

Example gap query:

```sql
SELECT
    s.name,
    ls.proficiency_score,
    cs.required_score,
    (cs.required_score - ls.proficiency_score) AS gap
FROM learner_skills ls
JOIN skills s         ON s.id  = ls.skill_id
JOIN career_skills cs ON cs.skill_id = ls.skill_id
JOIN learner_profiles lp ON lp.id = ls.learner_id
    AND lp.target_career_id = cs.career_id
WHERE ls.learner_id = 'u_1001'
ORDER BY gap DESC;
```

---

## Key Design Decisions

| Decision | Rationale |
|---|---|
| `learner_profiles.id` is `TEXT` | Maps to `auth.uid()::text` in Phase 3 with zero structural change |
| Skill `category` not stored | Derived at query time from `proficiency_score` vs `required_score` gap |
| `duration_text` as free text | Mock data uses mixed formats ("3 wks", "20 min") — normalising would lose info |
| `learningPreferences` as JSONB | Never used as a filter predicate; display-only config object |
| `activity_log` is append-only | Audit semantics; no UPDATE needed |
| `recommendations.is_active` | Soft-delete old batches when engine re-runs |
| `roadmap_replans` added | Required for the before/after roadmap comparison UI |

---

## Auth Notes (for Phase 3)

RLS is intentionally NOT enabled in Phase 1.

When Supabase Auth is added, every learner-scoped table has `learner_id TEXT`
that will bind to `auth.uid()::text`. Future RLS pattern:

```sql
-- Example (do NOT add now):
ALTER TABLE learner_skills ENABLE ROW LEVEL SECURITY;
CREATE POLICY "own data" ON learner_skills
  FOR ALL USING (learner_id = auth.uid()::text);
```

Reference tables (`skills`, `careers`, `resources`, `roadmap_nodes`,
`assessments`, `assessment_questions`) will use:

```sql
CREATE POLICY "read only" ON skills FOR SELECT USING (true);
```

---

## Source Files

| SQL file | Derived from |
|---|---|
| `001_initial_schema.sql` | All 5 mock data files + `schemas.py` |
| `002_seed_data.sql` | All 5 mock data files (field-by-field mapping) |
