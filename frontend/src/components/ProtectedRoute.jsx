/**
 * src/components/ProtectedRoute.jsx
 *
 * Route guard that:
 * 1. Redirects unauthenticated users to /login.
 * 2. Enforces the onboarding gate: if a user is authenticated but has not completed
 *    onboarding (no target career / onboarding_completed is false), redirects to /onboarding.
 * 3. Shows the LoadingState during initial session and profile checks.
 */
import { Navigate, Outlet, useLocation } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { useLearner } from '../hooks/useLearner';
import LoadingState from './LoadingState';

export default function ProtectedRoute() {
  const location = useLocation();
  const { user, loading: authLoading } = useAuth();
  const { data: currentUser, loading: learnerLoading } = useLearner();

  if (authLoading || (user && learnerLoading)) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <LoadingState rows={3} />
      </div>
    );
  }

  if (!user) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  // Onboarding gate: check if the user has completed onboarding
  const isOnboarded = Boolean(currentUser?.onboarding_completed || currentUser?.target_career_id);

  if (!isOnboarded && location.pathname !== '/onboarding') {
    return <Navigate to="/onboarding" replace />;
  }

  return <Outlet />;
}
