/**
 * src/hooks/useSkillAnalysis.js
 *
 * Fetches skill gap analysis from GET /api/skills/analysis.
 *
 * API returns SkillAnalysisResponse:
 *   { learner_id, career_id, career_title, categories[], all_gaps[], career_readiness_pct }
 *
 * categories[]: { id, label, description, skills[] }
 * skills[]:     { skill_id, name, proficiency_score, required_score, gap, status, importance }
 *
 * Adapts field names to match what skillsData.js provided:
 *   skill_id          -> id
 *   proficiency_score -> proficiency
 *   required_score    -> required
 *   (reasoning not in API — default to [])
 */
import { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';

function adaptSkill(s) {
  return {
    ...s,
    id: s.skill_id,
    proficiency: s.proficiency_score,
    required: s.required_score,
    category: null,   // filled in below when building flat list
    reasoning: [],    // not stored in DB — WhyThis falls back gracefully
  };
}

export function useSkillAnalysis() {
  const [data, setData] = useState(null);   // full SkillAnalysisResponse (adapted)
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);
        const resp = await apiFetch('/api/skills/analysis');

        if (!cancelled) {
          // Build adapted categories
          const categories = (resp.categories ?? []).map((cat) => ({
            id: cat.id,
            label: cat.label,
            description: cat.description,
            skills: (cat.skills ?? []).map((s) => ({ ...adaptSkill(s), category: cat.id })),
          }));

          // Build flat skills list (used by Profile and Progress)
          const skills = categories.flatMap((cat) => cat.skills);

          // targetRole shape matching skillsData.js
          const targetRole = {
            title: resp.career_title ?? '',
            description: '',
          };

          setData({
            ...resp,
            categories,
            skills,
            targetRole,
            careerReadiness: resp.career_readiness_pct ?? 0,
          });
        }
      } catch (err) {
        if (!cancelled) setError(err.message ?? 'Failed to load skill analysis');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  return { data, loading, error };
}
