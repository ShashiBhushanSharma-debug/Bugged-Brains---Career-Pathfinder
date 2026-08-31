/**
 * src/hooks/useLearningHistory.js
 *
 * Fetches the learner's resource progress history from GET /api/learning-history.
 *
 * API LearningHistoryItem:
 *   { id, learner_id, resource_id, title, type, status, progress_pct,
 *     completed_at, created_at, updated_at }
 *
 * Adapts progress_pct -> progress for backward-compat with coursesData.js usage.
 * Provides a historyByResourceId map for O(1) lookup when merging with resources.
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiFetch } from '../api/client';

export function useLearningHistory(status = null) {
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

        const qs = status ? `?status=${encodeURIComponent(status)}` : '';
        const resp = await apiFetch(`/api/learning-history${qs}`);

        if (!cancelled) {
          const items = (resp.items ?? []).map((item) => ({
            ...item,
            // Adapt progress_pct -> progress for existing component usage
            progress: item.progress_pct ?? 0,
            completedAt: item.completed_at ?? null,
          }));

          // Build resource_id -> item lookup map
          const historyByResourceId = {};
          items.forEach((item) => {
            if (item.resource_id) {
              historyByResourceId[item.resource_id] = item;
            }
          });

          setData({ items, total: resp.total ?? items.length, historyByResourceId });
        }
      } catch (err) {
        if (!cancelled) setError(err.message ?? 'Failed to load learning history');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [user, authLoading, status]);

  return { data: user ? data : null, loading: authLoading || (Boolean(user) && loading), error };
}
