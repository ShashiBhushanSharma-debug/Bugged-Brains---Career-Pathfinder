import './SkillCard.css';

export default function SkillCard({ skill, onClick }) {
  const { name, proficiency, required, status } = skill;
  const gap = Math.max(required - proficiency, 0);

  return (
    <button className="skill-card" onClick={onClick} type="button">
      <div className="skill-card-top">
        <span className={`dot dot-${status}`} aria-hidden="true" />
        <span className="skill-card-name">{name}</span>
        <span className="skill-card-pct data-label">{proficiency}%</span>
      </div>
      <div className="skill-card-bar" role="img" aria-label={`${name}: ${proficiency}% of ${required}% required`}>
        <div className="skill-card-bar-required" style={{ width: `${required}%` }} />
        <div className={`skill-card-bar-fill fill-${status}`} style={{ width: `${proficiency}%` }} />
      </div>
      <div className="skill-card-foot">
        <span className="data-label">Target {required}%</span>
        {gap > 0 && <span className="skill-card-gap">Gap {gap}%</span>}
        {gap === 0 && <span className="skill-card-met">Met</span>}
      </div>
    </button>
  );
}