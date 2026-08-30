import { Flame, GraduationCap, Clock, ClipboardCheck, Hammer, TrendingUp } from 'lucide-react';
import StatCard from '../components/StatCard';
import ProgressRing from '../components/ProgressRing';
import LoadingState from '../components/LoadingState';
import { useLearner } from '../hooks/useLearner';
import { useSkillAnalysis } from '../hooks/useSkillAnalysis';
import { useLearningHistory } from '../hooks/useLearningHistory';
import { useActivity } from '../hooks/useActivity';
import './Progress.css';

export default function ProgressPage() {
  const { data: currentUser, loading: userLoading } = useLearner();
  const { data: skillData, loading: skillLoading } = useSkillAnalysis();
  const { data: historyData } = useLearningHistory('completed');
  const { data: recentActivity } = useActivity();

  if (userLoading || skillLoading) return <LoadingState />;
  if (!currentUser) return null;

  // Real user-scoped metrics
  const skillsMastered = skillData?.categories?.find((c) => c.id === 'known')?.skills?.length ?? 0;
  const projectsDone = (historyData?.items ?? []).filter((h) => h.type === 'project').length;
  const assessmentsDone = (recentActivity ?? []).filter((a) => a.type === 'assessment').length;

  const skills = skillData?.skills ?? [];

  return (
    <div className="progress-page">
      <div>
        <span className="eyebrow">Your progress</span>
        <h1>How far you've come</h1>
        <p className="section-lede">A running record of skills mastered, time invested and readiness gained.</p>
      </div>

      <div className="progress-rings card">
        <div className="progress-ring-block">
          <ProgressRing value={currentUser.overallProgress} sublabel="Roadmap" color="var(--amber)" />
          <span>Overall progress</span>
        </div>
        <div className="progress-ring-block">
          <ProgressRing value={currentUser.careerReadiness} sublabel="Readiness" />
          <span>Career readiness</span>
        </div>
      </div>

      <div className="progress-stats">
        <StatCard icon={GraduationCap} label="Skills mastered" value={skillsMastered} accent="pine" />
        <StatCard icon={Hammer} label="Projects completed" value={projectsDone} accent="amber" />
        <StatCard icon={ClipboardCheck} label="Assessments taken" value={assessmentsDone} accent="slate" />
        <StatCard icon={Clock} label="Hours learned" value={currentUser.totalLearningHours} accent="rust" />
        <StatCard icon={Flame} label="Day streak" value={currentUser.streakDays} accent="amber" />
        <StatCard icon={TrendingUp} label="Weekly pace" value={`${currentUser.weeklyLearningHours} hrs`} accent="pine" />
      </div>

      <section className="card">
        <span className="eyebrow">Skill proficiency over time</span>
        {skills.length === 0 ? (
          <p className="data-label" style={{ padding: '1rem 0', color: 'var(--ink-faint)' }}>
            No skill data recorded yet. Complete onboarding or assessments to track your proficiency progression.
          </p>
        ) : (
          <div className="progress-skill-bars">
            {skills.map((s) => (
              <div className="progress-skill-row" key={s.id}>
                <span className="progress-skill-name">{s.name}</span>
                <div className="progress-skill-track">
                  <div
                    className={`progress-skill-fill fill-${s.status}`}
                    style={{ width: `${s.proficiency}%` }}
                  />
                </div>
                <span className="data-label">{s.proficiency}%</span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}
