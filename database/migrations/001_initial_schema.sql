-- =============================================================================
-- Migration: 001_initial_schema.sql
-- Project:   Career Pathfinder — Supabase PostgreSQL Schema
-- Phase:     1 (Database only — no auth, no FastAPI, no recommendation engine)
-- Author:    Sanchit (DB/Backend module)
-- Created:   2026-08-25
--
-- Derived from frontend mock data:
--   - frontend/src/data/userData.js
--   - frontend/src/data/skillsData.js
--   - frontend/src/data/coursesData.js
--   - frontend/src/data/roadmapData.js
--   - frontend/src/data/assessmentData.js
--   - Bugged-Brains---Career-Pathfinder.-Ai-work-main/schemas.py
--
-- Table creation order (dependency-safe):
--   1.  skills
--   2.  careers
--   3.  career_skills
--   4.  skill_prerequisites
--   5.  learner_profiles
--   6.  learner_skills
--   7.  resources
--   8.  resource_skills
--   9.  roadmap_nodes
--   10. roadmap_node_prerequisites
--   11. learner_roadmap_nodes
--   12. assessments
--   13. assessment_questions
--   14. assessment_results
--   15. learning_history
--   16. recommendations
--   17. activity_log
--   18. roadmap_replans
--
-- NOTE ON AUTH:
--   learner_profiles.id is TEXT and will map 1:1 to auth.uid()::text once
--   Supabase Auth is enabled in Phase 3. No structural changes will be needed.
--   RLS policies are intentionally NOT added here.
-- =============================================================================


-- =============================================================================
-- 1. skills
-- Global catalog of skills. Proficiency and required scores are NOT stored
-- here — they belong to learner_skills (per-learner) and career_skills
-- (per-career) respectively.
-- =============================================================================
CREATE TABLE IF NOT EXISTS skills (
    id          TEXT        NOT NULL,               -- e.g. 'sk_react', 'sk_html'
    name        TEXT        NOT NULL,               -- Display name, e.g. 'React'
    description TEXT        NULL,                   -- Optional longer description
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT skills_pkey PRIMARY KEY (id),
    CONSTRAINT skills_name_unique UNIQUE (name)
);

COMMENT ON TABLE  skills            IS 'Global catalog of learnable skills. Proficiency is per-learner (learner_skills); requirement level is per-career (career_skills).';
COMMENT ON COLUMN skills.id         IS 'Stable slug identifier, e.g. sk_react. Matches frontend mock IDs.';
COMMENT ON COLUMN skills.name       IS 'Human-readable display name used in UI.';


-- =============================================================================
-- 2. careers
-- Target career/role catalog. A learner chooses one as their goal.
-- =============================================================================
CREATE TABLE IF NOT EXISTS careers (
    id          TEXT        NOT NULL,               -- e.g. 'career_frontend_dev'
    title       TEXT        NOT NULL,               -- e.g. 'Frontend Developer'
    description TEXT        NULL,                   -- Role description from skillsData.js
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT careers_pkey PRIMARY KEY (id),
    CONSTRAINT careers_title_unique UNIQUE (title)
);

COMMENT ON TABLE  careers            IS 'Target career/role catalog. Learners pick one career as their goal.';
COMMENT ON COLUMN careers.id         IS 'Stable slug, e.g. career_frontend_dev.';
COMMENT ON COLUMN careers.title      IS 'Display title, e.g. Frontend Developer.';


-- =============================================================================
-- 3. career_skills
-- Which skills a career requires, and at what minimum proficiency (0-100).
-- This powers the skill-gap calculation:
--   gap = career_skills.required_score - learner_skills.proficiency_score
-- =============================================================================
CREATE TABLE IF NOT EXISTS career_skills (
    career_id       TEXT    NOT NULL,               -- FK -> careers.id
    skill_id        TEXT    NOT NULL,               -- FK -> skills.id
    required_score  INT     NOT NULL DEFAULT 0      -- Minimum proficiency 0-100
        CHECK (required_score BETWEEN 0 AND 100),
    importance      TEXT    NULL,                   -- 'core' | 'nice-to-have' | NULL

    CONSTRAINT career_skills_pkey       PRIMARY KEY (career_id, skill_id),
    CONSTRAINT career_skills_career_fk  FOREIGN KEY (career_id)  REFERENCES careers(id) ON DELETE CASCADE,
    CONSTRAINT career_skills_skill_fk   FOREIGN KEY (skill_id)   REFERENCES skills(id)  ON DELETE CASCADE
);

COMMENT ON TABLE  career_skills                 IS 'Required skills per career with minimum proficiency thresholds. Used to compute skill gaps.';
COMMENT ON COLUMN career_skills.required_score  IS '0-100 minimum proficiency a learner needs to be considered ready for this career in this skill.';
COMMENT ON COLUMN career_skills.importance      IS 'Optional tag: core | nice-to-have. Null means unclassified.';


-- =============================================================================
-- 4. skill_prerequisites
-- Directed edges: skill_id requires prerequisite_skill_id.
-- Supports the Skill Graph (Member 3). Do NOT implement graph algorithms here.
-- =============================================================================
CREATE TABLE IF NOT EXISTS skill_prerequisites (
    skill_id                TEXT    NOT NULL,       -- The skill that has the prereq
    prerequisite_skill_id   TEXT    NOT NULL,       -- The prereq skill

    CONSTRAINT skill_prerequisites_pkey     PRIMARY KEY (skill_id, prerequisite_skill_id),
    CONSTRAINT skill_prereq_skill_fk        FOREIGN KEY (skill_id)              REFERENCES skills(id) ON DELETE CASCADE,
    CONSTRAINT skill_prereq_prereq_fk       FOREIGN KEY (prerequisite_skill_id) REFERENCES skills(id) ON DELETE CASCADE,
    CONSTRAINT skill_prereq_no_self_loop    CHECK (skill_id <> prerequisite_skill_id)
);

COMMENT ON TABLE  skill_prerequisites                       IS 'Directed prerequisite edges between skills. Skill A requires Skill B to be sufficiently learned first.';
COMMENT ON COLUMN skill_prerequisites.skill_id              IS 'The skill that requires the prerequisite.';
COMMENT ON COLUMN skill_prerequisites.prerequisite_skill_id IS 'The skill that must be completed first.';


-- =============================================================================
-- 5. learner_profiles
-- One row per learner. Mirrors the shape of userData.js / GET /api/me.
-- Computed fields (career_readiness, overall_progress, total_learning_hours)
-- are cached here and refreshed by the recommendation engine.
-- =============================================================================
CREATE TABLE IF NOT EXISTS learner_profiles (
    id                      TEXT        NOT NULL,   -- Matches auth.uid()::text in Phase 3
    name                    TEXT        NOT NULL,   -- Full name, e.g. 'Alex Rivera'
    first_name              TEXT        NULL,       -- Used for personalised UI greetings
    target_career_id        TEXT        NULL,       -- FK -> careers.id (current goal)
    current_level           TEXT        NULL,       -- e.g. 'Beginner-Intermediate'
    career_readiness        INT         NULL        -- Cached 0-100, computed by engine
        CHECK (career_readiness IS NULL OR career_readiness BETWEEN 0 AND 100),
    overall_progress        INT         NULL        -- Cached 0-100, % of roadmap complete
        CHECK (overall_progress IS NULL OR overall_progress BETWEEN 0 AND 100),
    streak_days             INT         NOT NULL DEFAULT 0
        CHECK (streak_days >= 0),
    weekly_learning_hours   INT         NOT NULL DEFAULT 8  -- Mirrors schemas.py weekly_hours constraint
        CHECK (weekly_learning_hours BETWEEN 1 AND 80),
    total_learning_hours    INT         NOT NULL DEFAULT 0  -- Cached sum of completed durations
        CHECK (total_learning_hours >= 0),
    interests               TEXT[]      NULL,       -- e.g. ARRAY['Web Development', 'UI Engineering']
    learning_style          TEXT        NULL,       -- Free text, e.g. 'Project-based, with short video primers'
    preferred_session_length TEXT       NULL,       -- e.g. '30-45 min'
    learning_preferences    JSONB       NULL,       -- {pace, format: [], difficulty} — display only, never filtered
    notification_settings   JSONB       NULL,       -- {roadmapUpdates, weeklyDigest, assessmentReminders, productNews}
    current_focus_skill_id  TEXT        NULL,       -- FK -> skills.id (active skill being studied)
    joined_at               TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    created_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at              TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT learner_profiles_pkey            PRIMARY KEY (id),
    CONSTRAINT learner_profiles_career_fk       FOREIGN KEY (target_career_id)       REFERENCES careers(id) ON DELETE SET NULL,
    CONSTRAINT learner_profiles_focus_skill_fk  FOREIGN KEY (current_focus_skill_id)  REFERENCES skills(id)  ON DELETE SET NULL
);

COMMENT ON TABLE  learner_profiles                          IS 'Core learner record. Mirrors userData.js shape. Will bind to auth.uid() in Phase 3.';
COMMENT ON COLUMN learner_profiles.id                       IS 'TEXT PK matching auth.uid()::text once Supabase Auth is enabled. Currently uses mock IDs like u_1001.';
COMMENT ON COLUMN learner_profiles.career_readiness         IS 'Cached 0-100 score computed by recommendation engine. NULL = not yet computed.';
COMMENT ON COLUMN learner_profiles.overall_progress         IS 'Cached 0-100 % of roadmap nodes completed. NULL = not yet computed.';
COMMENT ON COLUMN learner_profiles.total_learning_hours     IS 'Cached sum of hours from completed learning_history rows. Updated by engine.';
COMMENT ON COLUMN learner_profiles.learning_preferences     IS 'JSONB: {pace: str, format: [str], difficulty: str}. Display-only; never used as filter predicate.';
COMMENT ON COLUMN learner_profiles.notification_settings    IS 'JSONB: {roadmapUpdates, weeklyDigest, assessmentReminders, productNews}. UI product settings only.';


-- =============================================================================
-- 6. learner_skills
-- Per-learner proficiency for each skill.
-- Unique per (learner, skill) pair. Status drives roadmap display logic.
-- =============================================================================
CREATE TABLE IF NOT EXISTS learner_skills (
    id                  UUID        NOT NULL DEFAULT gen_random_uuid(),
    learner_id          TEXT        NOT NULL,           -- FK -> learner_profiles.id
    skill_id            TEXT        NOT NULL,           -- FK -> skills.id
    proficiency_score   INT         NOT NULL DEFAULT 0  -- 0-100, current measured proficiency
        CHECK (proficiency_score BETWEEN 0 AND 100),
    status              TEXT        NOT NULL DEFAULT 'not-started',
    last_assessed_at    TIMESTAMPTZ NULL,               -- When an assessment last updated this score
    created_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at          TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT learner_skills_pkey          PRIMARY KEY (id),
    CONSTRAINT learner_skills_unique        UNIQUE (learner_id, skill_id),
    CONSTRAINT learner_skills_learner_fk    FOREIGN KEY (learner_id) REFERENCES learner_profiles(id) ON DELETE CASCADE,
    CONSTRAINT learner_skills_skill_fk      FOREIGN KEY (skill_id)   REFERENCES skills(id)           ON DELETE CASCADE,
    CONSTRAINT learner_skills_status_check  CHECK (status IN ('not-started', 'completed', 'current', 'adapted', 'recommended', 'locked'))
);

COMMENT ON TABLE  learner_skills                    IS 'Per-learner skill proficiency and status. Gap = career_skills.required_score - learner_skills.proficiency_score.';
COMMENT ON COLUMN learner_skills.proficiency_score  IS '0-100. Combined with career_skills.required_score to compute skill gap for recommendation engine.';
COMMENT ON COLUMN learner_skills.status             IS 'Display status: completed | current | adapted | recommended | locked | not-started. Drives roadmap colour coding.';
COMMENT ON COLUMN learner_skills.last_assessed_at   IS 'Set when an assessment result updates this skill score.';


-- =============================================================================
-- 7. resources
-- Global catalog of learning resources: courses, videos, articles,
-- documentation, projects, practice sets. Per-learner progress goes in
-- learning_history; per-learner recommendation goes in recommendations.
-- =============================================================================
CREATE TABLE IF NOT EXISTS resources (
    id                          TEXT        NOT NULL,   -- e.g. 'res_1'
    title                       TEXT        NOT NULL,
    description                 TEXT        NULL,
    type                        TEXT        NOT NULL,   -- course | video | article | documentation | project | practice
    difficulty                  TEXT        NULL,       -- Beginner | Intermediate | Advanced
    duration_text               TEXT        NULL,       -- '3 wks', '20 min' stored as-is from mock
    url                         TEXT        NULL,       -- External URL if applicable
    why_recommended_template    TEXT        NULL,       -- Generic reason; engine overrides per learner
    created_at                  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT resources_pkey               PRIMARY KEY (id),
    CONSTRAINT resources_type_check         CHECK (type IN ('course', 'video', 'article', 'documentation', 'project', 'practice')),
    CONSTRAINT resources_difficulty_check   CHECK (difficulty IS NULL OR difficulty IN ('Beginner', 'Intermediate', 'Advanced'))
);

COMMENT ON TABLE  resources                             IS 'Global resource catalog. coursesData.js is the source of truth. Progress and recommendations are per-learner in separate tables.';
COMMENT ON COLUMN resources.duration_text               IS 'Free-text duration ("3 wks", "20 min"). Not normalised to avoid losing format variety.';
COMMENT ON COLUMN resources.why_recommended_template    IS 'Generic rationale. The recommendation engine replaces this with a learner-specific string in recommendations.reasoning.';


-- =============================================================================
-- 8. resource_skills
-- Many-to-many: which skills does a resource teach?
-- Mock data has one skill per resource, but this table supports multiple.
-- =============================================================================
CREATE TABLE IF NOT EXISTS resource_skills (
    resource_id TEXT        NOT NULL,               -- FK -> resources.id
    skill_id    TEXT        NOT NULL,               -- FK -> skills.id
    is_primary  BOOLEAN     NOT NULL DEFAULT TRUE,  -- TRUE = main skill; FALSE = supplementary

    CONSTRAINT resource_skills_pkey         PRIMARY KEY (resource_id, skill_id),
    CONSTRAINT resource_skills_resource_fk  FOREIGN KEY (resource_id) REFERENCES resources(id) ON DELETE CASCADE,
    CONSTRAINT resource_skills_skill_fk     FOREIGN KEY (skill_id)    REFERENCES skills(id)    ON DELETE CASCADE
);

COMMENT ON TABLE  resource_skills               IS 'Maps resources to the skills they teach. Allows one resource to cover multiple skills.';
COMMENT ON COLUMN resource_skills.is_primary    IS 'TRUE if this is the main skill; FALSE for supplementary coverage.';


-- =============================================================================
-- 9. roadmap_nodes
-- Template roadmap node definitions (skill, course, project, or assessment).
-- These are the global templates. Per-learner status lives in learner_roadmap_nodes.
-- =============================================================================
CREATE TABLE IF NOT EXISTS roadmap_nodes (
    id               TEXT        NOT NULL,          -- e.g. 'rm_react'
    type             TEXT        NOT NULL,          -- skill | course | project | assessment
    title            TEXT        NOT NULL,
    skill_id         TEXT        NULL,              -- FK -> skills.id (primary skill)
    career_id        TEXT        NULL,              -- FK -> careers.id (which career path)
    stage            INT         NOT NULL,          -- Layout ordering (0-indexed)
    difficulty       TEXT        NULL,              -- Beginner | Intermediate | Advanced | Comprehensive
    duration_text    TEXT        NULL,              -- '3 wks', '45 min' stored as-is
    description      TEXT        NULL,
    expected_outcome TEXT        NULL,              -- Optional outcome statement
    skills_gained    JSONB       NULL,              -- TEXT[] display bullets e.g. ['Components & props']
    why              JSONB       NULL,              -- TEXT[] rationale bullets for node detail panel
    resources_display JSONB      NULL,              -- TEXT[] display-only resource references
    created_at       TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT roadmap_nodes_pkey       PRIMARY KEY (id),
    CONSTRAINT roadmap_nodes_type_check CHECK (type IN ('skill', 'course', 'project', 'assessment')),
    CONSTRAINT roadmap_nodes_skill_fk   FOREIGN KEY (skill_id)  REFERENCES skills(id)   ON DELETE SET NULL,
    CONSTRAINT roadmap_nodes_career_fk  FOREIGN KEY (career_id) REFERENCES careers(id)  ON DELETE SET NULL
);

COMMENT ON TABLE  roadmap_nodes                     IS 'Template roadmap node definitions. Per-learner status is in learner_roadmap_nodes. Edges are in roadmap_node_prerequisites.';
COMMENT ON COLUMN roadmap_nodes.stage               IS 'Integer stage for layout ordering. Nodes sharing a stage render as parallel stations.';
COMMENT ON COLUMN roadmap_nodes.skills_gained       IS 'JSONB TEXT[]: display-only. Never used as filter predicate.';
COMMENT ON COLUMN roadmap_nodes.why                 IS 'JSONB TEXT[]: AI-authored rationale bullets. Display only.';
COMMENT ON COLUMN roadmap_nodes.resources_display   IS 'JSONB TEXT[]: display resource names. Real mappings are in resource_skills.';


-- =============================================================================
-- 10. roadmap_node_prerequisites
-- Directed edges: node_id requires prerequisite_node_id to be completed first.
-- Self-referential on roadmap_nodes. Supports graph traversal by Member 3.
-- =============================================================================
CREATE TABLE IF NOT EXISTS roadmap_node_prerequisites (
    node_id              TEXT    NOT NULL,          -- Node that has the prerequisite
    prerequisite_node_id TEXT    NOT NULL,          -- Node that must be completed first

    CONSTRAINT roadmap_node_prerequisites_pkey      PRIMARY KEY (node_id, prerequisite_node_id),
    CONSTRAINT roadmap_node_prereq_node_fk          FOREIGN KEY (node_id)              REFERENCES roadmap_nodes(id) ON DELETE CASCADE,
    CONSTRAINT roadmap_node_prereq_prereq_fk        FOREIGN KEY (prerequisite_node_id) REFERENCES roadmap_nodes(id) ON DELETE CASCADE,
    CONSTRAINT roadmap_node_prereq_no_self_loop     CHECK (node_id <> prerequisite_node_id)
);

COMMENT ON TABLE  roadmap_node_prerequisites                        IS 'Directed prerequisite edges between roadmap nodes. Enables topological ordering for the Learning Path Generator (Member 3).';
COMMENT ON COLUMN roadmap_node_prerequisites.node_id                IS 'The node that has the prerequisite.';
COMMENT ON COLUMN roadmap_node_prerequisites.prerequisite_node_id   IS 'The node that must be completed before node_id.';


-- =============================================================================
-- 11. learner_roadmap_nodes
-- Per-learner status for each roadmap node.
-- =============================================================================
CREATE TABLE IF NOT EXISTS learner_roadmap_nodes (
    id          UUID        NOT NULL DEFAULT gen_random_uuid(),
    learner_id  TEXT        NOT NULL,               -- FK -> learner_profiles.id
    node_id     TEXT        NOT NULL,               -- FK -> roadmap_nodes.id
    status      TEXT        NOT NULL DEFAULT 'locked',
    adapted_at  TIMESTAMPTZ NULL,                   -- Set when AI re-plans this node
    created_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT learner_roadmap_nodes_pkey           PRIMARY KEY (id),
    CONSTRAINT learner_roadmap_nodes_unique         UNIQUE (learner_id, node_id),
    CONSTRAINT learner_roadmap_nodes_learner_fk     FOREIGN KEY (learner_id) REFERENCES learner_profiles(id) ON DELETE CASCADE,
    CONSTRAINT learner_roadmap_nodes_node_fk        FOREIGN KEY (node_id)    REFERENCES roadmap_nodes(id)    ON DELETE CASCADE,
    CONSTRAINT learner_roadmap_nodes_status_check   CHECK (status IN ('completed', 'current', 'adapted', 'recommended', 'locked'))
);

COMMENT ON TABLE  learner_roadmap_nodes             IS 'Per-learner progress state for each roadmap node. The AI engine updates status and adapted_at when re-planning.';
COMMENT ON COLUMN learner_roadmap_nodes.adapted_at  IS 'Set by AI engine when this node was re-ordered or added due to an assessment result.';


-- =============================================================================
-- 12. assessments
-- Assessment definitions. Questions are in assessment_questions.
-- questionCount is derived (COUNT(*)).
-- =============================================================================
CREATE TABLE IF NOT EXISTS assessments (
    id              TEXT        NOT NULL,           -- e.g. 'as_react_basics'
    title           TEXT        NOT NULL,           -- 'React Basics Check-in'
    skill_id        TEXT        NULL,               -- FK -> skills.id (primary skill tested)
    estimated_time  TEXT        NULL,               -- '10 min'
    unlocks_node_id TEXT        NULL,               -- FK -> roadmap_nodes.id (unlocked on pass)
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT assessments_pkey             PRIMARY KEY (id),
    CONSTRAINT assessments_skill_fk         FOREIGN KEY (skill_id)        REFERENCES skills(id)        ON DELETE SET NULL,
    CONSTRAINT assessments_unlock_node_fk   FOREIGN KEY (unlocks_node_id) REFERENCES roadmap_nodes(id) ON DELETE SET NULL
);

COMMENT ON TABLE  assessments                   IS 'Assessment definitions. questionCount is derived from COUNT(*) in assessment_questions.';
COMMENT ON COLUMN assessments.unlocks_node_id   IS 'The roadmap node that becomes available upon passing this assessment.';


-- =============================================================================
-- 13. assessment_questions
-- Individual MCQ questions. options is JSONB — always read as a complete block.
-- =============================================================================
CREATE TABLE IF NOT EXISTS assessment_questions (
    id                TEXT        NOT NULL,         -- e.g. 'as_react_basics_q1'
    assessment_id     TEXT        NOT NULL,         -- FK -> assessments.id
    prompt            TEXT        NOT NULL,         -- Question text
    options           JSONB       NOT NULL,         -- [{id: 'a', text: '...'}, ...]
    correct_option_id TEXT        NOT NULL,         -- e.g. 'b'
    skill_id          TEXT        NULL,             -- FK -> skills.id (per-question skill tag)
    order_index       INT         NOT NULL,         -- 1-based ordering within assessment

    CONSTRAINT assessment_questions_pkey            PRIMARY KEY (id),
    CONSTRAINT assessment_questions_assessment_fk   FOREIGN KEY (assessment_id) REFERENCES assessments(id) ON DELETE CASCADE,
    CONSTRAINT assessment_questions_skill_fk        FOREIGN KEY (skill_id)      REFERENCES skills(id)      ON DELETE SET NULL,
    CONSTRAINT assessment_questions_order_positive  CHECK (order_index >= 1)
);

COMMENT ON TABLE  assessment_questions                   IS 'Individual MCQ questions. options is JSONB [{id, text}] read as a complete block.';
COMMENT ON COLUMN assessment_questions.skill_id          IS 'Per-question skill tag enabling per-skill diagnostic scoring (scoreAssessment() pattern).';
COMMENT ON COLUMN assessment_questions.correct_option_id IS 'ID of the correct option in the options JSONB array.';
COMMENT ON COLUMN assessment_questions.options           IS 'JSONB: [{id: str, text: str}]. Never queried by individual option values.';


-- =============================================================================
-- 14. assessment_results
-- Completed submissions with raw answers, scores, and engine output.
-- =============================================================================
CREATE TABLE IF NOT EXISTS assessment_results (
    id                  UUID        NOT NULL DEFAULT gen_random_uuid(),
    learner_id          TEXT        NOT NULL,       -- FK -> learner_profiles.id
    assessment_id       TEXT        NOT NULL,       -- FK -> assessments.id
    score_pct           INT         NOT NULL
        CHECK (score_pct BETWEEN 0 AND 100),
    correct_count       INT         NOT NULL
        CHECK (correct_count >= 0),
    total_questions     INT         NOT NULL
        CHECK (total_questions > 0),
    answers             JSONB       NOT NULL,       -- {question_id: chosen_option_id}
    skill_performance   JSONB       NOT NULL,       -- [{skill: str, percent: int}]
    strengths           TEXT[]      NULL,           -- Skill names where percent >= 70
    weak_areas          TEXT[]      NULL,           -- Skill names where percent < 70
    recommended_next    TEXT        NULL,           -- Engine-generated guidance text
    triggered_replan    BOOLEAN     NOT NULL DEFAULT FALSE,
    taken_at            TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT assessment_results_pkey         PRIMARY KEY (id),
    CONSTRAINT assessment_results_learner_fk   FOREIGN KEY (learner_id)    REFERENCES learner_profiles(id) ON DELETE CASCADE,
    CONSTRAINT assessment_results_assess_fk    FOREIGN KEY (assessment_id) REFERENCES assessments(id)      ON DELETE CASCADE
);

COMMENT ON TABLE  assessment_results                    IS 'Completed submissions with raw answers and per-skill diagnostic output.';
COMMENT ON COLUMN assessment_results.answers            IS 'JSONB map {question_id: chosen_option_id}. Stored for audit and replay.';
COMMENT ON COLUMN assessment_results.skill_performance  IS 'JSONB from scoreAssessment(): [{skill, percent}]. Engine reads this to update learner_skills.';
COMMENT ON COLUMN assessment_results.triggered_replan   IS 'TRUE if this result caused the AI engine to re-plan the learner roadmap.';


-- =============================================================================
-- 15. learning_history
-- Per-learner progress records for resources. Corresponds to both
-- userData.js learningHistory[] and coursesData.js progress/status fields.
-- =============================================================================
CREATE TABLE IF NOT EXISTS learning_history (
    id              TEXT        NOT NULL,           -- e.g. 'lh_1'; use gen_random_uuid()::text for new rows
    learner_id      TEXT        NOT NULL,           -- FK -> learner_profiles.id
    resource_id     TEXT        NULL,               -- FK -> resources.id (NULL for non-catalog items)
    title           TEXT        NOT NULL,           -- Denormalised for display
    type            TEXT        NOT NULL,
    status          TEXT        NOT NULL DEFAULT 'not-started',
    progress_pct    INT         NOT NULL DEFAULT 0
        CHECK (progress_pct BETWEEN 0 AND 100),
    completed_at    TIMESTAMPTZ NULL,               -- Set when status = 'completed'
    created_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at      TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT learning_history_pkey            PRIMARY KEY (id),
    CONSTRAINT learning_history_learner_fk      FOREIGN KEY (learner_id)  REFERENCES learner_profiles(id) ON DELETE CASCADE,
    CONSTRAINT learning_history_resource_fk     FOREIGN KEY (resource_id) REFERENCES resources(id)        ON DELETE SET NULL,
    CONSTRAINT learning_history_status_check    CHECK (status IN ('not-started', 'in-progress', 'completed')),
    CONSTRAINT learning_history_type_check      CHECK (type IN ('course', 'project', 'video', 'article', 'practice', 'documentation'))
);

COMMENT ON TABLE  learning_history              IS 'Per-learner resource progress. Combines userData.js learningHistory[] with per-learner progress from coursesData.js.';
COMMENT ON COLUMN learning_history.resource_id  IS 'NULL for completions not in the resources catalog (e.g. external projects, pre-existing knowledge).';
COMMENT ON COLUMN learning_history.title        IS 'Denormalised for display queries. Avoids join to resources for simple history lists.';


-- =============================================================================
-- 16. recommendations
-- Per-learner ranked resource recommendations generated by the engine.
-- =============================================================================
CREATE TABLE IF NOT EXISTS recommendations (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    learner_id      TEXT        NOT NULL,           -- FK -> learner_profiles.id
    resource_id     TEXT        NOT NULL,           -- FK -> resources.id
    score           FLOAT       NOT NULL DEFAULT 0.0,
    reasoning       TEXT        NULL,               -- Per-learner 'whyRecommended' from engine
    is_active       BOOLEAN     NOT NULL DEFAULT TRUE,  -- FALSE = superseded by newer batch
    generated_at    TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT recommendations_pkey         PRIMARY KEY (id),
    CONSTRAINT recommendations_learner_fk   FOREIGN KEY (learner_id)  REFERENCES learner_profiles(id) ON DELETE CASCADE,
    CONSTRAINT recommendations_resource_fk  FOREIGN KEY (resource_id) REFERENCES resources(id)        ON DELETE CASCADE
);

COMMENT ON TABLE  recommendations               IS 'Per-learner ranked recommendations from the engine. Old batches soft-deleted via is_active = FALSE.';
COMMENT ON COLUMN recommendations.score         IS 'Ranking score from recommendation engine. ORDER BY score DESC in queries.';
COMMENT ON COLUMN recommendations.reasoning     IS 'Per-learner "whyRecommended" from engine. Overrides resources.why_recommended_template.';
COMMENT ON COLUMN recommendations.is_active     IS 'Set to FALSE when engine generates new batch, invalidating the old set.';


-- =============================================================================
-- 17. activity_log
-- Append-only event log for the Recent Activity feed.
-- =============================================================================
CREATE TABLE IF NOT EXISTS activity_log (
    id              UUID        NOT NULL DEFAULT gen_random_uuid(),
    learner_id      TEXT        NOT NULL,           -- FK -> learner_profiles.id
    type            TEXT        NOT NULL,           -- assessment | roadmap | course | project | practice | article
    label           TEXT        NOT NULL,           -- e.g. 'Completed "JavaScript Fundamentals" assessment'
    meta            TEXT        NULL,               -- e.g. 'Scored 88%'
    reference_id    TEXT        NULL,               -- Soft ref to related entity — no FK enforced
    occurred_at     TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT activity_log_pkey        PRIMARY KEY (id),
    CONSTRAINT activity_log_learner_fk  FOREIGN KEY (learner_id) REFERENCES learner_profiles(id) ON DELETE CASCADE
);

COMMENT ON TABLE  activity_log                  IS 'Append-only event log powering the Recent Activity feed. Mirrors recentActivity[] from userData.js.';
COMMENT ON COLUMN activity_log.reference_id     IS 'Soft reference to related entity ID. No FK enforced to keep the log flexible across entity types.';
COMMENT ON COLUMN activity_log.occurred_at      IS 'Event timestamp. Use ORDER BY occurred_at DESC for timeline queries.';


-- =============================================================================
-- 18. roadmap_replans
-- Records each AI-triggered roadmap adaptation event.
-- Corresponds to roadmapData.js replanReason and previousRoadmapPath.
-- =============================================================================
CREATE TABLE IF NOT EXISTS roadmap_replans (
    id                          UUID        NOT NULL DEFAULT gen_random_uuid(),
    learner_id                  TEXT        NOT NULL,   -- FK -> learner_profiles.id
    triggered_by_assessment_id  TEXT        NULL,       -- FK -> assessments.id
    headline                    TEXT        NOT NULL,   -- e.g. 'Your learning path has been updated'
    reason                      TEXT        NOT NULL,   -- Explanation paragraph
    changes                     JSONB       NOT NULL,   -- [{type, label, detail}]
    previous_path               TEXT[]      NULL,       -- Ordered node IDs before replan
    updated_path                TEXT[]      NULL,       -- Ordered node IDs after replan
    triggered_at                TIMESTAMPTZ NOT NULL DEFAULT NOW(),

    CONSTRAINT roadmap_replans_pkey             PRIMARY KEY (id),
    CONSTRAINT roadmap_replans_learner_fk       FOREIGN KEY (learner_id)                 REFERENCES learner_profiles(id) ON DELETE CASCADE,
    CONSTRAINT roadmap_replans_assessment_fk    FOREIGN KEY (triggered_by_assessment_id) REFERENCES assessments(id)      ON DELETE SET NULL
);

COMMENT ON TABLE  roadmap_replans               IS 'Audit log of AI-driven roadmap re-planning events. Corresponds to replanReason in roadmapData.js.';
COMMENT ON COLUMN roadmap_replans.changes       IS 'JSONB: [{type: added|moved|removed, label: str, detail: str}].';
COMMENT ON COLUMN roadmap_replans.previous_path IS 'Snapshot of ordered node IDs before the replan. Enables before/after comparison UI.';
COMMENT ON COLUMN roadmap_replans.updated_path  IS 'Snapshot of ordered node IDs after the replan.';


-- =============================================================================
-- INDEXES
-- Only indexes with clear justification from mock data access patterns
-- and future recommendation engine query paths.
-- =============================================================================

-- learner_skills
CREATE INDEX IF NOT EXISTS idx_learner_skills_learner_id    ON learner_skills(learner_id);
CREATE INDEX IF NOT EXISTS idx_learner_skills_skill_id      ON learner_skills(skill_id);

-- learning_history
CREATE INDEX IF NOT EXISTS idx_learning_history_learner_id      ON learning_history(learner_id);
CREATE INDEX IF NOT EXISTS idx_learning_history_learner_status  ON learning_history(learner_id, status);

-- learner_roadmap_nodes
CREATE INDEX IF NOT EXISTS idx_learner_roadmap_nodes_learner_id ON learner_roadmap_nodes(learner_id);

-- assessment_results
CREATE INDEX IF NOT EXISTS idx_assessment_results_learner_id        ON assessment_results(learner_id);
CREATE INDEX IF NOT EXISTS idx_assessment_results_learner_assess    ON assessment_results(learner_id, assessment_id);

-- recommendations
CREATE INDEX IF NOT EXISTS idx_recommendations_learner_active   ON recommendations(learner_id, is_active);

-- activity_log (most recent first)
CREATE INDEX IF NOT EXISTS idx_activity_log_learner_occurred    ON activity_log(learner_id, occurred_at DESC);

-- roadmap graph traversal (forward + reverse)
CREATE INDEX IF NOT EXISTS idx_roadmap_prereq_node_id           ON roadmap_node_prerequisites(node_id);
CREATE INDEX IF NOT EXISTS idx_roadmap_prereq_prereq_id         ON roadmap_node_prerequisites(prerequisite_node_id);

-- career_skills (gap computation)
CREATE INDEX IF NOT EXISTS idx_career_skills_career_id          ON career_skills(career_id);

-- resource_skills (candidate resource generation)
CREATE INDEX IF NOT EXISTS idx_resource_skills_skill_id         ON resource_skills(skill_id);

-- assessment_questions
CREATE INDEX IF NOT EXISTS idx_assessment_questions_assess_id   ON assessment_questions(assessment_id);

-- roadmap_replans
CREATE INDEX IF NOT EXISTS idx_roadmap_replans_learner_id       ON roadmap_replans(learner_id);
