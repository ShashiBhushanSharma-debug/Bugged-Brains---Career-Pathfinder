import { useState } from 'react';
import { Link, useNavigate, Navigate } from 'react-router-dom';
import { supabase } from '../api/supabaseClient';
import { useAuth } from '../contexts/AuthContext';
import GoogleIcon from '../components/GoogleIcon';
import LoadingState from '../components/LoadingState';
import './Auth.css';

export default function Signup() {
  const navigate = useNavigate();
  const { user, loading: authLoading } = useAuth();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);
  const [success, setSuccess] = useState(false);

  // If session is still initializing, show a brief loading state
  if (authLoading) {
    return (
      <div style={{ minHeight: '100vh', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <LoadingState rows={2} />
      </div>
    );
  }

  // Redirect if already logged in
  if (user) {
    return <Navigate to="/dashboard" replace />;
  }

  const handleSignup = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const { error: authError } = await supabase.auth.signUp({
      email,
      password,
      options: {
        emailRedirectTo: `${window.location.origin}/dashboard`,
        data: {
          full_name: fullName,
        },
      },
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    // If email confirmation is required, show success message.
    // If auto-confirm is enabled, redirect to onboarding.
    setSuccess(true);
    setLoading(false);

    // Small delay then redirect to onboarding (if session was created immediately)
    const { data: { session } } = await supabase.auth.getSession();
    if (session) {
      navigate('/onboarding');
    }
  };

  const handleGoogleSignup = async () => {
    setError('');
    const { error: authError } = await supabase.auth.signInWithOAuth({
      provider: 'google',
      options: {
        redirectTo: `${window.location.origin}/dashboard`,
      },
    });

    if (authError) {
      setError(authError.message);
    }
  };

  return (
    <div className="auth-page">
      <header className="auth-header">
        <Link to="/" className="auth-header-logo">
          <span className="auth-header-logo-mark">CP</span>
          Career Pathfinder
        </Link>
      </header>

      <div className="auth-body">
        <div className="auth-card">
          <h1>Create your account</h1>
          <p className="auth-subtitle">Start building your personalised learning path.</p>

          {/* Google OAuth */}
          <button
            type="button"
            className="auth-google-btn"
            onClick={handleGoogleSignup}
            disabled={loading}
          >
            <GoogleIcon />
            Continue with Google
          </button>

          <div className="auth-divider"><span>or</span></div>

          {/* Email / Password */}
          <form className="auth-form" onSubmit={handleSignup}>
            {error && <div className="auth-error">{error}</div>}
            {success && (
              <div className="auth-success">
                Account created! Check your email for a confirmation link, then sign in.
              </div>
            )}

            <div className="auth-field">
              <label htmlFor="signup-name">Full name</label>
              <input
                id="signup-name"
                type="text"
                placeholder="Alex Rivera"
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                required
                autoComplete="name"
              />
            </div>

            <div className="auth-field">
              <label htmlFor="signup-email">Email</label>
              <input
                id="signup-email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="auth-field">
              <label htmlFor="signup-password">Password</label>
              <input
                id="signup-password"
                type="password"
                placeholder="At least 6 characters"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={6}
                autoComplete="new-password"
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              style={{ width: '100%' }}
              disabled={loading || success}
            >
              {loading ? 'Creating account…' : 'Create account'}
            </button>
          </form>

          <div className="auth-footer">
            Already have an account?{' '}
            <Link to="/login">Sign in</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
