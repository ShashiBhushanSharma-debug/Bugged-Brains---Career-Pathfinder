import { useState } from 'react';
import { Search, Bell } from 'lucide-react';
import { currentUser } from '../data/userData';
import './Navbar.css';

export default function Navbar() {
  const [notifOpen, setNotifOpen] = useState(false);

  return (
    <header className="navbar">
      <div className="navbar-search">
        <Search size={16} strokeWidth={2} />
        <input type="search" placeholder="Search skills, courses, resources…" aria-label="Search" />
      </div>

      <div className="navbar-actions">
        <button
          className="navbar-icon-btn"
          aria-label="Notifications"
          aria-expanded={notifOpen}
          onClick={() => setNotifOpen((v) => !v)}
        >
          <Bell size={18} strokeWidth={2} />
          <span className="navbar-notif-dot" />
        </button>
        {notifOpen && (
          <div className="navbar-notif-panel" role="dialog" aria-label="Notifications">
            <div className="navbar-notif-item">
              <strong>Your roadmap was updated</strong>
              <p>State Management was added after your latest assessment.</p>
            </div>
            <div className="navbar-notif-item">
              <strong>Assessment available</strong>
              <p>React Basics Check-in is ready — 10 min.</p>
            </div>
          </div>
        )}
        <button className="navbar-avatar" aria-label="Profile menu">
          {currentUser.avatarInitials}
        </button>
      </div>
    </header>
  );
}