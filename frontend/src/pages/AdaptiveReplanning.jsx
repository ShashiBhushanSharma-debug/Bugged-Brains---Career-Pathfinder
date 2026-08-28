import { useLocation, useNavigate } from 'react-router-dom';
import { Sparkles, Plus, ArrowRight, CheckCircle2 } from 'lucide-react';
import Button from '../components/Button';
import RoadmapConnector from '../components/RoadmapConnector';
import EmptyState from '../components/EmptyState';
import './AdaptiveReplanning.css';

export default function AdaptiveReplanning() {
  const navigate = useNavigate();
  const location = useLocation();
  
  // Extract the LangGraph AI response passed from the Assessment page
  const aiResponse = location.state?.aiResponse;
  const roadmapData = aiResponse?.roadmap;

  // Fallback if the user navigates here directly without taking an assessment
  if (!roadmapData) {
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
  const changes = roadmapData.updated_steps
    .filter((step) => step.action_type !== 'retained')
    .map((step) => ({
      type: step.action_type === 'injected_remedial' ? 'added' : step.action_type,
      label: step.title,
      detail: step.rationale.why_now
    }));

  return (
    <div className="adaptive-page">
      <div className="adaptive-head">
        <span className="adaptive-badge"><Sparkles size={14} /> AI Adaptive Re-planning</span>
        <h1>{roadmapData.headline || aiResponse.headline}</h1>
        <p className="section-lede">{roadmapData.reasoning}</p>
        <p className="data-label">
          Target Mastery Updated: {(aiResponse.updated_mastery * 100).toFixed(0)}%
        </p>
      </div>

      <div className="adaptive-compare">
        {/* We focus entirely on the new AI-generated path rather than a side-by-side */}
        <div className="adaptive-path-col" style={{ width: '100%', maxWidth: '600px', margin: '0 auto' }}>
          <span className="eyebrow">Your Updated Learning Path</span>
          <div className="adaptive-path">
            {roadmapData.updated_steps.map((step, i) => {
              const isNewNode = step.action_type === 'injected_remedial' || step.action_type === 'added';
              return (
                <div key={step.node_id}>
                  <div className={`adaptive-node ${isNewNode ? 'new' : ''}`}>
                    {isNewNode ? <Plus size={14} strokeWidth={2.5} /> : <CheckCircle2 size={14} />}
                    {step.title}
                  </div>
                  {i < roadmapData.updated_steps.length - 1 && (
                    <RoadmapConnector variant={
                      roadmapData.updated_steps[i + 1].action_type === 'injected_remedial' ? 'added' : 'default'
                    } />
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>

      {changes.length > 0 && (
        <div className="adaptive-changes card">
          <span className="eyebrow">What changed and why</span>
          <ul className="adaptive-changes-list">
            {changes.map((c, index) => (
              <li key={`${c.label}-${index}`}>
                <span className={`adaptive-change-tag ${c.type}`}>
                  {c.type === 'injected_remedial' ? 'Targeted Review' : c.type}
                </span>
                <div>
                  <strong>{c.label}</strong>
                  <p>{c.detail}</p>
                </div>
              </li>
            ))}
          </ul>
        </div>
      )}

      <div className="adaptive-actions">
        <Button icon={ArrowRight} onClick={() => navigate('/roadmap')}>View Full Roadmap</Button>
        <Button variant="secondary" onClick={() => navigate('/dashboard')}>Back to Dashboard</Button>
      </div>
    </div>
  );
}