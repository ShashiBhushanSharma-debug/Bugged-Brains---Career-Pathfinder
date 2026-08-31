"""
tests/test_resources.py

Tests for GET /api/resources and GET /api/learning-history.
"""
import pytest


@pytest.mark.asyncio
async def test_get_resources_200(client):
    response = await client.get("/api/resources")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_resources_shape(client):
    data = (await client.get("/api/resources")).json()
    assert "resources" in data
    assert "total" in data
    assert data["total"] >= 8
    # Each resource has required fields
    for r in data["resources"]:
        assert "id" in r
        assert "title" in r
        assert "type" in r


@pytest.mark.asyncio
async def test_filter_resources_by_skill(client):
    """Filter by skill_id returns only resources for that skill."""
    response = await client.get("/api/resources?skill_id=sk_react")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    # All returned resources should cover sk_react
    for r in data["resources"]:
        assert "sk_react" in r["skill_ids"]


@pytest.mark.asyncio
async def test_filter_resources_by_type(client):
    response = await client.get("/api/resources?type=course")
    assert response.status_code == 200
    data = response.json()
    for r in data["resources"]:
        assert r["type"] == "course"


@pytest.mark.asyncio
async def test_get_resource_by_id(client):
    response = await client.get("/api/resources/res_1")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "res_1"
    assert data["title"] == "React Fundamentals"


@pytest.mark.asyncio
async def test_resource_not_found(client):
    response = await client.get("/api/resources/nonexistent")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_get_learning_history_200(client):
    response = await client.get("/api/learning-history")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_learning_history_shape(client, dev_learner_id):
    data = (await client.get("/api/learning-history")).json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 8  # 4 mock history + 4 resource-linked items

    for item in data["items"]:
        assert "id" in item
        assert "title" in item
        assert "status" in item
        assert item["status"] in ("not-started", "in-progress", "completed")


@pytest.mark.asyncio
async def test_filter_history_by_status(client):
    response = await client.get("/api/learning-history?status=completed")
    assert response.status_code == 200
    data = response.json()
    for item in data["items"]:
        assert item["status"] == "completed"


@pytest.mark.asyncio
async def test_get_recommendations_200(client):
    response = await client.get("/api/recommendations")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_get_recommendations_shape(client, dev_learner_id):
    data = (await client.get("/api/recommendations")).json()
    assert data["learner_id"] == dev_learner_id
    assert isinstance(data["recommendations"], list)
    assert len(data["recommendations"]) >= 4
    # Ordered by score descending
    scores = [r["score"] for r in data["recommendations"]]
    assert scores == sorted(scores, reverse=True)
