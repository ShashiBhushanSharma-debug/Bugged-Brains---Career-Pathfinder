import { Link } from 'react-router-dom';
import { BookOpen, Video, FileText, FileCode2, Hammer, PenTool, ChevronRight, Lock } from 'lucide-react';
import './ResourceCard.css';

const TYPE_ICON = {
  course: BookOpen,
  video: Video,
  article: FileText,
  documentation: FileCode2,
  project: Hammer,
  practice: PenTool,
};

export default function ResourceCard({ resource }) {
  const Icon = TYPE_ICON[resource.type] || BookOpen;
  const locked = resource.status === 'locked';
  const Wrapper = locked ? 'div' : Link;
  const wrapperProps = locked ? {} : { to: `/resources/${resource.id}` };

  return (
    <Wrapper className={`resource-row ${locked ? 'locked' : ''}`} {...wrapperProps}>
      <span className="resource-row-icon">
        {locked ? <Lock size={16} strokeWidth={2} /> : <Icon size={16} strokeWidth={2} />}
      </span>
      <div className="resource-row-main">
        <span className="resource-row-title">{resource.title}</span>
        <span className="resource-row-meta data-label">
          {resource.type} · {resource.skill} · {resource.difficulty} · {resource.duration}
        </span>
      </div>
      <div className="resource-row-progress">
        {resource.status !== 'locked' && resource.status !== 'not-started' && (
          <div className="resource-row-progress-bar">
            <div style={{ width: `${resource.progress}%` }} />
          </div>
        )}
        <span className={`resource-row-status status-${resource.status.replace('-', '')}`}>
          {resource.status.replace('-', ' ')}
        </span>
      </div>
      {!locked && <ChevronRight size={16} className="resource-row-chevron" />}
    </Wrapper>
  );
}