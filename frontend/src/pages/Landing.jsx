import { useNavigate } from 'react-router-dom';
import {
  Radar, GitBranch, Route as RouteIcon, RefreshCcw, Compass, Sparkles,
  Target, TrendingUp, ShieldCheck, ArrowRight,
} from 'lucide-react';
import Button from '../components/Button';
import Roadmap from '../components/Roadmap';
import WhyThis from '../components/WhyThis';
import { roadmapNodes } from '../data/roadmapData';
import './Landing.css';

const HOW_IT_WORKS = [
  { icon: Target, title: 'Tell us your goal', text: 'Your target role, current skills, interests and learning history.' },
  { icon: Radar, title: 'We find the gap', text: 'Every skill you have is measured against what your goal actually requires.' },
  { icon: GitBranch, title: 'We map prerequisites', text: 'Skills are ordered by what unlocks what — not a generic course list.' },
  { icon: RouteIcon, title: 'You get a path', text: 'Courses, projects and assessments sequenced specifically for you.' },
  { icon: RefreshCcw, title: 'It keeps adapting', text: 'Every assessment and project reshapes what comes next.' },
];

const FEATURES = [
  { icon: Radar, title: 'Skill-gap intelligence', text: 'See exactly what separates you from your target role, skill by skill.' },
  { icon: GitBranch, title: 'Prerequisite-aware roadmap', text: 'Skills unlock in the right order — never learn something before its foundation.' },
  { icon: Compass, title: 'Explainable recommendations', text: 'Every course or project comes with a visible "why this?" reason.' },
  { icon: RefreshCcw, title: 'Adaptive re-planning', text: 'Assessment results reshape your path automatically, not manually.' },
  { icon: TrendingUp, title: 'Career readiness score', text: 'A single number that tracks how close you are to being job-ready.' },
  { icon: ShieldCheck, title: 'Built on your history', text: 'Past courses, projects and assessments all feed the plan — nothing wasted.' },
];

export default function Landing() {
  const navigate = useNavigate();

  return (
    <div className="landing">
      {/* Top nav */}
      <header className="landing-nav">
        <div className="landing-nav-inner">
          <span className="landing-logo">
            <span className="landing-logo-mark">CP</span>
            Career Pathfinder
          </span>
          <nav className="landing-nav-links">
            <a href="#how-it-works">How it works</a>
            <a href="#features">Features</a>
            <button className="landing-nav-login" onClick={() => navigate('/login')}>Log in</button>
            <Button size="sm" onClick={() => navigate('/signup')}>Build My Path</Button>
          </nav>
        </div>
      </header>

      {/* Hero */}
      <section className="landing-hero">
        <div className="landing-hero-copy">
          <span className="eyebrow">Adaptive learning, plotted like a route</span>
          <h1>
            Your career goal is unique.
            <br />
            Your learning path should be too.
          </h1>
          <p className="section-lede">
            Career Pathfinder reads your goal, your current skills and your learning history,
            finds exactly where the gaps are, and builds a prerequisite-aware roadmap of courses,
            projects and assessments — then keeps re-routing it as you learn.
          </p>
          <div className="landing-hero-actions">
            <Button icon={ArrowRight} onClick={() => navigate('/signup')}>Build My Learning Path</Button>
            <Button variant="secondary" as="a" href="#how-it-works">Explore How It Works</Button>
          </div>
          <div className="landing-hero-stats">
            <div><strong>10,400+</strong><span>learners routed</span></div>
            <div><strong>92%</strong><span>report clearer next steps</span></div>
            <div><strong>1</strong><span>path, always up to date</span></div>
          </div>
        </div>

        <div className="landing-hero-visual">
          <span className="eyebrow landing-hero-visual-label">Live preview — a real Career Pathfinder roadmap</span>
          <Roadmap nodes={roadmapNodes} compact onSelectNode={() => navigate('/signup')} />
        </div>
      </section>

      {/* How it works */}
      <section className="landing-section" id="how-it-works">
        <span className="eyebrow">How Career Pathfinder works</span>
        <h2 className="section-title">From goal to route in five steps</h2>
        <div className="landing-steps">
          {HOW_IT_WORKS.map((step, i) => (
            <div className="landing-step" key={step.title}>
              <span className="landing-step-index data-label">{String(i + 1).padStart(2, '0')}</span>
              <span className="landing-step-icon"><step.icon size={18} strokeWidth={2} /></span>
              <h3>{step.title}</h3>
              <p>{step.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Skill-gap intelligence */}
      <section className="landing-section landing-section-split">
        <div>
          <span className="eyebrow">Skill-gap intelligence</span>
          <h2 className="section-title">We don't guess what you need next</h2>
          <p className="section-lede">
            Career Pathfinder compares your current proficiency against what your target role
            actually requires — skill by skill — and shows the gap plainly instead of burying it
            in a generic course catalog.
          </p>
          <ul className="landing-checklist">
            <li>Current vs. required proficiency, per skill</li>
            <li>Skills grouped by known, developing, recommended and future</li>
            <li>A single career readiness score you can watch move</li>
          </ul>
        </div>
        <div className="landing-mini-bars card">
          {[
            { name: 'JavaScript', pct: 80 },
            { name: 'React', pct: 28 },
            { name: 'TypeScript', pct: 15 },
            { name: 'Testing', pct: 0 },
          ].map((s) => (
            <div className="landing-mini-bar-row" key={s.name}>
              <span className="data-label">{s.name}</span>
              <div className="landing-mini-bar-track">
                <div className="landing-mini-bar-fill" style={{ width: `${s.pct}%` }} />
              </div>
              <span className="data-label">{s.pct}%</span>
            </div>
          ))}
        </div>
      </section>

      {/* Adaptive roadmap concept */}
      <section className="landing-section landing-section-split reverse">
        <div className="landing-adapt-visual card">
          <span className="eyebrow">Before → after an assessment</span>
          <div className="landing-adapt-path">
            <span>React Fundamentals</span>
            <span className="landing-adapt-arrow">↓</span>
            <span className="landing-adapt-old">TypeScript</span>
            <span className="landing-adapt-arrow">↓</span>
            <span className="landing-adapt-old">Testing</span>
          </div>
          <div className="landing-adapt-path">
            <span>React Fundamentals</span>
            <span className="landing-adapt-arrow">↓</span>
            <span className="landing-adapt-new">State Management</span>
            <span className="landing-adapt-arrow">↓</span>
            <span className="landing-adapt-new">Mini Project</span>
            <span className="landing-adapt-arrow">↓</span>
            <span>TypeScript</span>
          </div>
        </div>
        <div>
          <span className="eyebrow">Adaptive roadmap concept</span>
          <h2 className="section-title">The path changes because you do</h2>
          <p className="section-lede">
            Every assessment result and completed project feeds back into your roadmap. Strong
            performance skips ahead; a detected gap inserts exactly the step needed to close it —
            automatically, with the reasoning shown.
          </p>
        </div>
      </section>

      {/* Explainability */}
      <section className="landing-section">
        <span className="eyebrow">"Why this?"</span>
        <h2 className="section-title">Every recommendation explains itself</h2>
        <div className="landing-why-demo">
          <WhyThis
            reasons={[
              'You have completed JavaScript fundamentals',
              'React is required for your target role',
              'Your current React proficiency is beginner',
              'It unlocks 4 future roadmap skills',
            ]}
          />
        </div>
      </section>

      {/* Example learner journey */}
      <section className="landing-section">
        <span className="eyebrow">Example learner journey</span>
        <h2 className="section-title">What a real route looks like</h2>
        <p className="section-lede">Maya wants to become a Frontend Developer. Here's how her path plotted itself.</p>
        <div className="landing-journey">
          {[
            { label: 'Onboarding', text: 'Goal: Frontend Developer. Knows HTML & CSS, beginner JavaScript.' },
            { label: 'Gap found', text: 'React, TypeScript and Testing are missing entirely.' },
            { label: 'Path built', text: 'JavaScript → React → State Management → TypeScript → Testing.' },
            { label: 'Assessment', text: 'Strong on React basics, gap in state management detected.' },
            { label: 'Path adapts', text: 'State Management + a mini project inserted automatically.' },
          ].map((step) => (
            <div className="landing-journey-step" key={step.label}>
              <span className="landing-journey-dot" />
              <div>
                <strong>{step.label}</strong>
                <p>{step.text}</p>
              </div>
            </div>
          ))}
        </div>
      </section>

      {/* Feature highlights */}
      <section className="landing-section" id="features">
        <span className="eyebrow">Feature highlights</span>
        <h2 className="section-title">Everything the path needs, nothing it doesn't</h2>
        <div className="landing-features-grid">
          {FEATURES.map((f) => (
            <div className="landing-feature-card card" key={f.title}>
              <span className="landing-feature-icon"><f.icon size={18} strokeWidth={2} /></span>
              <h3>{f.title}</h3>
              <p>{f.text}</p>
            </div>
          ))}
        </div>
      </section>

      {/* Final CTA */}
      <section className="landing-cta">
        <Sparkles size={22} strokeWidth={1.75} />
        <h2>Plot your path in the next five minutes.</h2>
        <p>No generic course list. A route, built around your goal and reshaped as you learn.</p>
        <Button size="lg" icon={ArrowRight} onClick={() => navigate('/signup')}>Build My Learning Path</Button>
      </section>

      {/* Footer */}
      <footer className="landing-footer">
        <span className="landing-logo">
          <span className="landing-logo-mark">CP</span>
          Career Pathfinder
        </span>
        <nav>
          <a href="#how-it-works">How it works</a>
          <a href="#features">Features</a>
          <a href="/signup" onClick={(e) => { e.preventDefault(); navigate('/signup'); }}>Get started</a>
        </nav>
        <span className="data-label">© {new Date().getFullYear()} Career Pathfinder</span>
      </footer>
    </div>
  );
}