"""
app/config.py

Central settings object loaded from environment variables via pydantic-settings.
Never import secrets directly — always go through settings.
"""
from functools import lru_cache
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ── Database ──────────────────────────────────────────────────────────────
    database_url: str

    # asyncpg connection pool sizing
    db_min_connections: int = 2
    db_max_connections: int = 10

    # ── App ───────────────────────────────────────────────────────────────────
    app_env: str = "development"
    app_host: str = "0.0.0.0"
    app_port: int = Field(default=8000, validation_alias=AliasChoices("port", "app_port"))

    # ── CORS ──────────────────────────────────────────────────────────────────
    # Stored as a comma-separated string in .env; parsed into a list below.
    cors_origins: str = "http://localhost:5173,http://localhost:3000"

    @property
    def cors_origins_list(self) -> list[str]:
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # ── Supabase Auth ─────────────────────────────────────────────────────────
    # JWT secret used to verify Supabase access tokens on the backend.
    # Found in: Supabase Dashboard > Project Settings > API > JWT Secret
    supabase_jwt_secret: str = ""
    supabase_url: str = ""

    # ── Development ───────────────────────────────────────────────────────────
    # Placeholder learner used in all endpoints until Phase 3 adds real auth.
    dev_learner_id: str = "u_1001"

    @property
    def is_development(self) -> bool:
        return self.app_env.lower() == "development"


@lru_cache
def get_settings() -> Settings:
    """Cached singleton — imported everywhere as `from app.config import get_settings`."""
    return Settings()
