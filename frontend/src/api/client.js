/**
 * src/api/client.js
 *
 * Central HTTP utility for all backend calls.
 * Uses the Vite dev proxy (vite.config.js server.proxy) so relative /api/* paths
 * reach http://localhost:8000 in development without CORS issues.
 *
 * Phase 3: Automatically injects the Supabase auth access_token into every
 * request so the backend can verify the authenticated user.
 *
 * Performance & Data Isolation:
 * - Scopes in-memory GET cache keys by userId (${userId}:${method}:${path}) so
 *   data from User A can never leak to User B within the same browser session.
 * - In-flight request deduplication prevents duplicate concurrent round-trips.
 * - Automatic cache invalidation on any mutation (POST, PATCH, PUT, DELETE) and
 *   on user sign-out/switch.
 *
 * SECURITY: This file must NEVER contain database URLs, Supabase credentials,
 * or any secrets. All secrets live in backend/.env only.
 */
import { supabase } from './supabaseClient';

// In-memory cache for GET responses: key -> { timestamp, data }
const apiCache = new Map();
// In-flight promise tracker: key -> Promise
const inFlightRequests = new Map();
// Short TTL for cached GET requests (30 seconds)
const CACHE_TTL_MS = 30 * 1000;

/**
 * Clear the API client in-memory cache (e.g. on logout or user switch).
 */
export function clearApiCache() {
  apiCache.clear();
  inFlightRequests.clear();
}

/**
 * Fetch a JSON endpoint on the FastAPI backend with user-scoped caching and auth token injection.
 *
 * @param {string} path - Relative path, e.g. '/api/me'
 * @param {RequestInit} options - Standard fetch options (method, body, etc.)
 * @returns {Promise<any>} Parsed JSON response
 * @throws {Error} with message from FastAPI `detail` field or HTTP status
 */
export async function apiFetch(path, options = {}) {
  const method = (options.method || 'GET').toUpperCase();
  const isGet = method === 'GET';

  // Get current session and user ID for cache scoping & Bearer token
  const { data: { session } } = await supabase.auth.getSession();
  const userId = session?.user?.id ?? 'anon';
  const accessToken = session?.access_token;
  const cacheKey = `${userId}:${method}:${path}`;

  // If this is a mutation (POST, PATCH, PUT, DELETE), invalidate the cache
  if (!isGet) {
    apiCache.clear();
  } else {
    // Check if we have a fresh cached result for this specific user
    const cached = apiCache.get(cacheKey);
    if (cached && (Date.now() - cached.timestamp < CACHE_TTL_MS)) {
      return cached.data;
    }

    // Check if an identical GET request is currently in flight for this user
    if (inFlightRequests.has(cacheKey)) {
      return inFlightRequests.get(cacheKey);
    }
  }

  // Helper function to perform the actual network request
  const executeFetch = async () => {
    const headers = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    // Inject the Bearer token if we have a session
    if (accessToken) {
      headers['Authorization'] = `Bearer ${accessToken}`;
    }

    const res = await fetch(path, {
      ...options,
      headers,
    });

    if (!res.ok) {
      let message = `API error ${res.status}`;
      try {
        const body = await res.json();
        if (body?.detail) message = body.detail;
      } catch {
        // response body not JSON — keep generic message
      }
      throw new Error(message);
    }

    const data = await res.json();

    // Cache successful GET responses
    if (isGet) {
      apiCache.set(cacheKey, { timestamp: Date.now(), data });
    }

    return data;
  };

  if (isGet) {
    const promise = executeFetch().finally(() => {
      inFlightRequests.delete(cacheKey);
    });
    inFlightRequests.set(cacheKey, promise);
    return promise;
  }

  return executeFetch();
}
