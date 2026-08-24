import { Link } from 'react-router-dom';
import { BookOpen, Video, FileText, FileCode2, Hammer, PenTool, Lock } from 'lucide-react';
import './CourseCard.css';

const TYPE_ICON = {
  course: BookOpen,
  video: Video,
  article: FileText,
  documentation: FileCode2,
  project: Hammer,
  practice: PenTool,
};

const STATUS_LABEL = {
  'not-started': 'Not started',
  'in-progress': 'In progress',
  completed: 'Completed',
  locked: 'Locked',
};

export default function CourseCard({ resource }) {
  const Icon = TYPE_ICON[resource.type] || BookOpen;
  const locked = resource.status === 'locked';

  const content = (
    <>
      <div className="course-card-top">
        <span className="course-card-type">
          <Icon size={14} strokeWidth={2} />
          {resource.type}
        </span>
        {resource.recommended && <span className="course-card-recommended">Recommended</span>}
      </div>
      <h3 className="course-card-title">{resource.title}</h3>
      <p className="course-card-desc">{resource.description}</p>
      <div className="course-card-meta">
        <span className="data-label">{resource.skill}</span>
        <span className="data-label">{resource.difficulty}</span>
        <span className="data-label">{resource.duration}</span>
      </div>
      {resource.status === 'in-progress' && (
        <div className="course-card-progress">
          <div className="course-card-progress-bar">
            <div style={{ width: `${resource.progress}%` }} />
          </div>
          <span className="data-label">{resource.progress}%</span>
        </div>
      )}
      <div className="course-card-foot">
        {locked ? (
          <span className="course-card-status locked"><Lock size={12} /> Locked</span>
        ) : (
          <span className={`course-card-status ${resource.status}`}>{STATUS_LABEL[resource.status]}</span>
        )}
      </div>
    </>
  );

  if (locked) {
    return <div className="course-card locked">{content}</div>;
  }

  return (
    <Link to={`/resources/${resource.id}`} className="course-card">
      {content}
    </Link>
  );
}