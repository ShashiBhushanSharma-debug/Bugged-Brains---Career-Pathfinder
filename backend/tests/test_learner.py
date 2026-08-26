"""
tests/test_learner.py

Tests for GET /api/me and PATCH /api/me.
Uses seeded learner u_1001.
"""
import pytest


@pytest.mark.asyncio
async def test_get_me_returns_200(client, dev_learner_id):
    response = await client.get("/api/me")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_me_shape(client, dev_learner_id):
    """Response mirrors userData.js currentUser shape."""
    response = await client.get("/api/me")
    data = response.json()

    assert data["id"] == dev_learner_id
    assert data["name"] == "Alex Rivera"
    assert data["first_name"] == "Alex"
    assert data["target_career_id"] == "career_frontend_dev"
    assert data["streak_days"] == 6
    assert data["weekly_learning_hours"] == 8
    assert data["total_learning_hours"] == 46
    assert isinstance(data["interests"], list)
    assert "Web Development" in data["interests"]


@pytest.mark.asyncio
async def test_get_me_activity(client, dev_learner_id):
    """GET /api/me/activity returns a list with at least the 4 seeded items."""
    response = await client.get("/api/me/activity")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 4


@pytest.mark.asyncio
async def test_patch_me(client, dev_learner_id):
    """PATCH /api/me updates a field and returns the updated profile."""
    original = (await client.get("/api/me")).json()
    new_hours = 10 if original["weekly_learning_hours"] != 10 else 8

    response = await client.patch("/api/me", json={"weekly_learning_hours": new_hours})
    assert response.status_code == 200
    assert response.json()["weekly_learning_hours"] == new_hours

    # Restore original value
    await client.patch("/api/me", json={"weekly_learning_hours": original["weekly_learning_hours"]})
