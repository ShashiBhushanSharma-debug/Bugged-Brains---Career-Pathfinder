import { useState } from 'react';
import { useToast } from '../components/Toast';
import Button from '../components/Button';
import LoadingState from '../components/LoadingState';
import { useLearner } from '../hooks/useLearner';
import { apiFetch } from '../api/client';
import './Settings.css';

const NOTIF_LABELS = {
  roadmapUpdates: 'Roadmap updates',
  weeklyDigest: 'Weekly digest',
  assessmentReminders: 'Assessment reminders',
  productNews: 'Product news',
};

// Inner form: receives pre-loaded currentUser as a prop so useState can
// initialize directly from it — avoids setState-inside-useEffect pattern.
function SettingsForm({ currentUser }) {
  const showToast = useToast();
  const prefs = currentUser.learningPreferences ?? {};

  const [name, setName] = useState(currentUser.name ?? '');
  const [email] = useState('alex.rivera@example.com'); // no email field in API yet
  const [notifications, setNotifications] = useState(currentUser.notificationSettings ?? {});
  const [pace, setPace] = useState(prefs.pace ?? '');
  const [difficulty, setDifficulty] = useState(prefs.difficulty ?? '');
  const [saving, setSaving] = useState(false);

  const toggleNotif = (key) => setNotifications((prev) => ({ ...prev, [key]: !prev[key] }));

  const handleSave = async (e) => {
    e.preventDefault();
    setSaving(true);
    try {
      await apiFetch('/api/me', {
        method: 'PATCH',
        body: JSON.stringify({
          name,
          notification_settings: notifications,
          learning_preferences: { ...prefs, pace, difficulty },
        }),
      });
      showToast('Settings saved', { type: 'success' });
    } catch (err) {
      showToast(`Could not save: ${err.message}`, { type: 'error' });
    } finally {
      setSaving(false);
    }
  };

  return (
    <form className="settings-page" onSubmit={handleSave}>
      <div>
        <span className="eyebrow">Settings</span>
        <h1>Account &amp; preferences</h1>
      </div>

      <section className="card">
        <span className="eyebrow">Account</span>
        <div className="settings-field">
          <label htmlFor="name">Full name</label>
          <input id="name" value={name} onChange={(e) => setName(e.target.value)} />
        </div>
        <div className="settings-field">
          <label htmlFor="email">Email</label>
          <input id="email" type="email" value={email} readOnly />
        </div>
      </section>

      <section className="card">
        <span className="eyebrow">Learning preferences</span>
        <div className="settings-field">
          <label htmlFor="pace">Pace</label>
          <select id="pace" value={pace} onChange={(e) => setPace(e.target.value)}>
            <option>Relaxed (1–2 sessions / week)</option>
            <option>Steady (3–5 sessions / week)</option>
            <option>Intensive (daily)</option>
          </select>
        </div>
        <div className="settings-field">
          <label htmlFor="difficulty">Difficulty preference</label>
          <select id="difficulty" value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            <option>Keep it comfortable</option>
            <option>Push me slightly beyond current level</option>
            <option>Challenge me heavily</option>
          </select>
        </div>
      </section>

      <section className="card">
        <span className="eyebrow">Roadmap preferences</span>
        <p className="section-lede settings-note">
          Your roadmap adapts automatically after each assessment. Turn this off to review changes manually before they apply.
        </p>
        <label className="settings-toggle-row">
          <span>Auto-apply adaptive updates</span>
          <input type="checkbox" defaultChecked />
        </label>
      </section>

      <section className="card">
        <span className="eyebrow">Notifications</span>
        <div className="settings-toggle-list">
          {Object.entries(notifications).map(([key, value]) => (
            <label className="settings-toggle-row" key={key}>
              <span>{NOTIF_LABELS[key] ?? key}</span>
              <input type="checkbox" checked={!!value} onChange={() => toggleNotif(key)} />
            </label>
          ))}
        </div>
      </section>

      <div className="settings-actions">
        <Button type="submit" disabled={saving}>{saving ? 'Saving…' : 'Save changes'}</Button>
      </div>
    </form>
  );
}

// Outer shell: handles loading/error; renders SettingsForm once data is ready.
export default function Settings() {
  const { data: currentUser, loading, error } = useLearner();

  if (loading) return <LoadingState />;
  if (error) return <p className="section-lede" style={{ padding: '2rem' }}>Could not load settings: {error}</p>;
  if (!currentUser) return null;

  return <SettingsForm currentUser={currentUser} />;
}
