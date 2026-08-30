import { useNavigate } from 'react-router-dom';
import AssessmentCard from '../components/AssessmentCard';
import EmptyState from '../components/EmptyState';
import { ClipboardCheck } from 'lucide-react';
import { assessments } from '../data/assessmentData';
import { useActivity } from '../hooks/useActivity';
import './Assessments.css';

export default function Assessments() {
  const navigate = useNavigate();
  const { data: recentActivity } = useActivity();
  const upcoming = Object.values(assessments);

  // Derive completed assessments from authenticated learner's activity log
  const completedEvents = (recentActivity ?? []).filter((a) => a.type === 'assessment');

  return (
    <div className="assessments-page">
      <div>
        <span className="eyebrow">Assessments</span>
        <h1>Check-ins that shape your path</h1>
        <p className="section-lede">Each result feeds directly back into your roadmap — no assessment is just a grade.</p>
      </div>

      <section>
        <h2 className="assessments-section-title">Available now</h2>
        <div className="assessments-list">
          {upcoming.map((a) => (
            <AssessmentCard key={a.id} assessment={a} onStart={() => navigate(`/assessment/${a.id}`)} />
          ))}
        </div>
      </section>

      <section>
        <h2 className="assessments-section-title">Completed</h2>
        {completedEvents.length === 0 ? (
          <EmptyState icon={ClipboardCheck} title="No assessments completed yet" description="Your first result will appear here." />
        ) : (
          <div className="assessments-list">
            {completedEvents.map((a) => (
              <div key={a.id} className="card assessment-card">
                <div>
                  <span className="eyebrow">Completed</span>
                  <h3 className="assessment-card-title">{a.label}</h3>
                  <p className="section-lede">{a.meta}</p>
                </div>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}