"""Base transformer interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List
import structlog

logger = structlog.get_logger()


@dataclass
class TransformResult:
    """Result from a data transformation."""
    records: List[Dict[str, Any]]
    source: str
    transformed_at: datetime = field(default_factory=datetime.utcnow)
    input_count: int = 0
    output_count: int = 0
    dropped_count: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        self.output_count = len(self.records)


class BaseTransformer(ABC):
    """Abstract base class for data transformers."""

    def __init__(self):
        self.logger = logger.bind(transformer=self.__class__.__name__)

    @property
    @abstractmethod
    def name(self) -> str:
        """Transformer name for logging."""
        pass

    @abstractmethod
    def transform(self, records: List[Dict[str, Any]]) -> TransformResult:
        """
        Transform a list of records.

        Args:
            records: Raw records from extractor

        Returns:
            TransformResult with cleaned/enriched records
        """
        pass

    def _safe_float(self, value: Any, default: float = 0.0) -> float:
        """Safely convert to float."""
        if value is None:
            return default
        try:
            return float(value)
        except (ValueError, TypeError):
            return default

    def _safe_int(self, value: Any, default: int = 0) -> int:
        """Safely convert to int."""
        if value is None:
            return default
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return default

    def _normalize_string(self, value: Any) -> str:
        """Normalize string values."""
        if value is None:
            return ""
        return str(value).strip()

    def _parse_date(self, value: Any) -> datetime | None:
        """Parse various date formats."""
        if value is None:
            return None

        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            formats = [
                "%Y-%m-%d",
                "%Y-%m-%dT%H:%M:%S",
                "%Y-%m-%dT%H:%M:%SZ",
                "%Y-%m-%d %H:%M:%S",
                "%Y%m%d",
            ]
            for fmt in formats:
                try:
                    return datetime.strptime(value[:len(fmt) + 2], fmt)
                except (ValueError, IndexError):
                    continue

        return None
