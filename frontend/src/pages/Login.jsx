import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { supabase } from '../api/supabaseClient';
import { useAuth } from '../contexts/AuthContext';
import GoogleIcon from '../components/GoogleIcon';
import './Auth.css';

export default function Login() {
  const navigate = useNavigate();
  const { user } = useAuth();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  // Redirect if already logged in
  if (user) {
    navigate('/dashboard', { replace: true });
    return null;
  }

  const handleEmailLogin = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const { error: authError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    navigate('/dashboard');
  };

  const handleGoogleLogin = async () => {
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
          <h1>Welcome back</h1>
          <p className="auth-subtitle">Sign in to continue your learning path.</p>

          {/* Google OAuth */}
          <button
            type="button"
            className="auth-google-btn"
            onClick={handleGoogleLogin}
            disabled={loading}
          >
            <GoogleIcon />
            Continue with Google
          </button>

          <div className="auth-divider"><span>or</span></div>

          {/* Email / Password */}
          <form className="auth-form" onSubmit={handleEmailLogin}>
            {error && <div className="auth-error">{error}</div>}

            <div className="auth-field">
              <label htmlFor="login-email">Email</label>
              <input
                id="login-email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                autoComplete="email"
              />
            </div>

            <div className="auth-field">
              <label htmlFor="login-password">Password</label>
              <input
                id="login-password"
                type="password"
                placeholder="Your password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                autoComplete="current-password"
              />
            </div>

            <Link to="/forgot-password" className="auth-forgot-link">
              Forgot password?
            </Link>

            <button type="submit" className="btn btn-primary" style={{ width: '100%' }} disabled={loading}>
              {loading ? 'Signing in…' : 'Sign in'}
            </button>
          </form>

          <div className="auth-footer">
            Don't have an account?{' '}
            <Link to="/signup">Sign up</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
