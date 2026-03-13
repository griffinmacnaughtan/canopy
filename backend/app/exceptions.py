"""Custom exceptions for Canopy API.

Provides structured error handling with consistent error codes and messages.
"""

from typing import Any, Dict, Optional


class CanopyError(Exception):
    """Base exception for all Canopy errors."""

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"
    message: str = "An unexpected error occurred"

    def __init__(
        self,
        message: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        self.message = message or self.__class__.message
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to API response format."""
        result = {
            "error": self.error_code,
            "message": self.message,
        }
        if self.details:
            result["details"] = self.details
        return result


# =============================================================================
# Client Errors (4xx)
# =============================================================================


class ValidationError(CanopyError):
    """Invalid input data."""

    status_code = 400
    error_code = "VALIDATION_ERROR"
    message = "Invalid input data"


class PortfolioNotFoundError(CanopyError):
    """Portfolio does not exist."""

    status_code = 404
    error_code = "PORTFOLIO_NOT_FOUND"
    message = "Portfolio not found"

    def __init__(self, portfolio_id: str):
        super().__init__(
            message=f"Portfolio '{portfolio_id}' not found",
            details={"portfolio_id": portfolio_id},
        )


class AssetNotFoundError(CanopyError):
    """Asset does not exist."""

    status_code = 404
    error_code = "ASSET_NOT_FOUND"
    message = "Asset not found"


class ScenarioNotFoundError(CanopyError):
    """Scenario does not exist."""

    status_code = 404
    error_code = "SCENARIO_NOT_FOUND"
    message = "Scenario not found"


class DocumentError(CanopyError):
    """Document processing error."""

    status_code = 400
    error_code = "DOCUMENT_ERROR"
    message = "Failed to process document"


class FileTooLargeError(CanopyError):
    """Uploaded file exceeds size limit."""

    status_code = 413
    error_code = "FILE_TOO_LARGE"
    message = "File exceeds maximum size limit"

    def __init__(self, max_size_mb: int = 10):
        super().__init__(
            message=f"File exceeds maximum size of {max_size_mb}MB",
            details={"max_size_mb": max_size_mb},
        )


class UnsupportedFileTypeError(CanopyError):
    """Uploaded file type is not supported."""

    status_code = 415
    error_code = "UNSUPPORTED_FILE_TYPE"
    message = "File type not supported"

    def __init__(self, filename: str, supported_types: list = None):
        super().__init__(
            message=f"File type not supported: {filename}",
            details={
                "filename": filename,
                "supported_types": supported_types or ["pdf"],
            },
        )


class RateLimitExceededError(CanopyError):
    """Too many requests."""

    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"
    message = "Too many requests. Please try again later."

    def __init__(self, retry_after: int = 60):
        super().__init__(
            message=f"Rate limit exceeded. Retry after {retry_after} seconds.",
            details={"retry_after_seconds": retry_after},
        )


class InvalidPortfolioIdError(CanopyError):
    """Portfolio ID format is invalid."""

    status_code = 400
    error_code = "INVALID_PORTFOLIO_ID"
    message = "Invalid portfolio ID format"

    def __init__(self, portfolio_id: str):
        super().__init__(
            message=f"Invalid portfolio ID format: {portfolio_id}",
            details={"portfolio_id": portfolio_id, "expected_format": "UUID"},
        )


# =============================================================================
# Server Errors (5xx)
# =============================================================================


class LLMError(CanopyError):
    """LLM provider error."""

    status_code = 502
    error_code = "LLM_ERROR"
    message = "AI service temporarily unavailable"


class LLMConfigurationError(CanopyError):
    """LLM not configured properly."""

    status_code = 503
    error_code = "LLM_NOT_CONFIGURED"
    message = "AI service not configured"


class DatabaseError(CanopyError):
    """Database operation failed."""

    status_code = 503
    error_code = "DATABASE_ERROR"
    message = "Database operation failed"
