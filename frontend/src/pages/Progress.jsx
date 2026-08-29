import { Flame, GraduationCap, Clock, ClipboardCheck, Hammer, TrendingUp } from 'lucide-react';
import StatCard from '../components/StatCard';
import ProgressRing from '../components/ProgressRing';
import LoadingState from '../components/LoadingState';
import { useLearner } from '../hooks/useLearner';
import { useSkillAnalysis } from '../hooks/useSkillAnalysis';
// roadmapData is intentionally kept — no GET /api/roadmap endpoint exists yet.
import { roadmapNodes } from '../data/roadmapData';
import './Progress.css';

export default function ProgressPage() {
  const { data: currentUser, loading: userLoading } = useLearner();
  const { data: skillData, loading: skillLoading } = useSkillAnalysis();

  // roadmap stats from mock (no API yet)
  const skillsMastered = roadmapNodes.filter((n) => n.status === 'completed' && n.type === 'skill').length;
  const projectsDone = roadmapNodes.filter((n) => n.status === 'completed' && n.type === 'project').length;
  const assessmentsDone = 1; // static until GET /api/assessments is implemented

  if (userLoading || skillLoading) return <LoadingState />;
  if (!currentUser) return null;

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
      </section>
    </div>
  );
}
