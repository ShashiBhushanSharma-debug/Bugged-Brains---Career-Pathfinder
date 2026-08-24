import './SkillBadge.css';

const STATUS_LABEL = {
  completed: 'Completed',
  current: 'In progress',
  recommended: 'Recommended',
  locked: 'Locked',
  adapted: 'Adapted',
};

export default function SkillBadge({ name, status = 'locked', showLabel = false }) {
  return (
    <span className="skill-badge">
      <span className={`dot dot-${status}`} aria-hidden="true" />
      {name}
      {showLabel && <span className="skill-badge-status">· {STATUS_LABEL[status]}</span>}
    </span>
  );
}