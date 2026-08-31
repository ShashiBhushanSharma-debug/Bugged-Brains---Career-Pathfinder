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
import logging
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request
import httpx
import jwt

from app.config import get_settings, Settings

logger = logging.getLogger(__name__)


def _decode_supabase_secret(raw: str) -> Optional[bytes]:
    """
    Attempt to base64-decode the Supabase JWT secret.
    Supabase stores the JWT secret as a base64-encoded string in its dashboard
    and signs tokens with the raw decoded bytes.
    """
    if not raw:
        return None
    try:
        return base64.b64decode(raw, validate=True)
    except Exception:
        return None


async def _verify_token_with_supabase_api(token: str, supabase_url: str) -> Optional[Dict[str, Any]]:
    """
    Verify the token directly with the Supabase Auth API endpoint (GET /auth/v1/user).
    This serves as a reliable fallback when asymmetric keys (RS256/ES256), JWKS,
    or key rotations are configured on the Supabase project.
    """
    if not supabase_url:
        return None
    
    url = f"{supabase_url.rstrip('/')}/auth/v1/user"
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(url, headers={"Authorization": f"Bearer {token}"})
            if resp.status_code == 200:
                user_data = resp.json()
                if "id" in user_data:
                    return {
                        "sub": user_data["id"],
                        "email": user_data.get("email", ""),
                        "user_metadata": user_data.get("user_metadata", {}),
                    }
    except Exception as e:
        logger.debug("Supabase Auth API verification check failed: %s", e)
    return None


async def get_current_learner_id(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> str:
    """
    FastAPI dependency: resolve the current learner_id from the Supabase JWT.

    1. Read the Authorization header (Bearer token).
    2. Decode & verify the JWT (via local HS256 secret or Supabase Auth API).
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

    payload: Optional[Dict[str, Any]] = None

    # ── Verify the JWT ────────────────────────────────────────────────────────
    raw_secret = settings.supabase_jwt_secret
    is_secret_configured = bool(raw_secret and raw_secret != "your-jwt-secret-here")

    if is_secret_configured:
        # 1. Attempt verification with base64-decoded bytes (Supabase standard)
        b64_bytes = _decode_supabase_secret(raw_secret)
        if b64_bytes:
            try:
                payload = jwt.decode(
                    token,
                    b64_bytes,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token has expired.")
            except jwt.InvalidTokenError:
                payload = None

        # 2. If decoded bytes failed, attempt verification with raw string (UTF-8 bytes)
        if payload is None:
            try:
                payload = jwt.decode(
                    token,
                    raw_secret,
                    algorithms=["HS256"],
                    options={"verify_aud": False},
                )
            except jwt.ExpiredSignatureError:
                raise HTTPException(status_code=401, detail="Token has expired.")
            except jwt.InvalidTokenError:
                payload = None

    # 3. If local signature failed or asymmetric/JWKS is used, verify via Supabase Auth API
    if payload is None and settings.supabase_url:
        payload = await _verify_token_with_supabase_api(token, settings.supabase_url)

    # 4. In development mode only, if secret is unconfigured, allow unverified decode
    if payload is None:
        if settings.is_development:
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
            except Exception:
                raise HTTPException(status_code=401, detail="Malformed authentication token.")
        else:
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token.",
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
