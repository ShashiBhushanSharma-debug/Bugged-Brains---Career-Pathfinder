import { useNavigate } from 'react-router-dom';
import { Flame, GraduationCap, Clock, Target, ArrowRight, Sparkles } from 'lucide-react';
import ProgressRing from '../components/ProgressRing';
import StatCard from '../components/StatCard';
import WhyThis from '../components/WhyThis';
import Button from '../components/Button';
import LoadingState from '../components/LoadingState';
import { useLearner } from '../hooks/useLearner';
import { useActivity } from '../hooks/useActivity';
import { useSkillAnalysis } from '../hooks/useSkillAnalysis';
import { useRoadmap } from '../hooks/useRoadmap';
import { upcomingAssessment } from '../data/assessmentData';
import './Dashboard.css';

function timeAgo(iso) {
  if (!iso) return '—';
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
  const { data: skillData } = useSkillAnalysis();
  const { nodes: roadmapNodes, replanReason } = useRoadmap();

  const hour = new Date().getHours();
  const greeting = hour < 12 ? 'Good morning' : hour < 18 ? 'Good afternoon' : 'Good evening';

  if (userLoading) return <LoadingState />;
  if (userError) return <p className="section-lede" style={{ padding: '2rem' }}>Could not load profile: {userError}</p>;
  if (!currentUser) return null;

  // Mastered skills derived dynamically from authenticated learner's skill analysis (0 for new users)
  const skillsMastered = skillData?.categories?.find((c) => c.id === 'known')?.skills?.length ?? 0;

  // Active developing / recommended skill derived dynamically from API
  const currentNode = roadmapNodes.find((n) => n.status === 'current')
    || roadmapNodes.find((n) => n.status === 'recommended');

  const developingSkill = skillData?.categories?.find((c) => c.id === 'developing')?.skills?.[0]
    || skillData?.categories?.find((c) => c.id === 'recommended')?.skills?.[0];

  const focusTitle = currentNode?.title
    || developingSkill?.name
    || (currentUser.targetRole ? `${currentUser.targetRole} Roadmap` : 'Set your career goal');

  const focusDesc = currentNode?.description
    || (developingSkill
      ? `Working toward ${developingSkill.required}% target proficiency (currently ${developingSkill.proficiency}%).`
      : (currentUser.targetRole
          ? `Explore resources and assessments sequenced for your ${currentUser.targetRole} path.`
          : 'Complete onboarding to generate your customized skill roadmap.'));

  // Only show replan banner if the user genuinely has an adaptive replan or assessment logged
  const replanEvent = recentActivity?.find((a) => a.type === 'roadmap' || a.type === 'assessment');
  const bannerHeadline = replanReason?.headline || replanEvent?.label;

  const displayName = currentUser.firstName || currentUser.name?.split(' ')[0] || 'there';

  return (
    <div className="dashboard">
      <div className="dashboard-head">
        <div>
          <h1>{greeting}, {displayName}.</h1>
          <p className="section-lede">
            Target: {currentUser.targetRole || 'Not selected yet'} {currentUser.currentLevel ? `· ${currentUser.currentLevel}` : ''}
          </p>
        </div>
        <Button icon={ArrowRight} onClick={() => navigate(currentUser.targetRole ? '/roadmap' : '/onboarding')}>
          {currentUser.targetRole ? 'View Roadmap' : 'Start Onboarding'}
        </Button>
      </div>

      {bannerHeadline && (
        <div className="dashboard-updated-banner" onClick={() => navigate('/adaptive')} role="button" tabIndex={0}>
          <Sparkles size={16} strokeWidth={2} />
          <span>Your learning path has been updated — {bannerHeadline}</span>
          <ArrowRight size={15} />
        </div>
      )}

      <div className="dashboard-grid">
        <div className="card dashboard-readiness">
          <ProgressRing value={currentUser.careerReadiness} sublabel="Readiness" size={104} />
          <div>
            <span className="eyebrow">Career readiness</span>
            <p className="dashboard-readiness-text">
              {currentUser.targetRole
                ? `You're ${currentUser.careerReadiness}% of the way to being ready for ${currentUser.targetRole} roles.`
                : 'Complete onboarding to calculate your personalized career readiness score.'}
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
            <h2 className="dashboard-focus-title">{focusTitle}</h2>
            <p className="section-lede">{focusDesc}</p>
            <Button size="sm" onClick={() => navigate(currentUser.targetRole ? '/learn' : '/onboarding')}>
              {currentUser.targetRole ? 'Continue learning' : 'Set your goal'}
            </Button>
          </section>

          {currentNode?.why?.length > 0 && <WhyThis reasons={currentNode.why} />}

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
            ) : (recentActivity ?? []).length === 0 ? (
              <p className="data-label" style={{ padding: '0.5rem 0', color: 'var(--ink-faint)' }}>
                No recent activity yet. Start learning or take an assessment to log your progress.
              </p>
            ) : (
              <ul className="dashboard-activity-list">
                {recentActivity.map((a) => (
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