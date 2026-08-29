/**
 * src/hooks/useResources.js
 *
 * Fetches the resource catalog from GET /api/resources.
 *
 * API ResourceResponse: { id, title, description, type, difficulty,
 *   duration_text, url, why_recommended_template, primary_skill_id,
 *   primary_skill_name, skill_ids[] }
 *
 * Adapts field names to match what coursesData.js resources[] provided:
 *   duration_text        -> duration
 *   primary_skill_name   -> skill
 *   why_recommended_template -> whyRecommended (baseline; overridden by engine reasoning)
 *
 * Per-learner fields (status, progress, recommended) are NOT in the catalog API.
 * Those come from useLearningHistory and useRecommendations — merged at page level.
 */
import { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';

export function useResources({ skillId, type } = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);

        const params = new URLSearchParams();
        if (skillId) params.set('skill_id', skillId);
        if (type) params.set('type', type);
        const qs = params.toString() ? `?${params.toString()}` : '';

        const resp = await apiFetch(`/api/resources${qs}`);
        if (!cancelled) {
          const resources = (resp.resources ?? []).map((r) => ({
            ...r,
            // Adapt field names to match existing page usage
            skill: r.primary_skill_name ?? '',
            duration: r.duration_text ?? '',
            whyRecommended: r.why_recommended_template ?? '',
            // Per-learner defaults (will be merged from history/recommendations)
            status: 'not-started',
            progress: 0,
            recommended: false,
          }));
          setData({ resources, total: resp.total ?? resources.length });
        }
      } catch (err) {
        if (!cancelled) setError(err.message ?? 'Failed to load resources');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [skillId, type]);

  return { data, loading, error };
}
