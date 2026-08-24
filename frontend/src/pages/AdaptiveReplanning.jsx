import { useNavigate } from 'react-router-dom';
import { Sparkles, Plus, ArrowRightLeft, ArrowRight } from 'lucide-react';
import Button from '../components/Button';
import RoadmapConnector from '../components/RoadmapConnector';
import {
  previousRoadmapPath, previousRoadmapLabels, updatedRoadmapPath, roadmapNodes, replanReason,
} from '../data/roadmapData';
import './AdaptiveReplanning.css';

const nodeLabel = (id) => roadmapNodes.find((n) => n.id === id)?.title ?? previousRoadmapLabels[id] ?? id;
const isNewNode = (id) => !previousRoadmapPath.includes(id);

export default function AdaptiveReplanning() {
  const navigate = useNavigate();

  return (
    <div className="adaptive-page">
      <div className="adaptive-head">
        <span className="adaptive-badge"><Sparkles size={14} /> Adaptive re-planning</span>
        <h1>{replanReason.headline}</h1>
        <p className="section-lede">{replanReason.reason}</p>
        <p className="data-label">Triggered by: {replanReason.triggeredBy}</p>
      </div>

      <div className="adaptive-compare">
        <div className="adaptive-path-col">
          <span className="eyebrow">Previously</span>
          <div className="adaptive-path">
            {previousRoadmapPath.map((id, i) => (
              <div key={id}>
                <div className="adaptive-node old">{nodeLabel(id)}</div>
                {i < previousRoadmapPath.length - 1 && <RoadmapConnector />}
              </div>
            ))}
          </div>
        </div>

        <div className="adaptive-compare-icon">
          <ArrowRightLeft size={20} strokeWidth={1.75} />
        </div>

        <div className="adaptive-path-col">
          <span className="eyebrow">Updated</span>
          <div className="adaptive-path">
            {updatedRoadmapPath.map((id, i) => (
              <div key={id}>
                <div className={`adaptive-node ${isNewNode(id) ? 'new' : ''}`}>
                  {isNewNode(id) && <Plus size={12} strokeWidth={2.5} />}
                  {nodeLabel(id)}
                </div>
                {i < updatedRoadmapPath.length - 1 && (
                  <RoadmapConnector variant={isNewNode(updatedRoadmapPath[i + 1]) ? 'added' : 'default'} />
                )}
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="adaptive-changes card">
        <span className="eyebrow">What changed</span>
        <ul className="adaptive-changes-list">
          {replanReason.changes.map((c) => (
            <li key={c.label}>
              <span className={`adaptive-change-tag ${c.type}`}>{c.type}</span>
              <div>
                <strong>{c.label}</strong>
                <p>{c.detail}</p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <div className="adaptive-actions">
        <Button icon={ArrowRight} onClick={() => navigate('/roadmap')}>View Full Roadmap</Button>
        <Button variant="secondary" onClick={() => navigate('/dashboard')}>Back to Dashboard</Button>
      </div>
    </div>
  );
}