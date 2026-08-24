import { useMemo, useState } from 'react';
import { Library, Clock, BarChart3 } from 'lucide-react';
import ResourceCard from '../components/ResourceCard';
import Drawer from '../components/Drawer';
import WhyThis from '../components/WhyThis';
import Button from '../components/Button';
import EmptyState from '../components/EmptyState';
import { resources } from '../data/coursesData';
import './Resources.css';

const SKILLS = ['all', ...new Set(resources.map((r) => r.skill))];
const DIFFICULTIES = ['all', ...new Set(resources.map((r) => r.difficulty))];

export default function Resources() {
  const [skill, setSkill] = useState('all');
  const [difficulty, setDifficulty] = useState('all');
  const [onlyRecommended, setOnlyRecommended] = useState(false);
  const [activeResource, setActiveResource] = useState(null);

  const filtered = useMemo(() => {
    return resources.filter((r) => {
      if (skill !== 'all' && r.skill !== skill) return false;
      if (difficulty !== 'all' && r.difficulty !== difficulty) return false;
      if (onlyRecommended && !r.recommended) return false;
      return true;
    });
  }, [skill, difficulty, onlyRecommended]);

  return (
    <div className="resources-page">
      <div>
        <span className="eyebrow">Resource library</span>
        <h1>Resources</h1>
        <p className="section-lede">Every course, article, video and doc tied to your roadmap, filterable by skill and difficulty.</p>
      </div>

      <div className="resources-filters card">
        <div className="resources-filter-group">
          <span className="data-label">Skill</span>
          <select value={skill} onChange={(e) => setSkill(e.target.value)}>
            {SKILLS.map((s) => <option key={s} value={s}>{s === 'all' ? 'All skills' : s}</option>)}
          </select>
        </div>
        <div className="resources-filter-group">
          <span className="data-label">Difficulty</span>
          <select value={difficulty} onChange={(e) => setDifficulty(e.target.value)}>
            {DIFFICULTIES.map((d) => <option key={d} value={d}>{d === 'all' ? 'All levels' : d}</option>)}
          </select>
        </div>
        <label className="resources-filter-check">
          <input type="checkbox" checked={onlyRecommended} onChange={(e) => setOnlyRecommended(e.target.checked)} />
          Recommended only
        </label>
      </div>

      {filtered.length === 0 ? (
        <EmptyState icon={Library} title="No resources match" description="Try clearing a filter." />
      ) : (
        <div className="resources-list">
          {filtered.map((r) => (
            <div key={r.id} onClick={() => r.status !== 'locked' && setActiveResource(r)}>
              <ResourceCard resource={r} />
            </div>
          ))}
        </div>
      )}

      <Drawer
        open={!!activeResource}
        onClose={() => setActiveResource(null)}
        eyebrow={activeResource?.type}
        title={activeResource?.title ?? ''}
      >
        {activeResource && (
          <>
            <p className="resources-drawer-desc">{activeResource.description}</p>
            <div className="roadmap-drawer-meta">
              <span><Clock size={14} strokeWidth={2} /> {activeResource.duration}</span>
              <span><BarChart3 size={14} strokeWidth={2} /> {activeResource.difficulty}</span>
            </div>
            <WhyThis reasons={[activeResource.whyRecommended]} />
            <Button>{activeResource.status === 'completed' ? 'Review again' : 'Start Learning'}</Button>
          </>
        )}
      </Drawer>
    </div>
  );
}