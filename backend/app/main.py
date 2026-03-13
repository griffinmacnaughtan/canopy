"""
FastAPI application for Canopy - Climate Risk Intelligence Platform.

This is the main entry point for the API. Routes are organized into modules
under app/routes/ for maintainability.
"""

from contextlib import asynccontextmanager
import structlog

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from .database.connection import init_db, async_session_factory
from .database.init import seed_database
from .config import get_settings
from .routes import register_routes
from .exceptions import CanopyError

# Initialize
settings = get_settings()
logger = structlog.get_logger()

# Rate limiter
limiter = Limiter(key_func=get_remote_address)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Initialize database on startup."""
    logger.info("startup_begin", env=settings.app_env)

    try:
        await init_db()

        # Seed with initial data if empty
        async with async_session_factory() as session:
            await seed_database(session)

        logger.info("startup_complete", database="ready")
    except Exception as exc:
        logger.error("startup_db_error", error=str(exc), error_type=type(exc).__name__)
        logger.warning("startup_continuing_without_db")

    yield
    logger.info("shutdown_complete")


# Create app
app = FastAPI(
    title="Canopy",
    version="2.2.0",
    description="Climate risk intelligence platform for finance teams",
    lifespan=lifespan,
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
)

# Add rate limiter to app state
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)


# =============================================================================
# Exception Handlers
# =============================================================================


@app.exception_handler(CanopyError)
async def canopy_error_handler(request: Request, exc: CanopyError):
    """Handle custom Canopy exceptions."""
    logger.warning(
        "api_error",
        error_code=exc.error_code,
        message=exc.message,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


@app.exception_handler(Exception)
async def generic_error_handler(request: Request, exc: Exception):
    """Handle unexpected exceptions."""
    logger.error(
        "unhandled_error",
        error=str(exc),
        error_type=type(exc).__name__,
        path=request.url.path,
    )

    # Don't expose internal errors in production
    if settings.is_production:
        return JSONResponse(
            status_code=500,
            content={
                "error": "INTERNAL_ERROR",
                "message": "An unexpected error occurred",
            },
        )

    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": str(exc),
            "type": type(exc).__name__,
        },
    )


# =============================================================================
# Middleware
# =============================================================================


@app.middleware("http")
async def request_logging_middleware(request: Request, call_next):
    """Log all requests with timing."""
    import time

    # Skip health check logging
    if request.url.path.startswith("/health"):
        return await call_next(request)

    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    logger.info(
        "request",
        method=request.method,
        path=request.url.path,
        status=response.status_code,
        duration_ms=round(duration_ms, 2),
        client_ip=get_remote_address(request),
    )

    return response


# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# =============================================================================
# Routes
# =============================================================================

# Register all route modules
register_routes(app)


# =============================================================================
# Static Files
# =============================================================================

# Mount static files last to avoid route conflicts
try:
    app.mount("/", StaticFiles(directory="static", html=True), name="static")
except Exception:
    pass  # Static files directory may not exist in Docker/dev


# =============================================================================
# Application Info
# =============================================================================

@app.get("/info")
async def app_info():
    """Get application info (useful for debugging)."""
    return {
        "name": "Canopy",
        "version": "2.2.0",
        "environment": settings.app_env,
        "llm_provider": settings.llm_provider,
        "debug": settings.debug,
    }
