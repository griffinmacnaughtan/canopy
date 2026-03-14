"""Pytest configuration and shared fixtures."""

import asyncio
import os
from typing import AsyncGenerator, Generator, List

import pytest
from httpx import AsyncClient, ASGITransport

from app.models import Asset


# ---------------------------------------------------------------------------
# Environment — must be set before any app module is imported.
# ---------------------------------------------------------------------------

os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"
os.environ["APP_ENV"] = "test"
# Provide a placeholder key so settings validation passes;
# tests that exercise the copilot endpoint will get a 502 (LLM error) rather
# than an unrelated 503 (LLM not configured).
os.environ.setdefault("ANTHROPIC_API_KEY", "sk-test-placeholder")


# ---------------------------------------------------------------------------
# Event loop
# ---------------------------------------------------------------------------


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Single event loop shared across the whole test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


# ---------------------------------------------------------------------------
# Settings
# ---------------------------------------------------------------------------


@pytest.fixture
def settings():
    """Application settings (test overrides applied via env vars above)."""
    from app.config import get_settings
    return get_settings()


# ---------------------------------------------------------------------------
# Sample data
# ---------------------------------------------------------------------------


@pytest.fixture
def sample_assets() -> List[Asset]:
    """Multi-sector asset set for unit tests."""
    return [
        Asset(
            id="test-1",
            name="Test Tech Corp",
            sector="Information Technology",
            region="North America",
            revenue_usd_m=50_000,
            scope1_tco2e=25_000,
            scope2_tco2e=75_000,
            green_revenue_pct=35,
            controversies=0,
        ),
        Asset(
            id="test-2",
            name="Test Energy Inc",
            sector="Energy",
            region="North America",
            revenue_usd_m=100_000,
            scope1_tco2e=5_000_000,
            scope2_tco2e=1_000_000,
            green_revenue_pct=5,
            controversies=2,
        ),
        Asset(
            id="test-3",
            name="Test Utility Co",
            sector="Utilities",
            region="Europe",
            revenue_usd_m=20_000,
            scope1_tco2e=2_000_000,
            scope2_tco2e=500_000,
            green_revenue_pct=40,
            controversies=1,
        ),
    ]


# ---------------------------------------------------------------------------
# HTTP client
# ---------------------------------------------------------------------------


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """
    Async HTTP client wired to the FastAPI app.

    DB initialisation and seeding are performed eagerly (not as a background
    task) so that the database is fully ready before the first test runs.
    This prevents the "database is locked" errors that occur when a background
    asyncio.Task writes to SQLite at the same time as a test write.
    """
    from app.main import app
    from app.database.connection import init_db, async_session_factory
    from app.database.init import seed_database

    # Eagerly initialise and seed — no background task
    await init_db()
    async with async_session_factory() as session:
        await seed_database(session)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
