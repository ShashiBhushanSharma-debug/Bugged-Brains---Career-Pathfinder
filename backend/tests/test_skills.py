"""
tests/test_skills.py

Tests for GET /api/skills/analysis, GET /api/skills, GET /api/careers.
"""
import pytest


@pytest.mark.asyncio
async def test_skill_analysis_200(client):
    response = await client.get("/api/skills/analysis")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_skill_analysis_shape(client, dev_learner_id):
    """Response has the expected top-level structure."""
    response = await client.get("/api/skills/analysis")
    data = response.json()

    assert data["learner_id"] == dev_learner_id
    assert data["career_id"] == "career_frontend_dev"
    assert data["career_title"] == "Frontend Developer"
    assert isinstance(data["categories"], list)
    assert len(data["categories"]) == 4
    assert isinstance(data["all_gaps"], list)
    assert len(data["all_gaps"]) > 0
    assert 0 <= data["career_readiness_pct"] <= 100


@pytest.mark.asyncio
async def test_skill_analysis_categories(client):
    """All four expected categories are present."""
    data = (await client.get("/api/skills/analysis")).json()
    category_ids = [c["id"] for c in data["categories"]]
    assert "known" in category_ids
    assert "developing" in category_ids
    assert "recommended" in category_ids
    assert "future" in category_ids


@pytest.mark.asyncio
async def test_skill_analysis_gap_math(client):
    """gap = required_score - proficiency_score for every item."""
    data = (await client.get("/api/skills/analysis")).json()
    for item in data["all_gaps"]:
        expected_gap = item["required_score"] - item["proficiency_score"]
        assert item["gap"] == expected_gap, (
            f"Gap math wrong for {item['name']}: "
            f"{item['required_score']} - {item['proficiency_score']} != {item['gap']}"
        )


@pytest.mark.asyncio
async def test_skill_analysis_known_skills(client):
    """HTML and CSS should be in the 'known' category (proficiency >= required)."""
    data = (await client.get("/api/skills/analysis")).json()
    known = next(c for c in data["categories"] if c["id"] == "known")
    known_names = [s["name"] for s in known["skills"]]
    assert "HTML" in known_names
    assert "CSS" in known_names


@pytest.mark.asyncio
async def test_get_all_skills(client):
    response = await client.get("/api/skills")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 10
    skill_names = [s["name"] for s in data]
    assert "React" in skill_names
    assert "JavaScript" in skill_names


@pytest.mark.asyncio
async def test_get_careers(client):
    response = await client.get("/api/careers")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) >= 1
    assert data[0]["title"] == "Frontend Developer"


@pytest.mark.asyncio
async def test_get_career_detail(client):
    response = await client.get("/api/careers/career_frontend_dev")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == "career_frontend_dev"
    assert "required_skills" in data
    assert len(data["required_skills"]) >= 10


@pytest.mark.asyncio
async def test_career_not_found(client):
    response = await client.get("/api/careers/nonexistent_career")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_onboarding_creates_learner(client):
    """POST /api/onboarding: creates a new learner and returns success."""
    payload = {
        "learner_id": "test_onboarding_001",
        "name": "Test Learner",
        "first_name": "Test",
        "target_career_id": "career_frontend_dev",
        "current_level": "Beginner",
        "weekly_learning_hours": 5,
        "interests": ["Web Development"],
        "skills": [
            {"skill_id": "sk_html", "proficiency_score": 70},
            {"skill_id": "sk_css", "proficiency_score": 60},
        ],
        "prior_learning": [
            {"title": "Intro to HTML", "type": "course"},
        ],
    }
    response = await client.post("/api/onboarding", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["success"] is True
    assert data["learner_id"] == "test_onboarding_001"
    assert data["skills_saved"] == 2
    assert data["history_saved"] == 1
