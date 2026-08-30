import { useNavigate } from 'react-router-dom';
import { Flame, GraduationCap, Clock, Target, ArrowRight, Sparkles } from 'lucide-react';
import ProgressRing from '../components/ProgressRing';
import StatCard from '../components/StatCard';
import WhyThis from '../components/WhyThis';
import Button from '../components/Button';
import LoadingState from '../components/LoadingState';
import { useLearner } from '../hooks/useLearner';
import { useActivity } from '../hooks/useActivity';
// roadmapData and assessmentData are intentionally kept as mock —
// no GET /api/roadmap or GET /api/assessments endpoint exists yet.
import { roadmapNodes, replanReason } from '../data/roadmapData';
import { upcomingAssessment } from '../data/assessmentData';
import './Dashboard.css';

function timeAgo(iso) {
  const diff = Date.now() - new Date(iso).getTime();
  const hrs = Math.floor(diff / 3600000);
  if (hrs < 1) return 'just now';
  if (hrs < 24) return `${hrs}h ago`;
  return `${Math.floor(hrs / 24)}d ago`;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const { data: currentUser, loading: userLoading, error: userError } = useLearner();
  const { data: recentActivity, loading: actLoading } = useActivity();

  const currentNode = roadmapNodes.find((n) => n.status === 'current');
  const skillsMastered = roadmapNodes.filter((n) => n.status === 'completed' && n.type === 'skill').length;
  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  if (userLoading) return <LoadingState />;
  if (userError) return <p className="section-lede" style={{ padding: '2rem' }}>Could not load profile: {userError}</p>;
  if (!currentUser) return null;

  return (
    <div className="dashboard">
      <div className="dashboard-head">
        <div>
          <h1>{greeting}, {currentUser.firstName}.</h1>
          <p className="section-lede">Target: {currentUser.targetRole} · {currentUser.currentLevel}</p>
        </div>
        <Button icon={ArrowRight} onClick={() => navigate('/roadmap')}>View Roadmap</Button>
      </div>

      <div className="dashboard-updated-banner" onClick={() => navigate('/adaptive')} role="button" tabIndex={0}>
        <Sparkles size={16} strokeWidth={2} />
        <span>Your learning path has been updated — {replanReason.reason}</span>
        <ArrowRight size={15} />
      </div>

      <div className="dashboard-grid">
        <div className="card dashboard-readiness">
          <ProgressRing value={currentUser.careerReadiness} sublabel="Readiness" size={104} />
          <div>
            <span className="eyebrow">Career readiness</span>
            <p className="dashboard-readiness-text">
              You're {currentUser.careerReadiness}% of the way to being ready for {currentUser.targetRole} roles.
            </p>
          </div>
        </div>

        <div className="card dashboard-readiness">
          <ProgressRing value={currentUser.overallProgress} sublabel="Roadmap" size={104} color="var(--amber)" />
          <div>
            <span className="eyebrow">Overall progress</span>
            <p className="dashboard-readiness-text">
              {currentUser.overallProgress}% of your personalized roadmap is complete.
            </p>
          </div>
        </div>
      </div>

      <div className="dashboard-stats">
        <StatCard icon={Flame} label="Day streak" value={currentUser.streakDays} accent="amber" />
        <StatCard icon={GraduationCap} label="Skills mastered" value={skillsMastered} accent="pine" />
        <StatCard icon={Clock} label="Hours learned" value={currentUser.totalLearningHours} accent="slate" />
        <StatCard icon={Target} label="Weekly goal" value={`${currentUser.weeklyLearningHours} hrs`} accent="rust" />
      </div>

      <div className="dashboard-columns">
        <div className="dashboard-main-col">
          <section className="card">
            <span className="eyebrow">Current focus</span>
            <h2 className="dashboard-focus-title">{currentNode?.title ?? currentUser.currentFocus?.label ?? 'Your roadmap'}</h2>
            <p className="section-lede">{currentNode?.description}</p>
            <Button size="sm" onClick={() => navigate('/learn')}>Continue learning</Button>
          </section>

          {currentNode?.why && <WhyThis reasons={currentNode.why} />}

          <section className="card">
            <div className="dashboard-section-head">
              <span className="eyebrow">Upcoming assessment</span>
            </div>
            <h3 className="dashboard-assessment-title">{upcomingAssessment.title}</h3>
            <p className="section-lede">
              {upcomingAssessment.questionCount} questions · {upcomingAssessment.estimatedTime}. Unlocks {upcomingAssessment.unlocksIfPassed}.
            </p>
            <Button variant="secondary" size="sm" onClick={() => navigate(`/assessment/${upcomingAssessment.id}`)}>
              Start assessment
            </Button>
          </section>
        </div>

        <aside className="dashboard-side-col">
          <section className="card">
            <span className="eyebrow">Recent activity</span>
            {actLoading ? (
              <p className="data-label" style={{ padding: '0.5rem 0' }}>Loading…</p>
            ) : (
              <ul className="dashboard-activity-list">
                {(recentActivity ?? []).map((a) => (
                  <li key={a.id}>
                    <span className="dashboard-activity-label">{a.label}</span>
                    <span className="data-label">{a.meta} · {timeAgo(a.timestamp)}</span>
                  </li>
                ))}
              </ul>
            )}
          </section>
        </aside>
      </div>
    </div>
  );
}