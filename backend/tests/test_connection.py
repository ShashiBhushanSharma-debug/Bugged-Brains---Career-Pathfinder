"""
tests/test_connection.py

Verifies that the asyncpg pool can connect to Supabase PostgreSQL
and that the expected tables from 001_initial_schema.sql exist.
"""
import pytest
import pytest_asyncio


EXPECTED_TABLES = {
    "skills", "careers", "career_skills", "skill_prerequisites",
    "learner_profiles", "learner_skills", "resources", "resource_skills",
    "roadmap_nodes", "roadmap_node_prerequisites", "learner_roadmap_nodes",
    "assessments", "assessment_questions", "assessment_results",
    "learning_history", "recommendations", "activity_log", "roadmap_replans",
}


@pytest.mark.asyncio
async def test_pool_connects(db_pool):
    """Pool is open and can execute a query."""
    result = await db_pool.fetchval("SELECT 1")
    assert result == 1


@pytest.mark.asyncio
async def test_all_tables_exist(db_pool):
    """All 18 tables from 001_initial_schema.sql are present."""
    rows = await db_pool.fetch(
        """
        SELECT tablename
        FROM pg_tables
        WHERE schemaname = 'public'
        """
    )
    existing = {r["tablename"] for r in rows}
    missing = EXPECTED_TABLES - existing
    assert not missing, f"Missing tables: {missing}"


@pytest.mark.asyncio
async def test_seed_skills_exist(db_pool):
    """Seed data: 10 skills from 002_seed_data.sql."""
    count = await db_pool.fetchval("SELECT COUNT(*) FROM skills")
    assert count >= 10, f"Expected at least 10 skills, got {count}"


@pytest.mark.asyncio
async def test_seed_learner_exists(db_pool, dev_learner_id):
    """Seed data: demo learner u_1001 exists."""
    row = await db_pool.fetchrow(
        "SELECT id, name FROM learner_profiles WHERE id = $1", dev_learner_id
    )
    assert row is not None, f"Learner {dev_learner_id} not found in DB"
    assert row["name"] == "Alex Rivera"
