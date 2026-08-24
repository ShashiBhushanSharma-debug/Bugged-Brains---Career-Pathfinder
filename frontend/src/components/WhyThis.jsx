import { Check, Compass } from 'lucide-react';
import './WhyThis.css';

/**
 * The visible "explain yourself" panel. Every recommendation in the product
 * should be able to render one of these — it is the core trust mechanism
 * for an adaptive system that keeps changing the user's path.
 */
export default function WhyThis({ title = 'Why this?', reasons = [], compact = false }) {
  if (!reasons.length) return null;

  return (
    <div className={`why-this ${compact ? 'why-this-compact' : ''}`}>
      <div className="why-this-head">
        <Compass size={compact ? 15 : 17} strokeWidth={2} />
        <span>{title}</span>
      </div>
      <ul className="why-this-list">
        {reasons.map((reason, i) => (
          <li key={i}>
            <Check size={14} strokeWidth={2.5} />
            <span>{reason}</span>
          </li>
        ))}
      </ul>
    </div>
  );
}