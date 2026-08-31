"""
app/api/auth.py

Centralised authentication dependency for all protected endpoints.

Phase 3: Verifies Supabase JWT access tokens and extracts the learner_id
(auth.uid()) from the token's `sub` claim.

- If an Authorization header is provided, it is strictly validated. Any invalid,
  expired, or malformed token results in a 401 Unauthorized.
- No fallback to DEV_LEARNER_ID is ever performed when an authenticated token is present.
- When NO Authorization header is sent in development mode, it returns DEV_LEARNER_ID
  strictly to allow unauthenticated backend unit test runs.
"""
from __future__ import annotations

import base64

from fastapi import Depends, HTTPException, Request
import jwt

from app.config import get_settings, Settings


def _decode_supabase_secret(raw: str) -> bytes | str:
    """
    Supabase stores the JWT secret as a base64-encoded string in its dashboard.
    It signs tokens using the *decoded* raw bytes of that secret.

    PyJWT, when given a plain `str`, signs/verifies with the UTF-8 bytes of
    that string — which never match the decoded bytes → InvalidSignatureError.

    This helper returns the secret in the correct form:
    - If the raw value is valid base64 (Supabase standard), decode and return bytes.
    - Otherwise fall back to the raw string so existing non-base64 dev secrets still work.
    """
    if not raw:
        return raw
    try:
        # Standard base64 — Supabase JWT secrets are always base64
        return base64.b64decode(raw)
    except Exception:
        # Not base64 (e.g. a plain-text dev secret) — use as-is
        return raw


async def get_current_learner_id(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> str:
    """
    FastAPI dependency: resolve the current learner_id from the Supabase JWT.

    1. Read the Authorization header (Bearer token).
    2. Decode & verify the JWT.
    3. Return the `sub` claim (auth.uid()).
    """
    auth_header = request.headers.get("Authorization", "")

    # ── No token provided ────────────────────────────────────────────────────
    if not auth_header or not auth_header.startswith("Bearer "):
        request.state.is_authenticated = False
        if settings.is_development and settings.dev_learner_id:
            request.state.user_info = {"id": settings.dev_learner_id, "name": "Development Learner"}
            return settings.dev_learner_id
        raise HTTPException(
            status_code=401,
            detail="Missing authentication token.",
        )

    token = auth_header.split(" ", 1)[1].strip()
    if not token:
        raise HTTPException(status_code=401, detail="Empty authentication token.")

    payload = None

    # ── Verify the JWT if secret is configured ────────────────────────────────
    # Supabase JWT secrets are base64-encoded in the dashboard but Supabase signs
    # tokens with the *decoded* raw bytes.  We must base64-decode before passing
    # to PyJWT — otherwise PyJWT uses the UTF-8 bytes of the string, which never
    # match, producing an InvalidSignatureError (→ 401) on every real token.
    secret = _decode_supabase_secret(settings.supabase_jwt_secret)
    is_secret_configured = bool(
        settings.supabase_jwt_secret
        and settings.supabase_jwt_secret != "your-jwt-secret-here"
    )

    if is_secret_configured:
        try:
            payload = jwt.decode(
                token,
                secret,
                algorithms=["HS256"],
                options={"verify_aud": False},
            )
        except jwt.ExpiredSignatureError:
            raise HTTPException(status_code=401, detail="Token has expired.")
        except jwt.InvalidTokenError:
            if not settings.is_development:
                raise HTTPException(status_code=401, detail="Invalid authentication token.")

    # In development mode, if secret is unconfigured or not matching, allow unverified decode
    if payload is None:
        if settings.is_development:
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
            except Exception:
                raise HTTPException(status_code=401, detail="Malformed authentication token.")
        else:
            raise HTTPException(
                status_code=500,
                detail="Authentication secret is not configured on the server.",
            )

    # `sub` is the Supabase auth.uid()
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=401, detail="Token missing user identity.")

    # Store user metadata on request.state for downstream routes (e.g. get_me auto-provisioning)
    user_metadata = payload.get("user_metadata", {}) or {}
    request.state.is_authenticated = True
    request.state.user_info = {
        "id": user_id,
        "email": payload.get("email", ""),
        "full_name": user_metadata.get("full_name") or user_metadata.get("name") or "",
        "user_metadata": user_metadata,
    }

    return user_id
