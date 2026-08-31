/**
 * src/hooks/useRecommendations.js
 *
 * Fetches personalized recommendations from GET /api/recommendations.
 *
 * API RecommendationResponse:
 *   { learner_id, recommendations[], generated_at, is_engine_generated }
 *
 * RecommendationItem:
 *   { resource_id, resource_title, resource_type, target_skill_id,
 *     target_skill_name, score, reasoning, priority, difficulty,
 *     duration_text, score_breakdown }
 *
 * Returns: { data: { recommendations[], is_engine_generated, generated_at }, loading, error }
 * Also exposes recommendedIds: Set<string> for quick membership tests.
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiFetch } from '../api/client';

export function useRecommendations() {
  const { user, loading: authLoading } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    if (authLoading || !user) {
      return;
    }

    async function load() {
      try {
        setLoading(true);
        setError(null);
        const resp = await apiFetch('/api/recommendations');
        if (!cancelled) {
          const recommendations = resp.recommendations ?? [];
          setData({
            recommendations,
            is_engine_generated: resp.is_engine_generated,
            generated_at: resp.generated_at,
            // Convenience set for O(1) lookup at page level
            recommendedIds: new Set(recommendations.map((r) => r.resource_id)),
          });
        }
      } catch (err) {
        if (!cancelled) setError(err.message ?? 'Failed to load recommendations');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [user, authLoading]);

  return { data: user ? data : null, loading: authLoading || (Boolean(user) && loading), error };
}
