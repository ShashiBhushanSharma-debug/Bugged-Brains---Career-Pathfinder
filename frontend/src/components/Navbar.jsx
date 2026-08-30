import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Bell, LogOut } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import './Navbar.css';

/**
 * Derive avatar initials from the authenticated user.
 * Priority: user_metadata.full_name → email prefix → '?'
 */
function getInitials(user) {
  if (!user) return '?';
  const fullName = user.user_metadata?.full_name;
  if (fullName) {
    const parts = fullName.trim().split(/\s+/);
    return parts.length >= 2
      ? (parts[0][0] + parts[parts.length - 1][0]).toUpperCase()
      : parts[0].slice(0, 2).toUpperCase();
  }
  // Fallback to email
  const email = user.email || '';
  return email.slice(0, 2).toUpperCase();
}

export default function Navbar() {
  const navigate = useNavigate();
  const { user, signOut } = useAuth();
  const [notifOpen, setNotifOpen] = useState(false);
  const [menuOpen, setMenuOpen] = useState(false);

  const handleLogout = async () => {
    await signOut();
    navigate('/login');
  };

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

        {/* Avatar + dropdown menu */}
        <div className="navbar-avatar-wrapper">
          <button
            className="navbar-avatar"
            aria-label="Profile menu"
            aria-expanded={menuOpen}
            onClick={() => setMenuOpen((v) => !v)}
          >
            {getInitials(user)}
          </button>
          {menuOpen && (
            <div className="navbar-avatar-menu" role="menu">
              {user?.email && (
                <div className="navbar-avatar-menu-email">{user.email}</div>
              )}
              <button className="navbar-avatar-menu-item" role="menuitem" onClick={handleLogout}>
                <LogOut size={15} strokeWidth={2} />
                Sign out
              </button>
            </div>
          )}
        </div>
      </div>
    </header>
  );
}