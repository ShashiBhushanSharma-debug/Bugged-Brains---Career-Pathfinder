/**
 * src/hooks/useRoadmap.js
 *
 * Fetches the authenticated learner's personalised roadmap from GET /api/roadmap.
 *
 * API Response:
 *   { career_id, nodes: RoadmapNodeItem[], replan_reason: RoadmapReplanInfo | null }
 *
 * Returns: { data, nodes, replanReason, careerId, loading, error }
 */
import { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';

export function useRoadmap() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      try {
        setLoading(true);
        setError(null);
        const resp = await apiFetch('/api/roadmap');
        if (!cancelled) {
          setData(resp);
        }
      } catch (err) {
        if (!cancelled) setError(err.message ?? 'Failed to load roadmap');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, []);

  return {
    data,
    nodes: data?.nodes ?? [],
    replanReason: data?.replan_reason ?? null,
    careerId: data?.career_id ?? null,
    loading,
    error,
  };
}
