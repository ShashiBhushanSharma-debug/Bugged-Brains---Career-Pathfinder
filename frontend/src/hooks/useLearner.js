/**
 * src/hooks/useLearner.js
 *
 * Fetches the current learner profile from GET /api/me.
 * Also resolves the career display title via GET /api/careers/{id}.
 * Derives avatarInitials from the name field (not in the API response).
 *
 * Returns shape compatible with what userData.js currentUser provided,
 * so pages need minimal changes.
 */
import { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { apiFetch } from '../api/client';

function deriveInitials(name) {
  if (!name) return '??';
  const parts = name.trim().split(/\s+/);
  return parts.length >= 2
    ? (parts[0][0] + parts[1][0]).toUpperCase()
    : parts[0].slice(0, 2).toUpperCase();
}

export function useLearner() {
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

        // 1. Fetch learner profile
        const profile = await apiFetch('/api/me');

        // 2. Optionally resolve career title
        let careerTitle = profile.target_career_id ?? '';
        if (profile.target_career_id) {
          try {
            const career = await apiFetch(`/api/careers/${profile.target_career_id}`);
            if (career?.title) careerTitle = career.title;
          } catch {
            // Career lookup is best-effort; fall back to career_id
          }
        }

        if (!cancelled) {
          setData({
            // Raw API fields
            ...profile,
            // Derived / adapted fields for backward-compat with mock shape
            targetRole: careerTitle,
            firstName: profile.first_name ?? profile.name?.split(' ')[0] ?? '',
            avatarInitials: deriveInitials(profile.name),
            careerReadiness: profile.career_readiness ?? 0,
            overallProgress: profile.overall_progress ?? 0,
            streakDays: profile.streak_days ?? 0,
            weeklyLearningHours: profile.weekly_learning_hours ?? 0,
            totalLearningHours: profile.total_learning_hours ?? 0,
            currentLevel: profile.current_level ?? '',
            learningStyle: profile.learning_style ?? '',
            preferredSessionLength: profile.preferred_session_length ?? '',
            interests: profile.interests ?? [],
            learningPreferences: profile.learning_preferences ?? {},
            notificationSettings: profile.notification_settings ?? {},
            joinedAt: profile.joined_at ?? null,
          });
        }
      } catch (err) {
        if (!cancelled) setError(err.message ?? 'Failed to load profile');
      } finally {
        if (!cancelled) setLoading(false);
      }
    }

    load();
    return () => { cancelled = true; };
  }, [user, authLoading]);

  return { data: user ? data : null, loading: authLoading || (Boolean(user) && loading), error };
}
