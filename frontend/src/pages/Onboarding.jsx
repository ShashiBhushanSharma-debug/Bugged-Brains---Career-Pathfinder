import { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { ArrowLeft, ArrowRight, Search, X, Check } from 'lucide-react';
import Button from '../components/Button';
import { useAuth } from '../contexts/AuthContext';
import { apiFetch } from '../api/client';
import './Onboarding.css';

const STEPS = ['Goal', 'Current Skills', 'Interests', 'Experience', 'Learning History', 'Preferences'];

const ROLE_OPTIONS = ['Frontend Developer', 'Backend Developer', 'Full-Stack Developer', 'Data Analyst', 'UX Designer', 'Product Manager'];

const SKILL_LIBRARY = [
  'HTML', 'CSS', 'JavaScript', 'React', 'TypeScript', 'Node.js', 'Python',
  'SQL', 'Git', 'Testing', 'Accessibility', 'UI Design', 'Figma', 'REST APIs',
];

const INTEREST_OPTIONS = [
  'Web Development', 'UI Engineering', 'Design Systems', 'Accessibility',
  'Data Visualization', 'Mobile Apps', 'Developer Tools', 'AI/ML',
];

const EXPERIENCE_LEVELS = [
  { id: 'new', label: 'New to this', text: 'Little to no hands-on experience yet.' },
  { id: 'some', label: 'Some experience', text: 'Completed a few courses or small projects.' },
  { id: 'working', label: 'Working knowledge', text: 'Comfortable building small things on my own.' },
  { id: 'advancing', label: 'Advancing', text: 'Ready to go from foundational to job-ready.' },
];

const LEARNING_STYLES = [
  { id: 'project', label: 'Project-based', text: 'Learn by building real things.' },
  { id: 'video', label: 'Video-first', text: 'Prefer watching before doing.' },
  { id: 'reading', label: 'Reading & docs', text: 'Like working through written material.' },
  { id: 'mixed', label: 'A mix of everything', text: 'No strong preference — surprise me.' },
];

export default function Onboarding() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [step, setStep] = useState(0);
  const [submitError, setSubmitError] = useState('');
  const [submitting, setSubmitting] = useState(false);

  // Catalog lookups (loaded once)
  const [skillCatalog, setSkillCatalog] = useState([]);   // [{ id, name }]
  const [careerCatalog, setCareerCatalog] = useState([]); // [{ id, title }]

  useEffect(() => {
    // Load skill and career catalogs in parallel to build name->id maps
    apiFetch('/api/skills').then((items) => setSkillCatalog(items ?? [])).catch(() => {});
    apiFetch('/api/careers').then((items) => setCareerCatalog(items ?? [])).catch(() => {});
  }, []);

  const [targetRole, setTargetRole] = useState('');
  const [skillQuery, setSkillQuery] = useState('');
  const [selectedSkills, setSelectedSkills] = useState([]); // { name, proficiency }
  const [interests, setInterests] = useState([]);
  const [experienceLevel, setExperienceLevel] = useState('');
  const [weeklyHours, setWeeklyHours] = useState(6);
  const [historyInput, setHistoryInput] = useState('');
  const [historyItems, setHistoryItems] = useState([]);
  const [learningStyle, setLearningStyle] = useState('');

  const filteredSkills = SKILL_LIBRARY.filter(
    (s) => s.toLowerCase().includes(skillQuery.toLowerCase()) && !selectedSkills.some((sel) => sel.name === s)
  );

  const addSkill = (name) => {
    setSelectedSkills((prev) => [...prev, { name, proficiency: 40 }]);
    setSkillQuery('');
  };
  const removeSkill = (name) => setSelectedSkills((prev) => prev.filter((s) => s.name !== name));
  const setProficiency = (name, value) =>
    setSelectedSkills((prev) => prev.map((s) => (s.name === name ? { ...s, proficiency: value } : s)));

  const toggleInterest = (interest) =>
    setInterests((prev) => (prev.includes(interest) ? prev.filter((i) => i !== interest) : [...prev, interest]));

  const addHistoryItem = () => {
    if (!historyInput.trim()) return;
    setHistoryItems((prev) => [...prev, historyInput.trim()]);
    setHistoryInput('');
  };
  const removeHistoryItem = (item) => setHistoryItems((prev) => prev.filter((h) => h !== item));

  const canContinue = () => {
    if (step === 0) return targetRole !== '';
    if (step === 1) return selectedSkills.length > 0;
    if (step === 2) return interests.length > 0;
    if (step === 3) return experienceLevel !== '';
    return true;
  };

  // Build skill_id lookup from catalog; fall back to sanitised name if not found
  const resolveSkillId = (name) => {
    const match = skillCatalog.find(
      (s) => s.name?.toLowerCase() === name.toLowerCase()
    );
    return match?.id ?? null;
  };

  // Build career_id lookup from catalog
  const resolveCareerIdByTitle = (title) => {
    const match = careerCatalog.find(
      (c) => c.title?.toLowerCase() === title.toLowerCase()
    );
    return match?.id ?? null;
  };

  const handleFinalSubmit = async () => {
    setSubmitting(true);
    setSubmitError('');
    try {
      const skillsPayload = selectedSkills
        .map((s) => ({ skill_id: resolveSkillId(s.name), proficiency_score: s.proficiency }))
        .filter((s) => s.skill_id !== null); // only send skills we have IDs for

      const priorLearning = historyItems.map((title) => ({ title, type: 'course' }));

      const experienceLabelMap = {
        new: 'Beginner',
        some: 'Beginner–Intermediate',
        working: 'Intermediate',
        advancing: 'Intermediate–Advanced',
      };

      await apiFetch('/api/onboarding', {
        method: 'POST',
        body: JSON.stringify({
          learner_id: user?.id ?? 'anonymous', // auth.uid() — the backend will override this from the JWT
          name: user?.user_metadata?.full_name || user?.email?.split('@')[0] || targetRole,
          first_name: user?.user_metadata?.full_name?.split(' ')[0] || '',
          target_career_id: resolveCareerIdByTitle(targetRole),
          current_level: experienceLabelMap[experienceLevel] ?? experienceLevel,
          weekly_learning_hours: weeklyHours,
          interests,
          learning_style: learningStyle,
          learning_preferences: { pace: 'Steady (3–5 sessions / week)', difficulty: 'Push me slightly beyond current level' },
          skills: skillsPayload,
          prior_learning: priorLearning,
        }),
      });
      navigate('/dashboard');
    } catch (err) {
      setSubmitError(err.message ?? 'Could not save your profile. Please try again.');
      setSubmitting(false);
    }
  };

  const goNext = () => {
    if (step < STEPS.length - 1) {
      setStep((s) => s + 1);
    } else {
      handleFinalSubmit();
    }
  };
  const goBack = () => (step > 0 ? setStep((s) => s - 1) : navigate('/'));

  return (
    <div className="onboarding">
      <header className="onboarding-header">
        <span className="onboarding-logo">Career Pathfinder</span>
        <button className="onboarding-exit" onClick={() => navigate('/')}>Exit</button>
      </header>

      <div className="onboarding-progress">
        {STEPS.map((label, i) => (
          <div className={`onboarding-progress-step ${i === step ? 'active' : ''} ${i < step ? 'done' : ''}`} key={label}>
            <span className="onboarding-progress-num">{i < step ? <Check size={12} strokeWidth={3} /> : String(i + 1).padStart(2, '0')}</span>
            <span className="onboarding-progress-label">{label}</span>
          </div>
        ))}
      </div>

      <div className="onboarding-body">
        {step === 0 && (
          <section className="onboarding-step">
            <h2>What's your target career?</h2>
            <p className="section-lede">Pick the role you're aiming for — this drives every recommendation that follows.</p>
            <div className="onboarding-cards">
              {ROLE_OPTIONS.map((role) => (
                <button
                  key={role}
                  className={`onboarding-select-card ${targetRole === role ? 'selected' : ''}`}
                  onClick={() => setTargetRole(role)}
                  type="button"
                >
                  {role}
                </button>
              ))}
            </div>
          </section>
        )}

        {step === 1 && (
          <section className="onboarding-step">
            <h2>What skills do you already have?</h2>
            <p className="section-lede">Search and add skills, then set how confident you feel in each one.</p>
            <div className="onboarding-search">
              <Search size={16} strokeWidth={2} />
              <input
                type="text"
                placeholder="Search skills — JavaScript, SQL, Figma…"
                value={skillQuery}
                onChange={(e) => setSkillQuery(e.target.value)}
              />
            </div>
            {skillQuery && filteredSkills.length > 0 && (
              <div className="onboarding-suggestions">
                {filteredSkills.slice(0, 6).map((s) => (
                  <button key={s} className="onboarding-chip" onClick={() => addSkill(s)} type="button">
                    + {s}
                  </button>
                ))}
              </div>
            )}
            <div className="onboarding-skill-list">
              {selectedSkills.map((s) => (
                <div className="onboarding-skill-row" key={s.name}>
                  <span className="onboarding-skill-name">{s.name}</span>
                  <input
                    type="range"
                    min="0"
                    max="100"
                    value={s.proficiency}
                    onChange={(e) => setProficiency(s.name, Number(e.target.value))}
                    aria-label={`${s.name} proficiency`}
                  />
                  <span className="data-label onboarding-skill-pct">{s.proficiency}%</span>
                  <button aria-label={`Remove ${s.name}`} onClick={() => removeSkill(s.name)} type="button">
                    <X size={14} />
                  </button>
                </div>
              ))}
              {selectedSkills.length === 0 && <p className="onboarding-empty-hint">No skills added yet — search above to start.</p>}
            </div>
          </section>
        )}

        {step === 2 && (
          <section className="onboarding-step">
            <h2>What are you interested in?</h2>
            <p className="section-lede">Select as many as apply — these help shape future roadmap skills.</p>
            <div className="onboarding-tags">
              {INTEREST_OPTIONS.map((interest) => (
                <button
                  key={interest}
                  className={`onboarding-chip ${interests.includes(interest) ? 'selected' : ''}`}
                  onClick={() => toggleInterest(interest)}
                  type="button"
                >
                  {interest}
                </button>
              ))}
            </div>
          </section>
        )}

        {step === 3 && (
          <section className="onboarding-step">
            <h2>How would you describe your experience?</h2>
            <div className="onboarding-cards onboarding-cards-wide">
              {EXPERIENCE_LEVELS.map((level) => (
                <button
                  key={level.id}
                  className={`onboarding-select-card ${experienceLevel === level.id ? 'selected' : ''}`}
                  onClick={() => setExperienceLevel(level.id)}
                  type="button"
                >
                  <strong>{level.label}</strong>
                  <span>{level.text}</span>
                </button>
              ))}
            </div>
            <div className="onboarding-slider-block">
              <label htmlFor="weekly-hours">Weekly learning time available</label>
              <input
                id="weekly-hours"
                type="range"
                min="1"
                max="20"
                value={weeklyHours}
                onChange={(e) => setWeeklyHours(Number(e.target.value))}
              />
              <span className="data-label">{weeklyHours} hrs / week</span>
            </div>
          </section>
        )}

        {step === 4 && (
          <section className="onboarding-step">
            <h2>Any previous courses or projects?</h2>
            <p className="section-lede">Add anything relevant — we'll factor it into what's already covered.</p>
            <div className="onboarding-search">
              <input
                type="text"
                placeholder="e.g. Intro to Python, Portfolio site…"
                value={historyInput}
                onChange={(e) => setHistoryInput(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && (e.preventDefault(), addHistoryItem())}
              />
              <button type="button" className="onboarding-add-btn" onClick={addHistoryItem}>Add</button>
            </div>
            <div className="onboarding-tags">
              {historyItems.map((item) => (
                <span className="onboarding-chip selected" key={item}>
                  {item}
                  <button aria-label={`Remove ${item}`} onClick={() => removeHistoryItem(item)} type="button">
                    <X size={12} />
                  </button>
                </span>
              ))}
              {historyItems.length === 0 && <p className="onboarding-empty-hint">Optional — skip if this is your first step.</p>}
            </div>
          </section>
        )}

        {step === 5 && (
          <section className="onboarding-step">
            <h2>How do you like to learn?</h2>
            <div className="onboarding-cards onboarding-cards-wide">
              {LEARNING_STYLES.map((style) => (
                <button
                  key={style.id}
                  className={`onboarding-select-card ${learningStyle === style.id ? 'selected' : ''}`}
                  onClick={() => setLearningStyle(style.id)}
                  type="button"
                >
                  <strong>{style.label}</strong>
                  <span>{style.text}</span>
                </button>
              ))}
            </div>
            {submitError && (
              <p className="section-lede" style={{ color: 'var(--rust, #c0392b)', marginTop: '1rem' }}>
                {submitError}
              </p>
            )}
          </section>
        )}
      </div>

      <footer className="onboarding-footer">
        <Button variant="ghost" icon={ArrowLeft} iconPosition="left" onClick={goBack} disabled={submitting}>
          {step === 0 ? 'Back to home' : 'Back'}
        </Button>
        <Button icon={ArrowRight} onClick={goNext} disabled={!canContinue() || submitting}>
          {submitting ? 'Saving…' : step === STEPS.length - 1 ? 'Generate My Learning Path' : 'Continue'}
        </Button>
      </footer>
    </div>
  );
}
