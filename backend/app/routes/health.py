"""Health check endpoints."""

from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database.connection import async_session_factory, get_db

router = APIRouter()
settings = get_settings()


@router.get("/health")
async def health():
    """Basic health check."""
    return {"status": "ok", "version": settings.app_env}


@router.get("/health/live")
async def health_live():
    """Liveness probe - is the service running?"""
    return {"status": "live"}


@router.get("/health/ready")
async def health_ready(db: AsyncSession = Depends(get_db)):
    """Readiness probe - is the service ready to handle requests?"""
    checks = {
        "database": False,
        "llm": False,
    }

    # Check database connection
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = True
    except Exception:
        pass

    # Check LLM configuration
    try:
        if settings.anthropic_api_key or settings.openai_api_key:
            checks["llm"] = True
    except Exception:
        pass

    all_ready = all(checks.values())

    return {
        "status": "ready" if all_ready else "degraded",
        "checks": checks,
    }


@router.post("/admin/seed")
async def force_seed():
    """Manually trigger database seeding. Safe to call multiple times."""
    from ..database.init import seed_database

    try:
        async with async_session_factory() as session:
            seeded = await seed_database(session)
        return {"seeded": seeded, "message": "Seed complete" if seeded else "Already seeded"}
    except Exception as exc:
        return {"seeded": False, "error": str(exc), "type": type(exc).__name__}
