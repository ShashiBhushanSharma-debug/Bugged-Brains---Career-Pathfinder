import './StatCard.css';

export default function StatCard({ icon: Icon, label, value, meta, accent = 'ink' }) {
  return (
    <div className="stat-card">
      <div className={`stat-card-icon accent-${accent}`}>
        {Icon && <Icon size={18} strokeWidth={2} />}
      </div>
      <div className="stat-card-body">
        <span className="stat-card-value">{value}</span>
        <span className="stat-card-label">{label}</span>
        {meta && <span className="stat-card-meta">{meta}</span>}
      </div>
    </div>
  );
}