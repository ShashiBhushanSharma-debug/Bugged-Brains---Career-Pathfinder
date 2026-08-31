/**
 * src/hooks/useActivity.js
 *
 * Fetches recent activity from GET /api/me/activity.
 *
 * API returns ActivityLogItem[]: { id, type, label, meta, reference_id, occurred_at }
 * Dashboard timeAgo() uses item.timestamp — we map occurred_at -> timestamp.
 */
import { useState, useEffect } from 'react';
import { apiFetch } from '../api/client';

export function useActivity(limit = 20) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

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
  }, [limit]);

  return { data, loading, error };
}
