import { useMemo, useState } from 'react';
import { BookOpen } from 'lucide-react';
import CourseCard from '../components/CourseCard';
import EmptyState from '../components/EmptyState';
import LoadingState from '../components/LoadingState';
import { useResources } from '../hooks/useResources';
import { useRecommendations } from '../hooks/useRecommendations';
import { useLearningHistory } from '../hooks/useLearningHistory';
import './LearningHub.css';

const RESOURCE_TYPES = ['course', 'video', 'article', 'documentation', 'project', 'practice'];
const FILTERS = ['all', ...RESOURCE_TYPES];

export default function LearningHub() {
  const [filter, setFilter] = useState('all');

  const { data: resourceData, loading: resLoading } = useResources();
  const { data: recData } = useRecommendations();
  const { data: historyData } = useLearningHistory();

  // Merge catalog + per-learner status + recommended flag
  const resources = useMemo(() => {
    if (!resourceData?.resources) return [];
    const historyMap = historyData?.historyByResourceId ?? {};
    const recIds = recData?.recommendedIds ?? new Set();
    const recByResourceId = {};
    (recData?.recommendations ?? []).forEach((r) => {
      recByResourceId[r.resource_id] = r;
    });

    return resourceData.resources.map((r) => {
      const hist = historyMap[r.id];
      const rec = recByResourceId[r.id];
      return {
        ...r,
        status: hist?.status ?? 'not-started',
        progress: hist?.progress ?? 0,
        recommended: recIds.has(r.id),
        whyRecommended: rec?.reasoning ?? r.whyRecommended ?? '',
        duration: r.duration_text ?? r.duration ?? '',
        skill: r.primary_skill_name ?? r.skill ?? '',
      };
    });
  }, [resourceData, recData, historyData]);

  // "Continue learning" — in-progress items from learning history merged with catalog
  const inProgress = useMemo(
    () => resources.filter((r) => r.status === 'in-progress'),
    [resources]
  );

  // "Recommended for you" — engine recommendations, excluding completed
  const recommended = useMemo(
    () => resources.filter((r) => r.recommended && r.status !== 'completed'),
    [resources]
  );

  const filtered = useMemo(
    () => (filter === 'all' ? resources : resources.filter((r) => r.type === filter)),
    [resources, filter]
  );

  if (resLoading) return <LoadingState />;

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
