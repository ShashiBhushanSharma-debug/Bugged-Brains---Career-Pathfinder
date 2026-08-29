import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowRight } from 'lucide-react';
import ProgressRing from '../components/ProgressRing';
import SkillCard from '../components/SkillCard';
import WhyThis from '../components/WhyThis';
import Drawer from '../components/Drawer';
import Button from '../components/Button';
import LoadingState from '../components/LoadingState';
import { useSkillAnalysis } from '../hooks/useSkillAnalysis';
import './SkillAnalysis.css';

export default function SkillAnalysis() {
  const navigate = useNavigate();
  const [activeSkill, setActiveSkill] = useState(null);
  const { data, loading, error } = useSkillAnalysis();

  if (loading) return <LoadingState />;
  if (error) return <p className="section-lede" style={{ padding: '2rem' }}>Could not load skill analysis: {error}</p>;
  if (!data) return null;

  const { categories, targetRole, careerReadiness } = data;

  return (
    <div className="skill-analysis">
      <div className="skill-analysis-head">
        <div>
          <span className="eyebrow">Target role: {targetRole.title}</span>
          <h1>Skill Gap Analysis</h1>
          <p className="section-lede">{targetRole.description}</p>
        </div>
        <div className="skill-analysis-readiness card">
          <ProgressRing value={careerReadiness} sublabel="Readiness" size={92} />
        </div>
      </div>

      {categories.map((cat) => {
        const catSkills = cat.skills ?? [];
        if (!catSkills.length) return null;
        return (
          <section className="skill-analysis-section" key={cat.id}>
            <div className="skill-analysis-section-head">
              <h2>{cat.label}</h2>
              <p className="data-label">{cat.description}</p>
            </div>
            <div className="skill-analysis-grid">
              {catSkills.map((skill) => (
                <SkillCard key={skill.id} skill={skill} onClick={() => setActiveSkill(skill)} />
              ))}
            </div>
          </section>
        );
      })}

      <div className="skill-analysis-cta">
        <p>Ready to see how these skills sequence into a full path?</p>
        <Button icon={ArrowRight} onClick={() => navigate('/roadmap')}>View My Roadmap</Button>
      </div>

      <Drawer
        open={!!activeSkill}
        onClose={() => setActiveSkill(null)}
        eyebrow={activeSkill ? `${activeSkill.proficiency}% of ${activeSkill.required}% required` : ''}
        title={activeSkill?.name ?? ''}
      >
        {activeSkill && (
          <>
            <div className="skill-drawer-bar">
              <div className="skill-drawer-bar-track">
                <div
                  className={`skill-drawer-bar-fill fill-${activeSkill.status}`}
                  style={{ width: `${activeSkill.proficiency}%` }}
                />
                <div className="skill-drawer-bar-target" style={{ left: `${activeSkill.required}%` }} />
              </div>
              <div className="skill-drawer-bar-labels">
                <span className="data-label">Current {activeSkill.proficiency}%</span>
                <span className="data-label">Target {activeSkill.required}%</span>
              </div>
            </div>
            <WhyThis title="Gap detected because" reasons={activeSkill.reasoning ?? []} />
          </>
        )}
      </Drawer>
    </div>
  );
}
