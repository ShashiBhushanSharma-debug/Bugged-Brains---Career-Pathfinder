import './LoadingState.css';

export default function LoadingState({ rows = 3, variant = 'lines' }) {
  if (variant === 'cards') {
    return (
      <div className="loading-cards">
        {Array.from({ length: rows }).map((_, i) => (
          <div className="loading-card skeleton" key={i} />
        ))}
      </div>
    );
  }

  return (
    <div className="loading-lines">
      {Array.from({ length: rows }).map((_, i) => (
        <div className="loading-line skeleton" key={i} style={{ width: `${100 - i * 12}%` }} />
      ))}
    </div>
  );
}