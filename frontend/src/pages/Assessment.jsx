import { useState } from 'react';
import { useParams, useNavigate, Link } from 'react-router-dom';
import { CheckCircle2, XCircle, ArrowRight, ArrowLeft } from 'lucide-react';
import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import { apiFetch } from '../api/client';
import { assessments, scoreAssessment } from '../data/assessmentData';
import './Assessment.css';

export default function Assessment() {
  const { id } = useParams();
  const navigate = useNavigate();
  const assessment = assessments[id];

  const [index, setIndex] = useState(0);
  const [answers, setAnswers] = useState({});
  const [submitted, setSubmitted] = useState(false);
  const [isReplanning, setIsReplanning] = useState(false);

  if (!assessment) {
    return (
      <EmptyState
        title="Assessment not found"
        description="This assessment isn't available yet."
        action={<Link to="/assessments" className="btn btn-secondary btn-sm">Back to assessments</Link>}
      />
    );
  }

  const question = assessment.questions[index];
  const total = assessment.questions.length;
  const answeredCount = Object.keys(answers).length;

  const selectAnswer = (optionId) => setAnswers((prev) => ({ ...prev, [question.id]: optionId }));

  const handleUpdateRoadmap = async (resultScore) => {
    setIsReplanning(true);
    
    // Construct the payload required by the backend /api/me/replan endpoint
    const signal = {
      step_id: assessment.id || id,
      target_skill_id: assessment.skill_id || assessment.skillId || id,
      score_percentage: resultScore,
      user_feedback: ""
    };

    try {
      const replanResult = await apiFetch('/api/me/replan', {
        method: 'POST',
        body: JSON.stringify(signal),
      });
      
      // Navigate to the adaptive replanning view with the AI's generated response
      navigate('/adaptive', { state: { aiResponse: replanResult } });
    } catch (error) {
      console.error("Failed to trigger AI adaptive replan:", error);
      // Fallback navigation in case backend call fails
      navigate('/adaptive');
    } finally {
      setIsReplanning(false);
    }
  };

  if (submitted) {
    const result = scoreAssessment(assessment, answers);
    return (
      <div className="assessment-page">
        <div className="assessment-result card">
          <span className="eyebrow">Result</span>
          <div className="assessment-result-score">{result.score}%</div>
          <p className="section-lede">{result.correctCount} of {result.total} correct on {assessment.title}.</p>

          {result.strengths.length > 0 && (
            <div className="assessment-result-block">
              <span className="eyebrow">Strong areas</span>
              <div className="assessment-result-tags">
                {result.strengths.map((s) => (
                  <span className="assessment-result-tag good" key={s}><CheckCircle2 size={13} /> {s}</span>
                ))}
              </div>
            </div>
          )}

          {result.weakAreas.length > 0 && (
            <div className="assessment-result-block">
              <span className="eyebrow">Needs reinforcement</span>
              <div className="assessment-result-tags">
                {result.weakAreas.map((s) => (
                  <span className="assessment-result-tag weak" key={s}><XCircle size={13} /> {s}</span>
                ))}
              </div>
            </div>
          )}

          <p className="assessment-result-next">{result.recommendedNext}</p>

          <div className="assessment-result-actions">
            <Button variant="secondary" onClick={() => navigate('/assessments')}>Back to assessments</Button>
            <Button 
              icon={ArrowRight} 
              onClick={() => handleUpdateRoadmap(result.score)}
              disabled={isReplanning}
            >
              {isReplanning ? 'AI Replanning...' : 'Update My Roadmap'}
            </Button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="assessment-page">
      <div className="assessment-progress-head">
        <span className="eyebrow">{assessment.title}</span>
        <span className="data-label">{answeredCount} / {total} answered</span>
      </div>
      <div className="assessment-progress-track">
        <div style={{ width: `${((index + 1) / total) * 100}%` }} />
      </div>

      <div className="assessment-nav-dots">
        {assessment.questions.map((q, i) => (
          <button
            key={q.id}
            className={`assessment-nav-dot ${i === index ? 'active' : ''} ${answers[q.id] ? 'answered' : ''}`}
            onClick={() => setIndex(i)}
            aria-label={`Go to question ${i + 1}`}
            type="button"
          >
            {i + 1}
          </button>
        ))}
      </div>

      <div className="card assessment-question-card">
        <span className="data-label">Question {index + 1} of {total}</span>
        <h2 className="assessment-question-prompt">{question.prompt}</h2>
        <div className="assessment-options">
          {question.options.map((opt) => (
            <button
              key={opt.id}
              className={`assessment-option ${answers[question.id] === opt.id ? 'selected' : ''}`}
              onClick={() => selectAnswer(opt.id)}
              type="button"
            >
              {opt.text}
            </button>
          ))}
        </div>
      </div>

      <div className="assessment-footer">
        <Button variant="ghost" icon={ArrowLeft} iconPosition="left" onClick={() => setIndex((i) => Math.max(0, i - 1))} disabled={index === 0}>
          Previous
        </Button>
        {index < total - 1 ? (
          <Button icon={ArrowRight} onClick={() => setIndex((i) => i + 1)} disabled={!answers[question.id]}>
            Next
          </Button>
        ) : (
          <Button onClick={() => setSubmitted(true)} disabled={answeredCount < total}>
            Submit
          </Button>
        )}
      </div>
    </div>
  );
}