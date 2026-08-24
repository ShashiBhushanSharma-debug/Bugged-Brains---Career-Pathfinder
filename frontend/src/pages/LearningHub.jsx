import { useMemo, useState } from 'react';
import { BookOpen } from 'lucide-react';
import CourseCard from '../components/CourseCard';
import EmptyState from '../components/EmptyState';
import { resources, resourceTypes } from '../data/coursesData';
import './LearningHub.css';

const FILTERS = ['all', ...resourceTypes];

export default function LearningHub() {
  const [filter, setFilter] = useState('all');

  const inProgress = resources.filter((r) => r.status === 'in-progress');
  const recommended = resources.filter((r) => r.recommended && r.status !== 'completed');

  const filtered = useMemo(
    () => (filter === 'all' ? resources : resources.filter((r) => r.type === filter)),
    [filter]
  );

  return (
    <div className="learning-hub">
      <div>
        <span className="eyebrow">Learning Hub</span>
        <h1>Everything queued up for you</h1>
        <p className="section-lede">Courses, videos, articles, projects and practice — sequenced by your roadmap.</p>
      </div>

      {inProgress.length > 0 && (
        <section>
          <h2 className="learning-hub-section-title">Continue learning</h2>
          <div className="learning-hub-grid">
            {inProgress.map((r) => <CourseCard key={r.id} resource={r} />)}
          </div>
        </section>
      )}

      {recommended.length > 0 && (
        <section>
          <h2 className="learning-hub-section-title">Recommended for you</h2>
          <div className="learning-hub-grid">
            {recommended.map((r) => <CourseCard key={r.id} resource={r} />)}
          </div>
        </section>
      )}

      <section>
        <div className="learning-hub-section-head">
          <h2 className="learning-hub-section-title">Browse all</h2>
          <div className="learning-hub-filters">
            {FILTERS.map((f) => (
              <button
                key={f}
                className={`learning-hub-filter ${filter === f ? 'active' : ''}`}
                onClick={() => setFilter(f)}
                type="button"
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {filtered.length === 0 ? (
          <EmptyState icon={BookOpen} title="Nothing here yet" description="Try a different filter." />
        ) : (
          <div className="learning-hub-grid">
            {filtered.map((r) => <CourseCard key={r.id} resource={r} />)}
          </div>
        )}
      </section>
    </div>
  );
}