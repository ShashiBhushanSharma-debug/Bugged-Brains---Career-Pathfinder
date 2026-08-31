import { ClipboardCheck, ArrowRight, CheckCircle2 } from 'lucide-react';
import Button from './Button';
import './AssessmentCard.css';

export default function AssessmentCard({ assessment, onStart, completedScore }) {
  const isCompleted = completedScore !== undefined;

  return (
    <div className="assessment-card">
      <span className="assessment-card-icon">
        {isCompleted ? <CheckCircle2 size={20} strokeWidth={2} /> : <ClipboardCheck size={20} strokeWidth={2} />}
      </span>
      <div className="assessment-card-body">
        <h3>{assessment.title}</h3>
        <div className="assessment-card-meta">
          <span className="data-label">{assessment.skill}</span>
          <span className="data-label">{assessment.questionCount ?? assessment.questions?.length} questions</span>
          <span className="data-label">{assessment.estimatedTime}</span>
        </div>
        {assessment.unlocksIfPassed && (
          <p className="assessment-card-unlocks">Unlocks: {assessment.unlocksIfPassed}</p>
        )}
      </div>
      <div className="assessment-card-action">
        {isCompleted ? (
          <span className="assessment-card-score">{completedScore}%</span>
        ) : (
          <Button variant="secondary" size="sm" icon={ArrowRight} onClick={onStart}>
            Start
          </Button>
        )}
      </div>
    </div>
  );
}