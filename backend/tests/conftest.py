"""Pytest configuration and shared fixtures."""

import asyncio
import os
from typing import AsyncGenerator, Generator, List

import pytest
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool

from app.config import get_settings
from app.database.models import Base
from app.models import Asset


# Use in-memory SQLite for tests
os.environ["DATABASE_URL"] = "sqlite+aiosqlite:///:memory:"


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create an event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def settings():
    """Get application settings."""
    return get_settings()


@pytest.fixture
def sample_assets() -> List[Asset]:
    """Provide sample assets for testing."""
    return [
        Asset(
            id="test-1",
            name="Test Tech Corp",
            sector="Information Technology",
            region="North America",
            revenue_usd_m=50000,
            scope1_tco2e=25000,
            scope2_tco2e=75000,
            green_revenue_pct=35,
            controversies=0,
        ),
        Asset(
            id="test-2",
            name="Test Energy Inc",
            sector="Energy",
            region="North America",
            revenue_usd_m=100000,
            scope1_tco2e=5000000,
            scope2_tco2e=1000000,
            green_revenue_pct=5,
            controversies=2,
        ),
        Asset(
            id="test-3",
            name="Test Utility Co",
            sector="Utilities",
            region="Europe",
            revenue_usd_m=20000,
            scope1_tco2e=2000000,
            scope2_tco2e=500000,
            green_revenue_pct=40,
            controversies=1,
        ),
    ]


@pytest.fixture
async def async_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for API testing.

    Manually runs the lifespan context manager to initialize the database.
    """
    from contextlib import asynccontextmanager
    from app.main import app, lifespan

    # Run the lifespan startup
    @asynccontextmanager
    async def lifespan_context():
        async with lifespan(app):
            yield

    async with lifespan_context():
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            yield client
