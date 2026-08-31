/**
 * src/hooks/useActivity.js
 *
 * Fetches recent activity from GET /api/me/activity.
 *
 * API returns ActivityLogItem[]: { id, type, label, meta, reference_id, occurred_at }
 * Dashboard timeAgo() uses item.timestamp — we map occurred_at -> timestamp.
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiFetch } from '../api/client';

export function useActivity(limit = 20) {
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
        const items = await apiFetch(`/api/me/activity?limit=${limit}`);
        if (!cancelled) {
          // Adapt occurred_at -> timestamp so Dashboard timeAgo() keeps working
          setData(
            items.map((a) => ({
              ...a,
              timestamp: a.occurred_at,
            }))
          );
        }
      } catch (err) {
        if (!cancelled) setError(err.message ?? 'Failed to load activity');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [user, authLoading, limit]);

  return { data: user ? data : null, loading: authLoading || (Boolean(user) && loading), error };
}
