"""Async SQLAlchemy database connection."""

from pathlib import Path
from typing import AsyncGenerator

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool, StaticPool

from ..config import get_settings

settings = get_settings()


def _get_engine_kwargs():
    """Get engine kwargs based on database type."""
    kwargs = {
        "echo": settings.debug,
        "future": True,
    }

    if settings.is_sqlite:
        # SQLite needs StaticPool for async and check_same_thread=False
        kwargs["poolclass"] = StaticPool
        kwargs["connect_args"] = {"check_same_thread": False}
    else:
        # PostgreSQL via asyncpg: enforce a hard connect timeout at the driver
        # level.  asyncio.timeout() alone cannot interrupt an OS-level TCP
        # connect() call inside asyncpg, which means the lifespan can stall
        # indefinitely and uvicorn never binds the port within Railway's 100 s
        # healthcheck window.  asyncpg's native `timeout` parameter does not
        # depend on asyncio task cancellation.
        kwargs["connect_args"] = {"timeout": 10}  # seconds
        if settings.is_development:
            kwargs["poolclass"] = NullPool

    return kwargs


def _ensure_db_directory():
    """Create the database directory if using SQLite."""
    if settings.is_sqlite:
        # Extract path from URL like sqlite+aiosqlite:///path/to/db.db
        db_path = settings.database_url.split("///")[-1]
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)


# Ensure directory exists before creating engine
_ensure_db_directory()

engine = create_async_engine(
    settings.effective_database_url,
    **_get_engine_kwargs(),
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def init_db():
    """Initialize the database on startup.

    Creates all tables using SQLAlchemy metadata (checkfirst=True, so existing
    tables are left untouched). Works for both SQLite and PostgreSQL.
    """
    from .models import Base
    # Import pipeline models to ensure their tables are created
    from . import pipeline_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting async database sessions."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
