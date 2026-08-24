import { useState } from 'react';
import { Pencil, Check } from 'lucide-react';
import SkillBadge from '../components/SkillBadge';
import Button from '../components/Button';
import { currentUser } from '../data/userData';
import { skills } from '../data/skillsData';
import './Profile.css';

export default function Profile() {
  const [editing, setEditing] = useState(false);
  const [role, setRole] = useState(currentUser.targetRole);
  const [interests, setInterests] = useState(currentUser.interests);

  return (
    <div className="profile-page">
      <div className="profile-head">
        <div className="profile-avatar">{currentUser.avatarInitials}</div>
        <div>
          <h1>{currentUser.name}</h1>
          <p className="data-label">Member since {new Date(currentUser.joinedAt).toLocaleDateString('en-US', { month: 'long', year: 'numeric' })}</p>
        </div>
        <Button
          variant="secondary"
          size="sm"
          icon={editing ? Check : Pencil}
          onClick={() => setEditing((e) => !e)}
        >
          {editing ? 'Save' : 'Edit profile'}
        </Button>
      </div>

      <div className="profile-grid">
        <section className="card">
          <span className="eyebrow">Career goal</span>
          {editing ? (
            <input className="profile-input" value={role} onChange={(e) => setRole(e.target.value)} />
          ) : (
            <h2 className="profile-value">{role}</h2>
          )}
          <p className="data-label">Current level: {currentUser.currentLevel}</p>
        </section>

        <section className="card">
          <span className="eyebrow">Interests</span>
          <div className="profile-tags">
            {interests.map((i) => (
              <span className="profile-tag" key={i}>
                {i}
                {editing && (
                  <button onClick={() => setInterests((prev) => prev.filter((x) => x !== i))} aria-label={`Remove ${i}`}>×</button>
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
            {currentUser.learningHistory.map((h) => (
              <li key={h.id}>
                <span>{h.title}</span>
                <span className="data-label">{h.type} · {new Date(h.completedAt).toLocaleDateString()}</span>
              </li>
            ))}
          </ul>
        </section>

        <section className="card">
          <span className="eyebrow">Learning preferences</span>
          <ul className="profile-list">
            <li><span>Pace</span><span className="data-label">{currentUser.learningPreferences.pace}</span></li>
            <li><span>Difficulty</span><span className="data-label">{currentUser.learningPreferences.difficulty}</span></li>
            <li><span>Format</span><span className="data-label">{currentUser.learningPreferences.format.join(', ')}</span></li>
          </ul>
        </section>
      </div>
    </div>
  );
}