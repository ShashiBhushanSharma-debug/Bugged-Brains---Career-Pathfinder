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
  const hasCareer = Boolean(targetRole?.title);
  const totalSkills = categories.reduce((sum, cat) => sum + (cat.skills?.length ?? 0), 0);

  return (
    <div className="skill-analysis">
      <div className="skill-analysis-head">
        <div>
          <span className="eyebrow">
            {hasCareer ? `Target role: ${targetRole.title}` : 'No target role selected'}
          </span>
          <h1>Skill Gap Analysis</h1>
          <p className="section-lede">
            {hasCareer
              ? targetRole.description || `Required skills and current gaps for ${targetRole.title}.`
              : 'Complete onboarding or set a target career in Profile to analyze your required skills and gaps.'}
          </p>
        </div>
        <div className="skill-analysis-readiness card">
          <ProgressRing value={careerReadiness} sublabel="Readiness" size={92} />
        </div>
      </div>

      {totalSkills === 0 ? (
        <div className="card" style={{ padding: '2.5rem', textAlign: 'center', margin: '2rem 0' }}>
          <p className="section-lede" style={{ marginBottom: '1.25rem' }}>
            No skill proficiencies mapped yet. Complete onboarding to customize your learning path.
          </p>
          <Button onClick={() => navigate('/onboarding')}>Start Onboarding</Button>
        </div>
      ) : (
        categories.map((cat) => {
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
        })
      )}

      {totalSkills > 0 && (
        <div className="skill-analysis-cta">
          <p>Ready to see how these skills sequence into a full path?</p>
          <Button icon={ArrowRight} onClick={() => navigate('/roadmap')}>View My Roadmap</Button>
        </div>
      )}

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
