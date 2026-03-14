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


async def _migrate_postgres_schema(conn) -> None:
    """Add missing columns to existing tables (idempotent, PostgreSQL only).

    create_all() only creates *missing* tables; it never alters columns on
    existing ones.  This function fills the gap for schema evolution without
    requiring a full Alembic setup.  Every statement uses IF NOT EXISTS so it
    is safe to run on every startup.
    """
    from sqlalchemy import text

    statements = [
        # portfolios: description + is_sample + user_id added after initial deploy
        "ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS description TEXT",
        "ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS is_sample BOOLEAN NOT NULL DEFAULT FALSE",
        "ALTER TABLE portfolios ADD COLUMN IF NOT EXISTS user_id UUID",
        # Add FK constraint only if it doesn't already exist
        """DO $$ BEGIN
            IF NOT EXISTS (
                SELECT 1 FROM pg_constraint WHERE conname = 'portfolios_user_id_fkey'
            ) THEN
                ALTER TABLE portfolios
                    ADD CONSTRAINT portfolios_user_id_fkey
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
            END IF;
        END $$""",
    ]
    for sql in statements:
        await conn.execute(text(sql))


async def init_db():
    """Initialize the database on startup.

    Creates all tables using SQLAlchemy metadata (checkfirst=True, so existing
    tables are left untouched). Works for both SQLite and PostgreSQL.
    After create_all, runs lightweight column migrations so that schema
    changes made after the initial deploy are applied automatically.
    """
    from .models import Base
    # Import pipeline models to ensure their tables are created
    from . import pipeline_models  # noqa: F401

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        if not settings.is_sqlite:
            await _migrate_postgres_schema(conn)


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
