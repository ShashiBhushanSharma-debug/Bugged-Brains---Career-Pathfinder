import { useState } from 'react';
import { Link } from 'react-router-dom';
import { supabase } from '../api/supabaseClient';
import './Auth.css';

export default function ForgotPassword() {
  const [email, setEmail] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState(false);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    const { error: authError } = await supabase.auth.resetPasswordForEmail(email, {
      redirectTo: `${window.location.origin}/login`,
    });

    if (authError) {
      setError(authError.message);
      setLoading(false);
      return;
    }

    setSuccess(true);
    setLoading(false);
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
          <h1>Reset your password</h1>
          <p className="auth-subtitle">
            Enter your email and we'll send you a link to reset your password.
          </p>

          <form className="auth-form" onSubmit={handleSubmit}>
            {error && <div className="auth-error">{error}</div>}
            {success && (
              <div className="auth-success">
                If an account exists for <strong>{email}</strong>, you'll receive a
                password reset link shortly. Check your inbox.
              </div>
            )}

            {!success && (
              <>
                <div className="auth-field">
                  <label htmlFor="reset-email">Email</label>
                  <input
                    id="reset-email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    required
                    autoComplete="email"
                  />
                </div>

                <button
                  type="submit"
                  className="btn btn-primary"
                  style={{ width: '100%' }}
                  disabled={loading}
                >
                  {loading ? 'Sending…' : 'Send reset link'}
                </button>
              </>
            )}
          </form>

          <div className="auth-footer">
            <Link to="/login">Back to sign in</Link>
          </div>
        </div>
      </div>
    </div>
  );
}
