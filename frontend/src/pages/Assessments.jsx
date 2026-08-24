import { useNavigate } from 'react-router-dom';
import AssessmentCard from '../components/AssessmentCard';
import EmptyState from '../components/EmptyState';
import { ClipboardCheck } from 'lucide-react';
import { assessments } from '../data/assessmentData';
import './Assessments.css';

const COMPLETED = [
  { id: 'as_js_fundamentals', title: 'JavaScript Fundamentals Assessment', skill: 'JavaScript', estimatedTime: '12 min', questionCount: 8, score: 88 },
];

export default function Assessments() {
  const navigate = useNavigate();
  const upcoming = Object.values(assessments);

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
        {COMPLETED.length === 0 ? (
          <EmptyState icon={ClipboardCheck} title="No assessments completed yet" description="Your first result will appear here." />
        ) : (
          <div className="assessments-list">
            {COMPLETED.map((a) => (
              <AssessmentCard key={a.id} assessment={a} completedScore={a.score} />
            ))}
          </div>
        )}
      </section>
    </div>
  );
}