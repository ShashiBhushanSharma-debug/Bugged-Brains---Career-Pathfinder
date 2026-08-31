/**
 * src/api/supabaseClient.js
 *
 * Initialises the Supabase client for authentication.
 *
 * SECURITY: Only the publishable/anon key is used here — never the
 * service-role key. The anon key is safe to include in client-side code.
 *
 * Set these in a `.env` file at the frontend root:
 *   VITE_SUPABASE_URL=https://olaxjoqrbuwehlopbpzq.supabase.co
 *   VITE_SUPABASE_ANON_KEY=your-anon-key-here
 */
import { createClient } from '@supabase/supabase-js';

const supabaseUrl = import.meta.env.VITE_SUPABASE_URL;
const supabaseAnonKey = import.meta.env.VITE_SUPABASE_ANON_KEY;

if (!supabaseUrl || !supabaseAnonKey) {
  console.warn(
    '[Career Pathfinder] VITE_SUPABASE_URL or VITE_SUPABASE_ANON_KEY is not set. ' +
    'Authentication will not work. Add these to frontend/.env.'
  );
}

export const supabase = createClient(
  supabaseUrl || '',
  supabaseAnonKey || '',
);
