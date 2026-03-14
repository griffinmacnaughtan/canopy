"""Application configuration using Pydantic Settings."""

from functools import lru_cache
from pathlib import Path
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


# Default to SQLite in the backend directory for zero-config local dev
_DEFAULT_DB_PATH = Path(__file__).parent.parent / "data" / "canopy.db"
_DEFAULT_SQLITE_URL = f"sqlite+aiosqlite:///{_DEFAULT_DB_PATH}"


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Application
    # Use plain str (not Literal) so unexpected Railway values like "Production"
    # or "prod" don't cause a Pydantic ValidationError crash at startup.
    app_env: str = "development"
    debug: bool = True
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # CORS - comma-separated list of allowed origins, or "*" for all
    # In production set to your GitHub Pages URL, e.g.:
    #   CORS_ORIGINS=https://yourusername.github.io
    cors_origins: str = "*"

    @property
    def allowed_origins(self) -> List[str]:
        """Parse CORS_ORIGINS env var into a list for FastAPI middleware."""
        if self.cors_origins.strip() == "*":
            return ["*"]
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]

    # Database - defaults to SQLite for zero-config local dev
    # Set DATABASE_URL env var for PostgreSQL in production
    database_url: str = _DEFAULT_SQLITE_URL
    database_sync_url: str = ""  # Computed property handles this

    @property
    def is_sqlite(self) -> bool:
        return "sqlite" in self.database_url

    @property
    def effective_database_url(self) -> str:
        """Async database URL, normalizing bare postgresql:// or postgres:// from Railway."""
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgres://"):
            # Railway sometimes provides postgres:// (SQLAlchemy 2.x removed this alias)
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        return url

    @property
    def effective_sync_url(self) -> str:
        """Sync database URL for Alembic migrations."""
        if self.database_sync_url:
            return self.database_sync_url
        if self.is_sqlite:
            # Convert async sqlite URL to sync
            return self.database_url.replace("sqlite+aiosqlite", "sqlite")
        # Normalise bare postgresql:// or postgres:// from Railway, then swap driver
        url = self.database_url
        if url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+psycopg2://", 1)
        elif url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+psycopg2://", 1)
        return url.replace("postgresql+asyncpg", "postgresql+psycopg2")

    # LLM Provider
    llm_provider: str = "anthropic"
    anthropic_api_key: str = ""
    openai_api_key: str = ""

    # LLM Models
    anthropic_model: str = "claude-sonnet-4-20250514"
    openai_model: str = "gpt-4o"

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    @property
    def is_production(self) -> bool:
        return self.app_env == "production"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance."""
    return Settings()
