-- =============================================================================
-- Migration: 003_auth_rls.sql
-- Project:   Career Pathfinder — Supabase Row Level Security (RLS)
-- Phase:     3 (Authentication & User Identity)
-- Created:   2026-08-30
--
-- Maps Supabase auth.uid()::text to learner_profiles.id and all dependent
-- user-scoped tables.
-- =============================================================================

-- Enable RLS on user-specific tables
ALTER TABLE learner_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE learner_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE learner_roadmap_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE learning_history ENABLE ROW LEVEL SECURITY;
ALTER TABLE recommendations ENABLE ROW LEVEL SECURITY;
ALTER TABLE activity_log ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE roadmap_replans ENABLE ROW LEVEL SECURITY;

-- 1. learner_profiles
CREATE POLICY "Users can view own learner profile"
    ON learner_profiles FOR SELECT
    USING (id = auth.uid()::text);

CREATE POLICY "Users can insert own learner profile"
    ON learner_profiles FOR INSERT
    WITH CHECK (id = auth.uid()::text);

CREATE POLICY "Users can update own learner profile"
    ON learner_profiles FOR UPDATE
    USING (id = auth.uid()::text)
    WITH CHECK (id = auth.uid()::text);

-- 2. learner_skills
CREATE POLICY "Users can view own skills"
    ON learner_skills FOR SELECT
    USING (learner_id = auth.uid()::text);

CREATE POLICY "Users can insert/update own skills"
    ON learner_skills FOR ALL
    USING (learner_id = auth.uid()::text)
    WITH CHECK (learner_id = auth.uid()::text);

-- 3. learner_roadmap_nodes
CREATE POLICY "Users can view own roadmap nodes"
    ON learner_roadmap_nodes FOR SELECT
    USING (learner_id = auth.uid()::text);

CREATE POLICY "Users can manage own roadmap nodes"
    ON learner_roadmap_nodes FOR ALL
    USING (learner_id = auth.uid()::text)
    WITH CHECK (learner_id = auth.uid()::text);

-- 4. learning_history
CREATE POLICY "Users can view own learning history"
    ON learning_history FOR SELECT
    USING (learner_id = auth.uid()::text);

CREATE POLICY "Users can manage own learning history"
    ON learning_history FOR ALL
    USING (learner_id = auth.uid()::text)
    WITH CHECK (learner_id = auth.uid()::text);

-- 5. recommendations
CREATE POLICY "Users can view own recommendations"
    ON recommendations FOR SELECT
    USING (learner_id = auth.uid()::text);

CREATE POLICY "Users can manage own recommendations"
    ON recommendations FOR ALL
    USING (learner_id = auth.uid()::text)
    WITH CHECK (learner_id = auth.uid()::text);

-- 6. activity_log
CREATE POLICY "Users can view own activity log"
    ON activity_log FOR SELECT
    USING (learner_id = auth.uid()::text);

CREATE POLICY "Users can insert own activity log"
    ON activity_log FOR INSERT
    WITH CHECK (learner_id = auth.uid()::text);

-- 7. assessment_results
CREATE POLICY "Users can view own assessment results"
    ON assessment_results FOR SELECT
    USING (learner_id = auth.uid()::text);

CREATE POLICY "Users can insert own assessment results"
    ON assessment_results FOR INSERT
    WITH CHECK (learner_id = auth.uid()::text);

-- 8. roadmap_replans
CREATE POLICY "Users can view own roadmap replans"
    ON roadmap_replans FOR SELECT
    USING (learner_id = auth.uid()::text);

-- Public / Catalog Tables (Readable by all authenticated and anon users)
ALTER TABLE skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE careers ENABLE ROW LEVEL SECURITY;
ALTER TABLE career_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE skill_prerequisites ENABLE ROW LEVEL SECURITY;
ALTER TABLE resources ENABLE ROW LEVEL SECURITY;
ALTER TABLE resource_skills ENABLE ROW LEVEL SECURITY;
ALTER TABLE roadmap_nodes ENABLE ROW LEVEL SECURITY;
ALTER TABLE roadmap_node_prerequisites ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessments ENABLE ROW LEVEL SECURITY;
ALTER TABLE assessment_questions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Public read skills" ON skills FOR SELECT USING (true);
CREATE POLICY "Public read careers" ON careers FOR SELECT USING (true);
CREATE POLICY "Public read career_skills" ON career_skills FOR SELECT USING (true);
CREATE POLICY "Public read skill_prerequisites" ON skill_prerequisites FOR SELECT USING (true);
CREATE POLICY "Public read resources" ON resources FOR SELECT USING (true);
CREATE POLICY "Public read resource_skills" ON resource_skills FOR SELECT USING (true);
CREATE POLICY "Public read roadmap_nodes" ON roadmap_nodes FOR SELECT USING (true);
CREATE POLICY "Public read roadmap_node_prerequisites" ON roadmap_node_prerequisites FOR SELECT USING (true);
CREATE POLICY "Public read assessments" ON assessments FOR SELECT USING (true);
CREATE POLICY "Public read assessment_questions" ON assessment_questions FOR SELECT USING (true);
