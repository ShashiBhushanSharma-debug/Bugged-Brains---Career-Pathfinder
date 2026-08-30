import { useState } from 'react';
import { Pencil, Check } from 'lucide-react';
import SkillBadge from '../components/SkillBadge';
import Button from '../components/Button';
import LoadingState from '../components/LoadingState';
import { useToast } from '../components/Toast';
import { useLearner } from '../hooks/useLearner';
import { useSkillAnalysis } from '../hooks/useSkillAnalysis';
import { useLearningHistory } from '../hooks/useLearningHistory';
import { apiFetch } from '../api/client';
import './Profile.css';

export default function Profile() {
  const showToast = useToast();
  const [editing, setEditing] = useState(false);
  const [saving, setSaving] = useState(false);

  const { data: currentUser, loading: userLoading } = useLearner();
  const { data: skillData, loading: skillLoading } = useSkillAnalysis();
  const { data: historyData, loading: histLoading } = useLearningHistory('completed');

  const loading = userLoading || skillLoading || histLoading;

  // Controlled state — initialised once data arrives
  const [role, setRole] = useState('');
  const [interests, setInterests] = useState(null);

  // Sync controlled state when data loads (only on first load)
  if (currentUser && role === '' && !editing) {
    setRole(currentUser.targetRole ?? currentUser.target_career_id ?? '');
  }
  if (currentUser && interests === null && !editing) {
    setInterests(currentUser.interests ?? []);
  }

  const handleToggleEdit = async () => {
    if (editing) {
      // User is clicking "Save"
      setSaving(true);
      try {
        await apiFetch('/api/me', {
          method: 'PATCH',
          body: JSON.stringify({
            interests: interests ?? currentUser.interests ?? [],
          }),
        });
        showToast('Profile updated', { type: 'success' });
      } catch (err) {
        showToast(`Could not update profile: ${err.message}`, { type: 'error' });
      } finally {
        setSaving(false);
        setEditing(false);
      }
    } else {
      setEditing(true);
    }
  };

  if (loading) return <LoadingState />;
  if (!currentUser) return null;

  const skills = skillData?.skills ?? [];
  const completedHistory = historyData?.items ?? [];
  const displayInterests = interests ?? currentUser.interests ?? [];
  const prefs = currentUser.learningPreferences ?? {};

  return (
    <div className="profile-page">
      <div className="profile-head">
        <div className="profile-avatar">{currentUser.avatarInitials}</div>
        <div>
          <h1>{currentUser.name}</h1>
          <p className="data-label">
            Member since {currentUser.joinedAt
              ? new Date(currentUser.joinedAt).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })
              : '—'}
          </p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          icon={editing ? Check : Pencil}
          onClick={handleToggleEdit}
          disabled={saving}
        >
          {saving ? 'Saving…' : (editing ? 'Save' : 'Edit profile')}
        </Button>
      </div>

      <div className="profile-grid">
        <section className="card">
          <span className="eyebrow">Career goal</span>
          {editing ? (
            <input className="profile-input" value={role} onChange={(e) => setRole(e.target.value)} />
          ) : (
            <h2 className="profile-value">{role || currentUser.targetRole}</h2>
          )}
          <p className="data-label">Current level: {currentUser.currentLevel}</p>
        </section>

        <section className="card">
          <span className="eyebrow">Interests</span>
          <div className="profile-tags">
            {displayInterests.map((i) => (
              <span className="profile-tag" key={i}>
                {i}
                {editing && (
                  <button
                    onClick={() => setInterests((prev) => (prev ?? []).filter((x) => x !== i))}
                    aria-label={`Remove ${i}`}
                  >
                    ×
                  </button>
                )}
              </span>
            ))}
          </div>
        </section>

        <section className="card profile-span-2">
          <span className="eyebrow">Skills</span>
          <div className="profile-skills">
            {skills.map((s) => <SkillBadge key={s.id} name={s.name} status={s.status} showLabel />)}
          </div>
        </section>

        <section className="card">
          <span className="eyebrow">Completed learning</span>
          <ul className="profile-list">
            {completedHistory.length === 0 && (
              <li><span className="data-label">No completed items yet.</span></li>
            )}
            {completedHistory.map((h) => (
              <li key={h.id}>
                <span>{h.title}</span>
                <span className="data-label">
                  {h.type} · {h.completedAt ? new Date(h.completedAt).toLocaleDateString() : '—'}
                </span>
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <span className="eyebrow">Learning preferences</span>
          <ul className="profile-list">
            <li><span>Pace</span><span className="data-label">{prefs.pace ?? '—'}</span></li>
            <li><span>Difficulty</span><span className="data-label">{prefs.difficulty ?? '—'}</span></li>
            <li>
              <span>Format</span>
              <span className="data-label">
                {Array.isArray(prefs.format) ? prefs.format.join(', ') : prefs.format ?? '—'}
              </span>
            </li>
          </ul>
        </section>
      </div>
    </div>
  );
}
