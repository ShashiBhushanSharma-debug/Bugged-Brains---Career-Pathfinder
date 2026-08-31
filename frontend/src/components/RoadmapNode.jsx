import { forwardRef } from 'react';
import { Check, Lock, Zap, ArrowRight, BookOpen, Hammer, ClipboardCheck, GraduationCap } from 'lucide-react';
import './RoadmapNode.css';

const TYPE_ICON = {
  skill: GraduationCap,
  course: BookOpen,
  project: Hammer,
  assessment: ClipboardCheck,
};

const STATUS_ICON = {
  completed: Check,
  current: null,
  recommended: ArrowRight,
  locked: Lock,
  adapted: Zap,
};

const STATUS_LABEL = {
  completed: 'Completed',
  current: 'Current',
  recommended: 'Recommended next',
  locked: 'Locked',
  adapted: 'Adapted',
};

const RoadmapNode = forwardRef(function RoadmapNode({ node, onSelect, compact = false }, ref) {
  const TypeIcon = TYPE_ICON[node.type] || GraduationCap;
  const StatusIcon = STATUS_ICON[node.status];

  return (
    <button
      ref={ref}
      type="button"
      className={`roadmap-node status-${node.status} ${compact ? 'roadmap-node-compact' : ''}`}
      onClick={() => onSelect?.(node)}
      aria-label={`${node.title}, ${STATUS_LABEL[node.status]}`}
    >
      <span className="roadmap-node-station" aria-hidden="true">
        {StatusIcon ? <StatusIcon size={13} strokeWidth={2.75} /> : <span className="roadmap-node-pulse" />}
      </span>
      <span className="roadmap-node-type">
        <TypeIcon size={13} strokeWidth={2} />
        {node.type}
      </span>
      <span className="roadmap-node-title">{node.title}</span>
      <span className="roadmap-node-meta data-label">{node.duration} · {node.difficulty}</span>
      <span className={`roadmap-node-status status-${node.status}`}>{STATUS_LABEL[node.status]}</span>
    </button>
  );
});

export default RoadmapNode;