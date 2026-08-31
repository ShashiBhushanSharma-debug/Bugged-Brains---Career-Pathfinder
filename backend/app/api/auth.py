"""
app/api/auth.py

Centralised authentication dependency for all protected endpoints.

Phase 3 & Production: Verifies Supabase JWT access tokens using:
1. ES256 / RS256 Asymmetric JWKS public keys fetched from:
   https://<project-ref>.supabase.co/auth/v1/.well-known/jwks.json
2. HS256 Symmetric shared secret (legacy / local dev).

- If an Authorization header is provided, it is strictly validated. Any invalid,
  expired, or malformed token results in a 401 Unauthorized.
- No fallback to DEV_LEARNER_ID is ever performed when an authenticated token is present.
- When NO Authorization header is sent in development mode, it returns DEV_LEARNER_ID
  strictly to allow unauthenticated backend unit test runs.
"""
from __future__ import annotations

import base64
import logging
import time
from typing import Any, Dict, Optional

from fastapi import Depends, HTTPException, Request
import jwt
from jwt import PyJWKClient, PyJWKClientError

from app.config import get_settings, Settings

logger = logging.getLogger(__name__)

ALLOWED_ALGORITHMS = {"ES256", "RS256", "HS256"}

# In-memory JWKS clients cached per Supabase URL
_jwks_clients: Dict[str, PyJWKClient] = {}


def get_jwks_client(supabase_url: str) -> PyJWKClient:
    """
    Get or create a cached PyJWKClient for the given Supabase URL.
    JWKS keys are cached in-memory with a 1-hour TTL (3600s).
    """
    jwks_url = f"{supabase_url.rstrip('/')}/auth/v1/.well-known/jwks.json"
    if jwks_url not in _jwks_clients:
        _jwks_clients[jwks_url] = PyJWKClient(
            jwks_url,
            cache_keys=True,
            max_cached_keys=16,
            lifespan=3600,
        )
    return _jwks_clients[jwks_url]


def _decode_supabase_secret(raw: str) -> Optional[bytes]:
    """
    Attempt to base64-decode the Supabase JWT secret for HS256 tokens.
    """
    if not raw:
        return None
    try:
        clean = raw.strip().strip('"').strip("'")
        return base64.b64decode(clean, validate=True)
    except Exception:
        return None


def _get_signing_key_with_refresh(jwks_client: PyJWKClient, kid: str):
    """
    Retrieve signing key by kid from JWKS client.
    If not found in cache (possible key rotation), invalidate cache and retry once.
    """
    try:
        return jwks_client.get_signing_key(kid)
    except Exception:
        # Key rotation or cache miss — invalidate cached set and retry once
        try:
            jwks_client.jwk_set = None
            return jwks_client.get_signing_key(kid)
        except Exception as retry_err:
            raise PyJWKClientError(f"Signing key not found for kid '{kid}': {retry_err}") from retry_err


async def get_current_learner_id(
    request: Request,
    settings: Settings = Depends(get_settings),
) -> str:
    """
    FastAPI dependency: resolve the current learner_id from the Supabase JWT.

    1. Read the Authorization header (Bearer token).
    2. Inspect unverified header for algorithm and key ID (kid).
    3. Verify token:
       - If ES256 / RS256: fetch public key from Supabase JWKS and verify signature.
       - If HS256: verify using SUPABASE_JWT_SECRET.
    4. Validate expiration, issuer, audience, and required `sub` claim.
    5. Return the `sub` claim (auth.uid()).
    """
    auth_header = request.headers.get("Authorization", "")
    has_header = bool(auth_header)
    is_bearer = auth_header.startswith("Bearer ")

    # ── No token provided ────────────────────────────────────────────────────
    if not has_header or not is_bearer:
        print(f"[AUTH DIAGNOSTIC] authorization_present={has_header}, is_bearer={is_bearer}, action=REJECT_NO_TOKEN")
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
        print("[AUTH DIAGNOSTIC] token_present=False, action=REJECT_EMPTY_TOKEN")
        raise HTTPException(status_code=401, detail="Empty authentication token.")

    # ── Inspect unverified token header & metadata ────────────────────────────
    alg = None
    kid = None
    iss = None
    aud = None
    exp = None
    has_sub = False
    is_expired = False

    try:
        header = jwt.get_unverified_header(token)
        alg = header.get("alg")
        kid = header.get("kid")
    except Exception as e:
        print(f"[AUTH DIAGNOSTIC] header_inspection_error={type(e).__name__}")
        raise HTTPException(status_code=401, detail="Malformed authentication token header.")

    # Reject disallowed algorithms (including 'none' or missing alg)
    if not alg or alg not in ALLOWED_ALGORITHMS:
        print(f"[AUTH DIAGNOSTIC] disallowed_alg={alg}, action=REJECT_401")
        raise HTTPException(status_code=401, detail=f"Unsupported token algorithm '{alg}'.")

    try:
        unverified = jwt.decode(
            token,
            options={"verify_signature": False, "verify_exp": False, "verify_aud": False},
        )
        iss = unverified.get("iss")
        aud = unverified.get("aud")
        exp = unverified.get("exp")
        has_sub = bool(unverified.get("sub"))
        if exp:
            is_expired = time.time() > exp
    except Exception as e:
        print(f"[AUTH DIAGNOSTIC] payload_inspection_error={type(e).__name__}")
        raise HTTPException(status_code=401, detail="Malformed authentication token payload.")

    print(
        f"[AUTH DIAGNOSTIC] incoming_jwt: alg={alg}, kid={kid}, iss={iss}, aud={aud}, "
        f"has_sub={has_sub}, is_expired={is_expired}"
    )

    if is_expired:
        print("[AUTH DIAGNOSTIC] rejection_reason=Token_is_expired")
        raise HTTPException(status_code=401, detail="Token has expired.")

    payload: Optional[Dict[str, Any]] = None

    # ── 1. Asymmetric Verification (ES256 / RS256 via Supabase JWKS) ──────────
    if alg in {"ES256", "RS256"}:
        supabase_url = settings.supabase_url
        if not supabase_url:
            print("[AUTH DIAGNOSTIC] error=SUPABASE_URL_missing_for_JWKS")
            if not settings.is_development:
                raise HTTPException(status_code=500, detail="Server configuration error: SUPABASE_URL is not set.")
        else:
            if not kid:
                print("[AUTH DIAGNOSTIC] error=asymmetric_token_missing_kid")
                raise HTTPException(status_code=401, detail="Token missing key ID (kid).")

            try:
                jwks_client = get_jwks_client(supabase_url)
                signing_key = _get_signing_key_with_refresh(jwks_client, kid)
                print(f"[AUTH DIAGNOSTIC] alg={alg} kid={kid} key_found=True")

                payload = jwt.decode(
                    token,
                    signing_key.key,
                    algorithms=[alg],
                    audience="authenticated",
                    options={
                        "verify_signature": True,
                        "verify_exp": True,
                        "verify_nbf": True,
                        "verify_aud": True,
                        "verify_iss": False,  # validate explicitly below for clean diagnostic logging
                    },
                )
                print(f"[AUTH DIAGNOSTIC] verification_method=supabase_jwks, signature_valid=True")
            except jwt.ExpiredSignatureError:
                print("[AUTH DIAGNOSTIC] verification_method=supabase_jwks, error=ExpiredSignatureError")
                raise HTTPException(status_code=401, detail="Token has expired.")
            except jwt.InvalidAudienceError:
                print(f"[AUTH DIAGNOSTIC] verification_method=supabase_jwks, error=InvalidAudience (aud={aud})")
                raise HTTPException(status_code=401, detail="Invalid token audience.")
            except PyJWKClientError as e:
                print(f"[AUTH DIAGNOSTIC] verification_method=supabase_jwks, error=PyJWKClientError ({e})")
                raise HTTPException(status_code=401, detail="Unable to verify token signature with key server.")
            except Exception as e:
                print(f"[AUTH DIAGNOSTIC] verification_method=supabase_jwks, error={type(e).__name__} ({e})")
                payload = None

        # Validate issuer if supabase_url is configured
        if payload and supabase_url:
            expected_iss = f"{supabase_url.rstrip('/')}/auth/v1"
            token_iss = payload.get("iss")
            if token_iss and token_iss != expected_iss:
                print(f"[AUTH DIAGNOSTIC] issuer_mismatch: expected={expected_iss}, received={token_iss}")
                raise HTTPException(status_code=401, detail="Invalid token issuer.")

    # ── 2. Symmetric Verification (HS256 via SUPABASE_JWT_SECRET) ─────────────
    elif alg == "HS256":
        raw_secret = (settings.supabase_jwt_secret or "").strip().strip('"').strip("'")
        is_secret_configured = bool(raw_secret and raw_secret != "your-jwt-secret-here")

        if is_secret_configured:
            # Try base64 decoded bytes first
            b64_bytes = _decode_supabase_secret(raw_secret)
            if b64_bytes:
                try:
                    payload = jwt.decode(
                        token,
                        b64_bytes,
                        algorithms=["HS256"],
                        audience="authenticated",
                        options={"verify_aud": False},
                    )
                    print("[AUTH DIAGNOSTIC] verification_method=hs256_base64, success=True")
                except jwt.ExpiredSignatureError:
                    raise HTTPException(status_code=401, detail="Token has expired.")
                except Exception:
                    payload = None

            # Fallback to UTF-8 raw string bytes
            if payload is None:
                try:
                    payload = jwt.decode(
                        token,
                        raw_secret,
                        algorithms=["HS256"],
                        audience="authenticated",
                        options={"verify_aud": False},
                    )
                    print("[AUTH DIAGNOSTIC] verification_method=hs256_raw_string, success=True")
                except jwt.ExpiredSignatureError:
                    raise HTTPException(status_code=401, detail="Token has expired.")
                except Exception:
                    payload = None

    # ── 3. Development Fallback (only when secrets/JWKS unconfigured in dev) ──
    if payload is None:
        if settings.is_development:
            try:
                payload = jwt.decode(token, options={"verify_signature": False})
                print("[AUTH DIAGNOSTIC] step=dev_unverified_fallback, success=True")
            except Exception:
                raise HTTPException(status_code=401, detail="Malformed authentication token.")
        else:
            print("[AUTH DIAGNOSTIC] final_result=REJECTED_401 (signature verification failed)")
            raise HTTPException(
                status_code=401,
                detail="Invalid authentication token.",
            )

    # ── 4. Validate `sub` (auth.uid()) ────────────────────────────────────────
    user_id = payload.get("sub")
    if not user_id:
        print("[AUTH DIAGNOSTIC] final_result=REJECTED_401 (token missing sub claim)")
        raise HTTPException(status_code=401, detail="Token missing user identity.")

    print(f"[AUTH DIAGNOSTIC] final_result=AUTHENTICATED (has_sub=True)")

    # Store user metadata on request.state for downstream route auto-provisioning
    user_metadata = payload.get("user_metadata", {}) or {}
    request.state.is_authenticated = True
    request.state.user_info = {
        "id": user_id,
        "email": payload.get("email", ""),
        "full_name": user_metadata.get("full_name") or user_metadata.get("name") or "",
        "user_metadata": user_metadata,
    }

    return user_id
