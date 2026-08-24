import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, Clock, TrendingUp } from 'lucide-react';
import Roadmap from '../components/Roadmap';
import Drawer from '../components/Drawer';
import WhyThis from '../components/WhyThis';
import Button from '../components/Button';
import { roadmapNodes } from '../data/roadmapData';
import './RoadmapPage.css';

const LEGEND = [
  { status: 'completed', label: 'Completed' },
  { status: 'current', label: 'Current' },
  { status: 'recommended', label: 'Recommended next' },
  { status: 'locked', label: 'Locked' },
  { status: 'adapted', label: 'Adapted' },
];

export default function RoadmapPage() {
  const navigate = useNavigate();
  const [activeNode, setActiveNode] = useState(null);

  return (
    <div className="roadmap-page">
      <div className="roadmap-page-head">
        <div>
          <span className="eyebrow">Your personalized path</span>
          <h1>Learning Roadmap</h1>
          <p className="section-lede">
            Each stop is sequenced by prerequisite — click any node for the reasoning behind it.
          </p>
        </div>
        <Button variant="secondary" icon={Sparkles} onClick={() => navigate('/adaptive')}>
          View last update
        </Button>
      </div>

      <div className="roadmap-page-legend">
        {LEGEND.map((l) => (
          <span className="roadmap-page-legend-item" key={l.status}>
            <span className={`dot dot-${l.status}`} /> {l.label}
          </span>
        ))}
      </div>

      <Roadmap nodes={roadmapNodes} onSelectNode={setActiveNode} />

      <Drawer
        open={!!activeNode}
        onClose={() => setActiveNode(null)}
        eyebrow={activeNode?.type}
        title={activeNode?.title ?? ''}
      >
        {activeNode && (
          <>
            <p className="roadmap-drawer-desc">{activeNode.description}</p>

            <div className="roadmap-drawer-meta">
              <span><Clock size={14} strokeWidth={2} /> {activeNode.duration}</span>
              <span><TrendingUp size={14} strokeWidth={2} /> {activeNode.difficulty}</span>
            </div>

            <WhyThis reasons={activeNode.why} />

            {activeNode.skillsGained?.length > 0 && (
              <div className="roadmap-drawer-block">
                <span className="eyebrow">Skills gained</span>
                <ul className="roadmap-drawer-list">
                  {activeNode.skillsGained.map((s) => <li key={s}>{s}</li>)}
                </ul>
              </div>
            )}

            {activeNode.resources?.length > 0 && (
              <div className="roadmap-drawer-block">
                <span className="eyebrow">Resources</span>
                <ul className="roadmap-drawer-list">
                  {activeNode.resources.map((r) => <li key={r}>{r}</li>)}
                </ul>
              </div>
            )}

            {activeNode.expectedOutcome && (
              <div className="roadmap-drawer-block">
                <span className="eyebrow">Expected outcome</span>
                <p className="roadmap-drawer-desc">{activeNode.expectedOutcome}</p>
              </div>
            )}

            {activeNode.status !== 'locked' && activeNode.status !== 'completed' && (
              <Button onClick={() => navigate('/learn')}>
                {activeNode.type === 'assessment' ? 'Start assessment' : 'Go to resource'}
              </Button>
            )}
          </>
        )}
      </Drawer>
    </div>
  );
}