/**
 * src/api/client.js
 *
 * Central HTTP utility for all backend calls.
 * Uses the Vite dev proxy (vite.config.js server.proxy) so relative /api/* paths
 * reach http://localhost:8000 in development without CORS issues.
 *
 * SECURITY: This file must NEVER contain database URLs, Supabase credentials,
 * or any secrets. All secrets live in backend/.env only.
 */

/**
 * Fetch a JSON endpoint on the FastAPI backend.
 *
 * @param {string} path  - Relative path, e.g. '/api/me'
 * @param {RequestInit} options - Standard fetch options (method, body, etc.)
 * @returns {Promise<any>} Parsed JSON response
 * @throws {Error} with message from FastAPI `detail` field or HTTP status
 */
export async function apiFetch(path, options = {}) {
  const res = await fetch(path, {
    headers: {
      'Content-Type': 'application/json',
      ...options.headers,
    },
    ...options,
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

  return res.json();
}
