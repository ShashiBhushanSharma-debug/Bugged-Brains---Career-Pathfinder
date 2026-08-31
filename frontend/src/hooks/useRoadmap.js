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
import { useAuth } from '../contexts/AuthContext';
import { apiFetch } from '../api/client';

export function useRoadmap() {
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
  }, [user, authLoading]);

  return {
    data: user ? data : null,
    nodes: user ? (data?.nodes ?? []) : [],
    replanReason: user ? (data?.replan_reason ?? null) : null,
    careerId: user ? (data?.career_id ?? null) : null,
    loading: authLoading || (Boolean(user) && loading),
    error,
  };
}
