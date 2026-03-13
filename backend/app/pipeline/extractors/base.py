"""Base extractor interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import structlog

logger = structlog.get_logger()


@dataclass
class ExtractionResult:
    """Result from a data extraction operation."""

    source: str
    records: List[Dict[str, Any]]
    extracted_at: datetime = field(default_factory=datetime.utcnow)
    record_count: int = 0
    watermark: Optional[str] = None  # For incremental loading
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)

    def __post_init__(self):
        self.record_count = len(self.records)


class BaseExtractor(ABC):
    """Abstract base class for data extractors."""

    def __init__(self, config: Any):
        self.config = config
        self.logger = logger.bind(extractor=self.__class__.__name__)

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Name of the data source."""
        pass

    @abstractmethod
    async def extract(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        **kwargs,
    ) -> ExtractionResult:
        """
        Extract data from the source.

        Args:
            start_date: Start of date range (for incremental loading)
            end_date: End of date range
            **kwargs: Source-specific parameters

        Returns:
            ExtractionResult with records and metadata
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """Check if the data source is available."""
        pass

    async def extract_with_retry(
        self,
        max_retries: int = 3,
        **kwargs,
    ) -> ExtractionResult:
        """Extract with exponential backoff retry."""
        import asyncio

        last_error = None

        for attempt in range(max_retries):
            try:
                self.logger.info(
                    "extraction_attempt",
                    attempt=attempt + 1,
                    max_retries=max_retries,
                )
                result = await self.extract(**kwargs)
                self.logger.info(
                    "extraction_success",
                    record_count=result.record_count,
                    source=result.source,
                )
                return result

            except Exception as e:
                last_error = e
                wait_time = (2**attempt) * self.config.retry_delay_seconds
                self.logger.warning(
                    "extraction_retry",
                    attempt=attempt + 1,
                    error=str(e),
                    wait_seconds=wait_time,
                )
                await asyncio.sleep(wait_time)

        self.logger.error(
            "extraction_failed",
            max_retries=max_retries,
            error=str(last_error),
        )
        return ExtractionResult(
            source=self.source_name,
            records=[],
            errors=[f"Failed after {max_retries} attempts: {last_error}"],
        )
