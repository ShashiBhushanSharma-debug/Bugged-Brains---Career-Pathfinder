"""
tests/test_learner.py

Tests for GET /api/me and PATCH /api/me.
Uses seeded learner u_1001.
"""
import pytest
from unittest.mock import AsyncMock, patch


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

# Test for the replanning of the overall career path finder

@pytest.mark.asyncio
async def test_post_me_replan_success(client, dev_learner_id):
    """
    POST /api/me/replan executes the BKT math and dynamic replanner,
    returning a structured response with headline, mastery, and roadmap steps.
    """
    # Sample mock response matching the LangGraph output schema
    mock_final_state = {
        "replan_status_message": "Targeted recovery step injected for React.",
        "new_mastery_score": 0.4521,
        "replan_output": {
            "headline": "Targeted recovery step injected for React.",
            "reasoning": "Score was below threshold; reinforcing core concepts.",
            "updated_steps": [
                {
                    "node_id": "remedial_sk_react",
                    "title": "Targeted Recovery: React Core Foundations",
                    "type": "skill",
                    "target_skill_id": "sk_react",
                    "difficulty": "Beginner",
                    "estimated_hours": 4,
                    "action_type": "injected_remedial",
                    "rationale": {
                        "why_now": "Reinforcing core mechanics before proceeding.",
                        "skill_gap_addressed": "React fundamentals gap."
                    }
                }
            ]
        }
    }

    # Patch adaptive_graph_app.ainvoke so tests do not rely on external Cerebras network calls
    with patch("app.api.routes.learner.adaptive_graph_app.ainvoke", new_callable=AsyncMock) as mock_invoke:
        mock_invoke.return_value = mock_final_state

        payload = {
            "step_id": "as_react_basics",
            "target_skill_id": "sk_react",
            "score_percentage": 50.0,
            "user_feedback": "too fast"
        }

        response = await client.post("/api/me/replan", json=payload)
        assert response.status_code == 200

        data = response.json()
        assert data["status"] == "success"
        assert data["headline"] == "Targeted recovery step injected for React."
        assert data["updated_mastery"] == 0.4521
        assert "roadmap" in data
        assert len(data["roadmap"]["updated_steps"]) == 1
        assert data["roadmap"]["updated_steps"][0]["action_type"] == "injected_remedial"


@pytest.mark.asyncio
async def test_post_me_replan_validation_error(client):
    """
    POST /api/me/replan rejects invalid signals missing required fields.
    """
    invalid_payload = {
        "step_id": "as_react_basics"
        # Missing required target_skill_id and score_percentage
    }

    response = await client.post("/api/me/replan", json=invalid_payload)
    assert response.status_code == 422  # Unprocessable Entity
