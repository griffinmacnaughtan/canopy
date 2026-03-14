"""Staging loader for temporary data storage before production load."""

import json
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger()


@dataclass
class LoadResult:
    """Result from a data load operation."""

    success: bool
    records_loaded: int
    records_failed: int
    destination: str
    load_time_seconds: float = 0
    errors: list[str] = field(default_factory=list)
    metadata: dict[str, Any] = field(default_factory=dict)


class StagingLoader:
    """
    Load data to staging area before production tables.

    The staging layer provides:
    - Data isolation during validation
    - Rollback capability if production load fails
    - Incremental load tracking via watermarks
    - Audit trail of all data changes

    For simplicity, uses JSON files as staging.
    In production, this would be a staging schema in Postgres.
    """

    def __init__(self, staging_dir: Path | None = None):
        self.staging_dir = staging_dir or Path(__file__).parent.parent.parent / "data" / "staging"
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self.logger = logger.bind(loader="staging")

    def load(
        self,
        records: list[dict[str, Any]],
        source: str,
        batch_id: str | None = None,
    ) -> LoadResult:
        """
        Load records to staging area.

        Args:
            records: Data records to stage
            source: Data source identifier
            batch_id: Optional batch identifier for tracking

        Returns:
            LoadResult with load statistics
        """
        start_time = datetime.utcnow()
        batch_id = batch_id or datetime.utcnow().strftime("%Y%m%d_%H%M%S")

        if not records:
            return LoadResult(
                success=True,
                records_loaded=0,
                records_failed=0,
                destination="staging",
                metadata={"batch_id": batch_id, "source": source},
            )

        try:
            # Create staging file
            staging_file = self.staging_dir / f"{source}_{batch_id}.json"

            staging_data = {
                "batch_id": batch_id,
                "source": source,
                "staged_at": datetime.utcnow().isoformat(),
                "record_count": len(records),
                "records": records,
            }

            with open(staging_file, "w") as f:
                json.dump(staging_data, f, indent=2, default=str)

            # Update watermark
            self._update_watermark(source, records)

            load_time = (datetime.utcnow() - start_time).total_seconds()

            self.logger.info(
                "staging_complete",
                source=source,
                batch_id=batch_id,
                records=len(records),
                file=str(staging_file),
            )

            return LoadResult(
                success=True,
                records_loaded=len(records),
                records_failed=0,
                destination=str(staging_file),
                load_time_seconds=load_time,
                metadata={
                    "batch_id": batch_id,
                    "source": source,
                    "staging_file": str(staging_file),
                },
            )

        except Exception as e:
            self.logger.error("staging_failed", error=str(e))
            return LoadResult(
                success=False,
                records_loaded=0,
                records_failed=len(records),
                destination="staging",
                errors=[str(e)],
            )

    def _update_watermark(self, source: str, records: list[dict[str, Any]]) -> None:
        """Update the watermark file for incremental loading."""
        watermark_file = self.staging_dir / "watermarks.json"

        # Load existing watermarks
        watermarks = {}
        if watermark_file.exists():
            with open(watermark_file) as f:
                watermarks = json.load(f)

        # Find the latest timestamp or date in records
        latest = None
        for record in records:
            for key in ["_extracted_at", "transformed_at", "observation_date", "reporting_year"]:
                value = record.get(key)
                if value:
                    if isinstance(value, int):
                        # Year field
                        candidate = str(value)
                    else:
                        candidate = str(value)
                    if latest is None or candidate > latest:
                        latest = candidate

        if latest:
            watermarks[source] = {
                "last_value": latest,
                "updated_at": datetime.utcnow().isoformat(),
            }

            with open(watermark_file, "w") as f:
                json.dump(watermarks, f, indent=2)

    def get_watermark(self, source: str) -> str | None:
        """Get the last watermark for a source (for incremental loading)."""
        watermark_file = self.staging_dir / "watermarks.json"

        if not watermark_file.exists():
            return None

        with open(watermark_file) as f:
            watermarks = json.load(f)

        source_wm = watermarks.get(source, {})
        return source_wm.get("last_value")

    def get_staged_batches(self, source: str | None = None) -> list[dict[str, Any]]:
        """List all staged batches, optionally filtered by source."""
        batches = []

        for file in self.staging_dir.glob("*.json"):
            if file.name == "watermarks.json":
                continue

            try:
                with open(file) as f:
                    data = json.load(f)

                if source and data.get("source") != source:
                    continue

                batches.append(
                    {
                        "file": str(file),
                        "batch_id": data.get("batch_id"),
                        "source": data.get("source"),
                        "staged_at": data.get("staged_at"),
                        "record_count": data.get("record_count"),
                    }
                )

            except (json.JSONDecodeError, KeyError):
                continue

        return sorted(batches, key=lambda x: x.get("staged_at", ""), reverse=True)

    def load_staged_batch(self, batch_file: str) -> list[dict[str, Any]]:
        """Load records from a staged batch file."""
        with open(batch_file) as f:
            data = json.load(f)
        return data.get("records", [])

    def clear_staged(self, source: str | None = None, before_date: datetime | None = None) -> int:
        """Clear staged files, optionally filtered by source or date."""
        cleared = 0

        for file in self.staging_dir.glob("*.json"):
            if file.name == "watermarks.json":
                continue

            try:
                with open(file) as f:
                    data = json.load(f)

                # Check source filter
                if source and data.get("source") != source:
                    continue

                # Check date filter
                if before_date:
                    staged_at = data.get("staged_at")
                    if staged_at:
                        file_date = datetime.fromisoformat(staged_at.replace("Z", "+00:00"))
                        if file_date >= before_date:
                            continue

                file.unlink()
                cleared += 1

            except (json.JSONDecodeError, KeyError, OSError):
                continue

        self.logger.info("staging_cleared", files=cleared, source=source)
        return cleared
