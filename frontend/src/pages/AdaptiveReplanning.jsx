import { useLocation, useNavigate } from 'react-router-dom';
import { Sparkles, Plus, ArrowRight, CheckCircle2 } from 'lucide-react';
import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import { useRoadmap } from '../hooks/useRoadmap';
import './AdaptiveReplanning.css';

export default function AdaptiveReplanning() {
  const navigate = useNavigate();
  const location = useLocation();
  const { replanReason: savedReplan } = useRoadmap();
  
  // Extract the LangGraph AI response passed from the Assessment page, or fallback to saved DB replan
  const aiResponse = location.state?.aiResponse;
  const roadmapData = aiResponse?.roadmap;

  const headline = roadmapData?.headline || aiResponse?.headline || savedReplan?.headline;
  const reasoning = roadmapData?.reasoning || savedReplan?.reason;
  const updatedSteps = roadmapData?.updated_steps ?? [];
  const savedChanges = savedReplan?.changes ?? [];

  // If no replan data from live state or database
  if (!headline && !reasoning) {
    return (
      <div className="adaptive-page">
        <EmptyState
          title="No recent adaptations"
          description="Your roadmap is currently up to date. Take an assessment to trigger AI replanning."
          action={<Button onClick={() => navigate('/assessments')}>Go to Assessments</Button>}
        />
      </div>
    );
  }

  // Filter out normal 'retained' steps to explicitly show the user what the AI altered
  const changes = updatedSteps.length > 0
    ? updatedSteps
        .filter((step) => step.action_type !== 'retained')
        .map((step) => ({
          type: step.action_type === 'injected_remedial' ? 'added' : step.action_type,
          label: step.title,
          detail: step.rationale.why_now,
        }))
    : savedChanges;

  return (
    <div className="adaptive-page">
      <div className="adaptive-head">
        <span className="adaptive-badge"><Sparkles size={14} /> AI Adaptive Re-planning</span>
        <h1>{headline}</h1>
        <p className="section-lede">{reasoning}</p>
        {aiResponse?.updated_mastery != null && (
          <p className="data-label">
            Target Mastery Updated: {(aiResponse.updated_mastery * 100).toFixed(0)}%
          </p>
        )}
      </div>

      <div className="adaptive-compare">
        <div className="adaptive-path-col" style={{ width: '100%', maxWidth: '600px', margin: '0 auto' }}>
          <span className="eyebrow">Adjusted Steps</span>
          {changes.length > 0 ? (
            <div className="adaptive-changes">
              {changes.map((c, i) => (
                <div key={i} className="card" style={{ marginBottom: '1rem', padding: '1.25rem' }}>
                  <span className="eyebrow" style={{ color: 'var(--amber-ink)' }}>{c.type}</span>
                  <h3 style={{ margin: '0.25rem 0', fontSize: '1rem' }}>{c.label}</h3>
                  <p className="data-label">{c.detail || c.why}</p>
                </div>
              ))}
            </div>
          ) : (
            <div className="adaptive-path">
              {updatedSteps.map((step) => {
                const isNewNode = step.action_type === 'injected_remedial' || step.action_type === 'added';
                return (
                  <div key={step.node_id}>
                    <div className={`adaptive-node ${isNewNode ? 'new' : ''}`}>
                      {isNewNode ? <Plus size={14} strokeWidth={2.5} /> : <CheckCircle2 size={14} />}
                      {step.title}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <div style={{ marginTop: '2rem', textAlign: 'center' }}>
            <Button icon={ArrowRight} onClick={() => navigate('/roadmap')}>
              View Full Roadmap
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}