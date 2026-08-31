"""
tests/test_standalone_auth_and_health.py

Offline unit tests verifying:
1. GET /health returns 200 OK with {"status": "ok"}
2. GET / (root) returns 200 OK with {"status": "ok"}
3. Missing JWT returns 401 Unauthorized on protected routes
4. Invalid/malformed JWT returns 401 Unauthorized
5. POST /api/recommendations strictly requires valid authentication
6. Secret decoding and production token verification
"""
import base64
import pytest
from httpx import AsyncClient, ASGITransport
import jwt

from app.main import app
from app.api.auth import _decode_supabase_secret
from app.config import get_settings


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.asyncio
async def test_health_check_responds_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/health")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "version" in data


@pytest.mark.asyncio
async def test_root_endpoint_responds_200():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert "health" in data


@pytest.mark.asyncio
async def test_protected_routes_reject_missing_token_in_production(monkeypatch):
    """When APP_ENV=production, missing Bearer token must return 401."""
    settings = get_settings()
    monkeypatch.setattr(settings, "app_env", "production")

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/me")
        assert resp.status_code == 401
        assert "Missing authentication token" in resp.text


@pytest.mark.asyncio
async def test_protected_routes_reject_malformed_token():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/me", headers={"Authorization": "Bearer bad-token"})
        assert resp.status_code == 401


@pytest.mark.asyncio
async def test_post_recommendations_rejects_missing_or_invalid_auth(monkeypatch):
    from unittest.mock import AsyncMock
    import app.database.connection as conn_module

    # Mock DB pool so dependency resolution succeeds without a live DB
    monkeypatch.setattr(conn_module, "_pool", AsyncMock())
    settings = get_settings()

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        # 1. Missing auth in production
        monkeypatch.setattr(settings, "app_env", "production")
        resp1 = await client.post(
            "/api/recommendations",
            json={"learner_id": "target_user", "recommendations": []},
        )
        assert resp1.status_code == 401

        # 2. Invalid token in production
        resp2 = await client.post(
            "/api/recommendations",
            json={"learner_id": "target_user", "recommendations": []},
            headers={"Authorization": "Bearer invalid.jwt.here"},
        )
        assert resp2.status_code == 401


def test_base64_secret_decoding_unit():
    raw_b64 = "dGVzdC1zZWNyZXQtZm9yLXVuaXQtdGVzdGluZy1vbmx5LXNhZmU="
    decoded = _decode_supabase_secret(raw_b64)
    assert isinstance(decoded, bytes)
    assert decoded == base64.b64decode(raw_b64)


def test_plain_secret_fallback_unit():
    plain = "not-base64-plain-secret"
    result = _decode_supabase_secret(plain)
    assert result is not None
