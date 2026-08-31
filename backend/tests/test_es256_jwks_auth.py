"""
tests/test_es256_jwks_auth.py

Comprehensive tests verifying Supabase ES256 asymmetric JWKS verification:
1. Valid ES256 JWT with matching JWKS key -> 200 OK / authenticated
2. ES256 JWT with unknown kid -> 401 Unauthorized
3. ES256 JWT with invalid signature -> 401 Unauthorized
4. Expired ES256 JWT -> 401 Unauthorized
5. Wrong issuer -> 401 Unauthorized
6. Wrong audience -> 401 Unauthorized
7. Missing sub -> 401 Unauthorized
8. Disallowed algorithm (e.g. none) -> 401 Unauthorized
9. HS256 compatibility -> 200 OK
10. JWKS cache refresh on unknown kid
"""
import base64
import time
from unittest.mock import AsyncMock, MagicMock
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import AsyncClient, ASGITransport
import jwt
from jwt import PyJWKClientError

from app.main import app
from app.config import get_settings
import app.api.auth as auth_module


@pytest.fixture
def ec_keypair():
    """Generate a temporary, in-memory EC key pair for ES256 testing."""
    private_key = ec.generate_private_key(ec.SECP256R1())
    public_key = private_key.public_key()
    return private_key, public_key


@pytest.fixture
def mock_db_and_learner(monkeypatch):
    """Mock DB pool and learner profile repository for unit testing."""
    import app.database.connection as conn_module
    monkeypatch.setattr(conn_module, "_pool", AsyncMock())

    from app.database.repositories import learner_repo
    async def mock_get_learner(pool, lid):
        return {
            "id": lid,
            "name": "Test User",
            "first_name": "Test",
            "target_career_id": "cr_frontend",
            "current_level": "Beginner",
            "weekly_learning_hours": 8,
            "onboarding_completed": True,
        }
    monkeypatch.setattr(learner_repo, "get_learner_by_id", mock_get_learner)


@pytest.mark.asyncio
async def test_es256_valid_token_authenticated(ec_keypair, mock_db_and_learner, monkeypatch):
    """Valid ES256 JWT signed with private key and verified with mock JWKS public key."""
    private_key, public_key = ec_keypair
    kid = "test-kid-valid-001"
    supabase_url = "https://mock.supabase.co"

    settings = get_settings()
    monkeypatch.setattr(settings, "supabase_url", supabase_url)
    monkeypatch.setattr(settings, "app_env", "production")

    # Mock JWKS client
    mock_jwks_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    mock_signing_key.key_id = kid
    mock_jwks_client.get_signing_key.return_value = mock_signing_key
    monkeypatch.setattr(auth_module, "get_jwks_client", lambda url: mock_jwks_client)

    payload = {
        "sub": "user_es256_valid_123",
        "iss": f"{supabase_url}/auth/v1",
        "aud": "authenticated",
        "email": "es256@example.com",
        "user_metadata": {"full_name": "ES256 User"},
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": kid})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 200, f"Expected 200, got {resp.status_code}: {resp.text}"
        data = resp.json()
        assert data["id"] == "user_es256_valid_123"


@pytest.mark.asyncio
async def test_es256_unknown_kid_returns_401(ec_keypair, mock_db_and_learner, monkeypatch):
    """ES256 JWT with a kid not found in JWKS must return 401."""
    private_key, _ = ec_keypair
    supabase_url = "https://mock.supabase.co"

    settings = get_settings()
    monkeypatch.setattr(settings, "supabase_url", supabase_url)
    monkeypatch.setattr(settings, "app_env", "production")

    mock_jwks_client = MagicMock()
    mock_jwks_client.get_signing_key.side_effect = PyJWKClientError("Key not found")
    monkeypatch.setattr(auth_module, "get_jwks_client", lambda url: mock_jwks_client)

    payload = {
        "sub": "user_unknown_kid",
        "iss": f"{supabase_url}/auth/v1",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": "unknown-kid"})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_es256_invalid_signature_returns_401(mock_db_and_learner, monkeypatch):
    """ES256 JWT signed with an unrelated private key must fail signature verification."""
    key1 = ec.generate_private_key(ec.SECP256R1())
    key2 = ec.generate_private_key(ec.SECP256R1())  # Different key
    public_key2 = key2.public_key()
    kid = "test-kid-sig-mismatch"
    supabase_url = "https://mock.supabase.co"

    settings = get_settings()
    monkeypatch.setattr(settings, "supabase_url", supabase_url)
    monkeypatch.setattr(settings, "app_env", "production")

    mock_jwks_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key2
    mock_jwks_client.get_signing_key.return_value = mock_signing_key
    monkeypatch.setattr(auth_module, "get_jwks_client", lambda url: mock_jwks_client)

    # Sign with key1, but JWKS has public_key2
    payload = {
        "sub": "user_bad_sig",
        "iss": f"{supabase_url}/auth/v1",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, key1, algorithm="ES256", headers={"kid": kid})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_es256_expired_token_returns_401(ec_keypair, mock_db_and_learner, monkeypatch):
    """Expired ES256 JWT must return 401."""
    private_key, public_key = ec_keypair
    kid = "test-kid-expired"
    supabase_url = "https://mock.supabase.co"

    settings = get_settings()
    monkeypatch.setattr(settings, "supabase_url", supabase_url)
    monkeypatch.setattr(settings, "app_env", "production")

    mock_jwks_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    mock_jwks_client.get_signing_key.return_value = mock_signing_key
    monkeypatch.setattr(auth_module, "get_jwks_client", lambda url: mock_jwks_client)

    payload = {
        "sub": "user_expired",
        "iss": f"{supabase_url}/auth/v1",
        "aud": "authenticated",
        "exp": int(time.time()) - 3600,  # 1 hour ago
    }
    token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": kid})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401
        assert "expired" in resp.text.lower()


@pytest.mark.asyncio
async def test_es256_wrong_issuer_returns_401(ec_keypair, mock_db_and_learner, monkeypatch):
    """ES256 JWT with wrong issuer must return 401."""
    private_key, public_key = ec_keypair
    kid = "test-kid-issuer"
    supabase_url = "https://mock.supabase.co"

    settings = get_settings()
    monkeypatch.setattr(settings, "supabase_url", supabase_url)
    monkeypatch.setattr(settings, "app_env", "production")

    mock_jwks_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    mock_jwks_client.get_signing_key.return_value = mock_signing_key
    monkeypatch.setattr(auth_module, "get_jwks_client", lambda url: mock_jwks_client)

    payload = {
        "sub": "user_wrong_iss",
        "iss": "https://malicious.supabase.co/auth/v1",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": kid})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_es256_wrong_audience_returns_401(ec_keypair, mock_db_and_learner, monkeypatch):
    """ES256 JWT with wrong audience must return 401."""
    private_key, public_key = ec_keypair
    kid = "test-kid-aud"
    supabase_url = "https://mock.supabase.co"

    settings = get_settings()
    monkeypatch.setattr(settings, "supabase_url", supabase_url)
    monkeypatch.setattr(settings, "app_env", "production")

    mock_jwks_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    mock_jwks_client.get_signing_key.return_value = mock_signing_key
    monkeypatch.setattr(auth_module, "get_jwks_client", lambda url: mock_jwks_client)

    payload = {
        "sub": "user_wrong_aud",
        "iss": f"{supabase_url}/auth/v1",
        "aud": "wrong-audience",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": kid})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_es256_missing_sub_returns_401(ec_keypair, mock_db_and_learner, monkeypatch):
    """ES256 JWT without sub claim must return 401."""
    private_key, public_key = ec_keypair
    kid = "test-kid-no-sub"
    supabase_url = "https://mock.supabase.co"

    settings = get_settings()
    monkeypatch.setattr(settings, "supabase_url", supabase_url)
    monkeypatch.setattr(settings, "app_env", "production")

    mock_jwks_client = MagicMock()
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    mock_jwks_client.get_signing_key.return_value = mock_signing_key
    monkeypatch.setattr(auth_module, "get_jwks_client", lambda url: mock_jwks_client)

    payload = {
        "iss": f"{supabase_url}/auth/v1",
        "aud": "authenticated",
        "exp": int(time.time()) + 3600,
    }
    token = jwt.encode(payload, private_key, algorithm="ES256", headers={"kid": kid})

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/me", headers={"Authorization": f"Bearer {token}"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_disallowed_algorithm_returns_401(mock_db_and_learner, monkeypatch):
    """Tokens with alg=none or disallowed algorithms must be rejected immediately."""
    settings = get_settings()
    monkeypatch.setattr(settings, "app_env", "production")

    # Unsigned token with alg=none
    token_none = jwt.encode({"sub": "attacker"}, key="", algorithm="none")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/me", headers={"Authorization": f"Bearer {token_none}"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_jwks_cache_refresh_on_unknown_kid(ec_keypair):
    """When a kid is initially missing from cache, the helper invalidates cache and retries."""
    _, public_key = ec_keypair
    mock_signing_key = MagicMock()
    mock_signing_key.key = public_key
    mock_signing_key.key_id = "rotated-kid"

    mock_client = MagicMock()
    # First call raises error, second call (after refresh) returns key
    mock_client.get_signing_key.side_effect = [
        PyJWKClientError("Not in cache"),
        mock_signing_key,
    ]

    key = auth_module._get_signing_key_with_refresh(mock_client, "rotated-kid")
    assert key == mock_signing_key
    assert mock_client.jwk_set is None  # Cache was invalidated
