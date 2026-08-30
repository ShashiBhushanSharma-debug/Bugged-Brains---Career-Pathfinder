import { NavLink, useNavigate } from 'react-router-dom';
import {
  Compass, Map, Radar, GraduationCap, ClipboardCheck, TrendingUp, Library, User, Settings, LogOut,
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import './Sidebar.css';

const NAV_ITEMS = [
  { to: '/dashboard', label: 'Overview', icon: Compass },
  { to: '/roadmap', label: 'My Roadmap', icon: Map },
  { to: '/analysis', label: 'Skill Analysis', icon: Radar },
  { to: '/learn', label: 'Learn', icon: GraduationCap },
  { to: '/resources', label: 'Resources', icon: Library },
  { to: '/assessments', label: 'Assessments', icon: ClipboardCheck },
  { to: '/progress', label: 'Progress', icon: TrendingUp },
];

const BOTTOM_ITEMS = [
  { to: '/profile', label: 'Profile', icon: User },
  { to: '/settings', label: 'Settings', icon: Settings },
];

export default function Sidebar() {
  const navigate = useNavigate();
  const { signOut } = useAuth();

  const handleLogout = async () => {
    await signOut();
    navigate('/login');
  };

  return (
    <>
      <aside className="sidebar">
        <NavLink to="/dashboard" className="sidebar-logo">
          <span className="sidebar-logo-mark">CP</span>
          <span className="sidebar-logo-text">Career Pathfinder</span>
        </NavLink>

        <nav className="sidebar-nav" aria-label="Main navigation">
          {NAV_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <Icon size={17} strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>

        <nav className="sidebar-nav sidebar-nav-bottom" aria-label="Account navigation">
          {BOTTOM_ITEMS.map(({ to, label, icon: Icon }) => (
            <NavLink
              key={to}
              to={to}
              className={({ isActive }) => `sidebar-link ${isActive ? 'active' : ''}`}
            >
              <Icon size={17} strokeWidth={2} />
              <span>{label}</span>
            </NavLink>
          ))}
          <button className="sidebar-link sidebar-logout-btn" onClick={handleLogout}>
            <LogOut size={17} strokeWidth={2} />
            <span>Sign out</span>
          </button>
        </nav>
      </aside>

      <nav className="mobile-nav" aria-label="Main navigation">
        {[...NAV_ITEMS.slice(0, 4), BOTTOM_ITEMS[0]].map(({ to, label, icon: Icon }) => (
          <NavLink key={to} to={to} className={({ isActive }) => `mobile-nav-link ${isActive ? 'active' : ''}`}>
            <Icon size={19} strokeWidth={2} />
            <span>{label}</span>
          </NavLink>
        ))}
      </nav>
    </>
  );
}