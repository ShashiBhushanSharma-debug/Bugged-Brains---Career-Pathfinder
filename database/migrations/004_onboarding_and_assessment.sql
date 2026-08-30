-- =============================================================================
-- Migration: 004_onboarding_and_assessment.sql
-- Project:   Career Pathfinder — Supabase PostgreSQL
-- Purpose:   Add onboarding_completed column to learner_profiles and ensure
--            clean default state for newly registered accounts.
-- =============================================================================

-- 1. Add onboarding_completed column if not present
ALTER TABLE learner_profiles
ADD COLUMN IF NOT EXISTS onboarding_completed BOOLEAN NOT NULL DEFAULT FALSE;

-- 2. Mark existing seeded development learner u_1001 as onboarded
UPDATE learner_profiles
SET onboarding_completed = TRUE
WHERE id = 'u_1001';

COMMENT ON COLUMN learner_profiles.onboarding_completed IS 'TRUE once the learner has completed the initial onboarding wizard.';
