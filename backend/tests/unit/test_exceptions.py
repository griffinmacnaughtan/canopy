"""Tests for custom exception handling."""

from app.exceptions import (
    CanopyError,
    FileTooLargeError,
    LLMError,
    PortfolioNotFoundError,
    RateLimitExceededError,
    UnsupportedFileTypeError,
    ValidationError,
)


class TestCanopyError:
    """Tests for base CanopyError."""

    def test_default_values(self):
        """Test default error values."""
        error = CanopyError()

        assert error.status_code == 500
        assert error.error_code == "INTERNAL_ERROR"
        assert "unexpected" in error.message.lower()

    def test_custom_message(self):
        """Test custom error message."""
        error = CanopyError(message="Custom error occurred")

        assert error.message == "Custom error occurred"

    def test_to_dict(self):
        """Test error serialization."""
        error = CanopyError(message="Test error", details={"field": "value"})

        result = error.to_dict()

        assert result["error"] == "INTERNAL_ERROR"
        assert result["message"] == "Test error"
        assert result["details"] == {"field": "value"}


class TestValidationError:
    """Tests for ValidationError."""

    def test_status_code(self):
        """Test 400 status code."""
        error = ValidationError()

        assert error.status_code == 400
        assert error.error_code == "VALIDATION_ERROR"


class TestPortfolioNotFoundError:
    """Tests for PortfolioNotFoundError."""

    def test_error_message(self):
        """Test error message includes portfolio ID."""
        error = PortfolioNotFoundError("abc-123")

        assert error.status_code == 404
        assert "abc-123" in error.message
        assert error.details["portfolio_id"] == "abc-123"


class TestFileTooLargeError:
    """Tests for FileTooLargeError."""

    def test_default_size(self):
        """Test default max size."""
        error = FileTooLargeError()

        assert error.status_code == 413
        assert "10MB" in error.message

    def test_custom_size(self):
        """Test custom max size."""
        error = FileTooLargeError(max_size_mb=5)

        assert "5MB" in error.message
        assert error.details["max_size_mb"] == 5


class TestUnsupportedFileTypeError:
    """Tests for UnsupportedFileTypeError."""

    def test_error_details(self):
        """Test error includes filename and supported types."""
        error = UnsupportedFileTypeError("document.docx", ["pdf", "txt"])

        assert error.status_code == 415
        assert "document.docx" in error.message
        assert error.details["filename"] == "document.docx"
        assert error.details["supported_types"] == ["pdf", "txt"]


class TestRateLimitExceededError:
    """Tests for RateLimitExceededError."""

    def test_retry_after(self):
        """Test retry-after information."""
        error = RateLimitExceededError(retry_after=120)

        assert error.status_code == 429
        assert "120" in error.message
        assert error.details["retry_after_seconds"] == 120


class TestLLMError:
    """Tests for LLMError."""

    def test_status_code(self):
        """Test 502 status code."""
        error = LLMError()

        assert error.status_code == 502
        assert error.error_code == "LLM_ERROR"
