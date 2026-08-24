import './RoadmapConnector.css';

/**
 * A single vertical "track" segment between two stops in a linear list —
 * used by the adaptive re-planning previous-vs-updated comparison, where a
 * full graph layout would be overkill.
 */
export default function RoadmapConnector({ variant = 'default' }) {
  return (
    <div className={`roadmap-connector roadmap-connector-${variant}`} aria-hidden="true">
      <span className="roadmap-connector-line" />
    </div>
  );
}