"""Structured logging configuration for ESG Copilot."""

import logging
import sys
from typing import Any

import structlog
from structlog.typing import Processor

from .config import get_settings


def setup_logging() -> None:
    """Configure structured logging for the application."""
    settings = get_settings()

    # Determine log level
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)

    # Shared processors for all environments
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if settings.log_format == "json":
        # JSON format for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Console format for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=log_level,
    )

    # Set third-party loggers to WARNING
    for logger_name in ["uvicorn", "uvicorn.access", "sqlalchemy.engine"]:
        logging.getLogger(logger_name).setLevel(logging.WARNING)


def get_logger(name: str = __name__) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name, typically __name__.

    Returns:
        A configured structlog logger.
    """
    return structlog.get_logger(name)


class RequestLoggingMiddleware:
    """Middleware to log all HTTP requests."""

    def __init__(self, app: Any) -> None:
        self.app = app
        self.logger = get_logger("http")

    async def __call__(self, scope: dict, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        import time

        start_time = time.perf_counter()

        # Extract request info
        method = scope["method"]
        path = scope["path"]
        client = scope.get("client", ("unknown", 0))
        client_ip = client[0] if client else "unknown"

        # Track response status
        response_status = 0

        async def send_wrapper(message: dict) -> None:
            nonlocal response_status
            if message["type"] == "http.response.start":
                response_status = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, send_wrapper)
        finally:
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Skip health check logs to reduce noise
            if path.startswith("/health"):
                return

            self.logger.info(
                "request",
                method=method,
                path=path,
                status=response_status,
                duration_ms=round(duration_ms, 2),
                client_ip=client_ip,
            )
