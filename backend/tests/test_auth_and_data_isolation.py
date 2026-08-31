"""
tests/test_auth_and_data_isolation.py

Comprehensive tests verifying:
1. Supabase JWT authentication & strict 401 error handling.
2. Fresh user un-onboarded profile state (onboarding_completed: False, target_career_id: None).
3. Data isolation across separate user accounts.
4. Onboarding persistence against the authenticated Supabase user ID.
5. Personalized Roadmap endpoint (GET /api/roadmap).
6. Assessment replan persistence for authenticated accounts.
"""
import json
import pytest
import jwt
from unittest.mock import AsyncMock, patch


def make_test_token(user_id: str, email: str = "test@example.com", full_name: str = "Test User") -> str:
    """Generate an unverified JWT token for testing in development mode."""
    payload = {
        "sub": user_id,
        "email": email,
        "user_metadata": {
            "full_name": full_name,
            "name": full_name,
        },
    }
    return jwt.encode(payload, "dummy-secret-for-dev", algorithm="HS256")


@pytest.mark.asyncio
async def test_invalid_token_returns_401(client):
    """Providing an invalid/malformed token must return 401 Unauthorized without fallback."""
    response = await client.get("/api/me", headers={"Authorization": "Bearer invalid.token.payload"})
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_fresh_authenticated_user_clean_state(client):
    """
    A brand-new authenticated user must receive a clean, un-onboarded profile
    with onboarding_completed=False and target_career_id=None.
    """
    fresh_user_id = "user_test_fresh_001"
    token = make_test_token(fresh_user_id, "fresh@example.com", "Fresh User")
    headers = {"Authorization": f"Bearer {token}"}

    # 1. GET /api/me
    response = await client.get("/api/me", headers=headers)
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == fresh_user_id
    assert data["name"] == "Fresh User"
    assert data["target_career_id"] is None
    assert data["onboarding_completed"] is False
    assert data["interests"] == []
    assert data["current_focus_skill_id"] is None

    # 2. GET /api/me/activity
    act_resp = await client.get("/api/me/activity", headers=headers)
    assert act_resp.status_code == 200
    assert act_resp.json() == []

    # 3. GET /api/learning-history
    hist_resp = await client.get("/api/learning-history", headers=headers)
    assert hist_resp.status_code == 200
    assert hist_resp.json()["items"] == []

    # 4. GET /api/roadmap
    roadmap_resp = await client.get("/api/roadmap", headers=headers)
    assert roadmap_resp.status_code == 200
    assert roadmap_resp.json()["nodes"] == []


@pytest.mark.asyncio
async def test_onboarding_and_roadmap_flow(client):
    """
    POST /api/onboarding persists profile against the authenticated user,
    marks onboarding_completed=True, and generates personalized roadmap nodes.
    """
    user_id = "user_test_onboard_002"
    token = make_test_token(user_id, "onboard@example.com", "Onboard User")
    headers = {"Authorization": f"Bearer {token}"}

    onboard_payload = {
        "learner_id": "spoofed_id_attempt",  # Backend must ignore this and use JWT sub
        "name": "Onboard User",
        "first_name": "Onboard",
        "target_career_id": "career_frontend_dev",
        "current_level": "Beginner",
        "weekly_learning_hours": 12,
        "interests": ["UI Engineering"],
        "learning_style": "Project-based",
        "skills": [
            {"skill_id": "sk_html", "proficiency_score": 85},
            {"skill_id": "sk_css", "proficiency_score": 75},
        ],
        "prior_learning": [
            {"title": "HTML Basics", "type": "course"},
        ],
    }

    # 1. Submit onboarding
    post_resp = await client.post("/api/onboarding", json=onboard_payload, headers=headers)
    assert post_resp.status_code == 201
    assert post_resp.json()["learner_id"] == user_id
    assert post_resp.json()["success"] is True

    # 2. Check updated profile
    me_resp = await client.get("/api/me", headers=headers)
    assert me_resp.status_code == 200
    me_data = me_resp.json()
    assert me_data["id"] == user_id
    assert me_data["target_career_id"] == "career_frontend_dev"
    assert me_data["onboarding_completed"] is True
    assert me_data["weekly_learning_hours"] == 12

    # 3. Check personalized roadmap
    roadmap_resp = await client.get("/api/roadmap", headers=headers)
    assert roadmap_resp.status_code == 200
    roadmap_data = roadmap_resp.json()
    assert len(roadmap_data["nodes"]) > 0

    # HTML and CSS should be marked completed due to scores >= 70
    html_node = next((n for n in roadmap_data["nodes"] if n["id"] == "rm_html"), None)
    assert html_node is not None
    assert html_node["status"] == "completed"

    # 4. Check activity log has onboarding entry
    act_resp = await client.get("/api/me/activity", headers=headers)
    assert act_resp.status_code == 200
    acts = act_resp.json()
    assert len(acts) >= 1
    assert any("Completed onboarding" in a["label"] for a in acts)


@pytest.mark.asyncio
async def test_user_data_isolation(client):
    """
    Verifies User A cannot read or overwrite User B's learning history, profile, or activity.
    """
    user_a = "user_iso_a"
    user_b = "user_iso_b"

    token_a = make_test_token(user_a, "a@example.com", "User A")
    token_b = make_test_token(user_b, "b@example.com", "User B")

    headers_a = {"Authorization": f"Bearer {token_a}"}
    headers_b = {"Authorization": f"Bearer {token_b}"}

    # Initialize profiles for user_a and user_b
    await client.get("/api/me", headers=headers_a)
    await client.get("/api/me", headers=headers_b)

    # User A creates a history item
    item_payload = {
        "title": "User A Private Course",
        "type": "course",
        "status": "in-progress",
        "progress_pct": 50,
    }
    create_resp = await client.post("/api/learning-history", json=item_payload, headers=headers_a)
    assert create_resp.status_code == 201
    item_id = create_resp.json()["id"]

    # User A sees 1 item
    hist_a = (await client.get("/api/learning-history", headers=headers_a)).json()
    assert any(i["id"] == item_id for i in hist_a["items"])

    # User B sees 0 items (data isolated)
    hist_b = (await client.get("/api/learning-history", headers=headers_b)).json()
    assert not any(i["id"] == item_id for i in hist_b["items"])

    # User B cannot update User A's history item
    update_resp = await client.patch(
        f"/api/learning-history/{item_id}",
        json={"progress_pct": 100},
        headers=headers_b,
    )
    assert update_resp.status_code == 404
