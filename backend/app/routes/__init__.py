"""API routes for Canopy."""

from .agents import router as agents_router
from .copilot import router as copilot_router
from .documents import router as documents_router
from .evals import router as evals_router
from .health import router as health_router
from .pipeline import router as pipeline_router
from .portfolios import router as portfolios_router
from .scoring import router as scoring_router


def register_routes(app):
    """Register all route modules with the FastAPI app."""
    app.include_router(health_router, tags=["Health"])
    app.include_router(portfolios_router, tags=["Portfolios"])
    app.include_router(scoring_router, tags=["Scoring"])
    app.include_router(documents_router, tags=["Documents"])
    app.include_router(copilot_router, tags=["Copilot"])
    app.include_router(agents_router, tags=["Agent"])
    app.include_router(evals_router, tags=["Evals"])
    app.include_router(pipeline_router)


__all__ = [
    "register_routes",
    "health_router",
    "portfolios_router",
    "scoring_router",
    "documents_router",
    "copilot_router",
    "agents_router",
    "evals_router",
]
