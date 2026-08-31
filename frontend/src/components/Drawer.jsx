import { useEffect } from 'react';
import { X } from 'lucide-react';
import './Drawer.css';

export default function Drawer({ open, onClose, title, eyebrow, children }) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e) => e.key === 'Escape' && onClose?.();
    document.addEventListener('keydown', onKey);
    return () => document.removeEventListener('keydown', onKey);
  }, [open, onClose]);

  return (
    <div className={`drawer-overlay ${open ? 'open' : ''}`} onClick={onClose} aria-hidden={!open}>
      <div
        className={`drawer ${open ? 'open' : ''}`}
        role="dialog"
        aria-modal="true"
        aria-label={title}
        onClick={(e) => e.stopPropagation()}
      >
        <div className="drawer-head">
          <div>
            {eyebrow && <span className="eyebrow">{eyebrow}</span>}
            <h3>{title}</h3>
          </div>
          <button className="drawer-close" onClick={onClose} aria-label="Close panel">
            <X size={18} strokeWidth={2} />
          </button>
        </div>
        <div className="drawer-body">{children}</div>
      </div>
    </div>
  );
}