/**
 * src/contexts/AuthContext.jsx
 *
 * React context providing Supabase auth state to the entire application.
 *
 * Exposes: { user, session, loading, signOut }
 *
 * - Subscribes to supabase.auth.onAuthStateChange() to persist session
 *   across page refreshes automatically.
 * - `loading` is true only during the initial session check so the
 *   ProtectedRoute can show a spinner instead of flashing the login page.
 */
/* eslint-disable react-refresh/only-export-components */
import { createContext, useContext, useEffect, useState } from 'react';
import { supabase } from '../api/supabaseClient';
import { clearApiCache } from '../api/client';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [session, setSession] = useState(null);
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // 1. Check for an existing session on mount
    supabase.auth.getSession().then(({ data: { session: currentSession } }) => {
      setSession(currentSession);
      setUser(currentSession?.user ?? null);
      setLoading(false);
    });

    // 2. Subscribe to auth state changes (login, logout, token refresh)
    const { data: { subscription } } = supabase.auth.onAuthStateChange(
      (_event, newSession) => {
        clearApiCache();
        setSession(newSession);
        setUser(newSession?.user ?? null);
        setLoading(false);
      }
    );

    return () => subscription.unsubscribe();
  }, []);

  const signOut = async () => {
    clearApiCache();
    await supabase.auth.signOut();
    setSession(null);
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, session, loading, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

/**
 * Hook to access auth state in any component.
 * @returns {{ user: object|null, session: object|null, loading: boolean, signOut: function }}
 */
export function useAuth() {
  const context = useContext(AuthContext);
  if (context === null) {
    throw new Error('useAuth must be used within an <AuthProvider>');
  }
  return context;
}
