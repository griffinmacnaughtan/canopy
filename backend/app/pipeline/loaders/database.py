"""Database loader using SQLAlchemy ORM - works with SQLite and PostgreSQL."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional
import json
import structlog

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ...database.pipeline_models import ClimateData, EmissionsData, PipelineRun
from .staging import LoadResult

logger = structlog.get_logger()


class DatabaseLoader:
    """
    Load pipeline data using SQLAlchemy ORM.

    Works with both SQLite (local dev) and PostgreSQL (production).
    Uses the app's existing database connection.
    """

    def __init__(self, session: AsyncSession):
        self.session = session
        self.logger = logger.bind(loader="database")

    async def load_emissions(
        self,
        records: List[Dict[str, Any]],
    ) -> LoadResult:
        """Load emissions records to database."""
        start_time = datetime.utcnow()
        loaded = 0
        failed = 0
        errors = []

        for record in records:
            try:
                # Check if exists (upsert logic)
                existing = await self.session.execute(
                    select(EmissionsData).where(
                        EmissionsData.facility_id == record.get("facility_id"),
                        EmissionsData.reporting_year == record.get("reporting_year"),
                    )
                )
                existing_record = existing.scalar_one_or_none()

                if existing_record:
                    # Update existing
                    for key, value in record.items():
                        if hasattr(existing_record, key) and value is not None:
                            setattr(existing_record, key, value)
                    existing_record.loaded_at = datetime.utcnow()
                else:
                    # Insert new
                    db_record = EmissionsData(
                        facility_id=record.get("facility_id"),
                        facility_name=record.get("facility_name"),
                        city=record.get("city"),
                        state=record.get("state"),
                        region=record.get("region"),
                        industry_type=record.get("industry_type"),
                        sector=record.get("sector"),
                        naics_code=record.get("naics_code"),
                        latitude=record.get("latitude"),
                        longitude=record.get("longitude"),
                        reporting_year=record.get("reporting_year"),
                        total_emissions_mt_co2e=record.get("total_emissions_mt_co2e"),
                        co2_emissions_mt=record.get("co2_emissions_mt"),
                        methane_emissions_mt_co2e=record.get("methane_emissions_mt_co2e"),
                        n2o_emissions_mt_co2e=record.get("n2o_emissions_mt_co2e"),
                        emissions_scope=record.get("emissions_scope"),
                        source=record.get("source", "unknown"),
                        transformed_at=self._parse_datetime(record.get("transformed_at")),
                        loaded_at=datetime.utcnow(),
                    )
                    self.session.add(db_record)

                loaded += 1

            except Exception as e:
                failed += 1
                errors.append(f"Record {record.get('facility_id')}: {str(e)}")

        await self.session.commit()

        load_time = (datetime.utcnow() - start_time).total_seconds()

        self.logger.info(
            "emissions_loaded",
            loaded=loaded,
            failed=failed,
            time_seconds=load_time,
        )

        return LoadResult(
            success=failed == 0,
            records_loaded=loaded,
            records_failed=failed,
            destination="database:emissions_data",
            load_time_seconds=load_time,
            errors=errors[:10],
        )

    async def load_climate(
        self,
        records: List[Dict[str, Any]],
    ) -> LoadResult:
        """Load climate records to database."""
        start_time = datetime.utcnow()
        loaded = 0
        failed = 0
        errors = []

        for record in records:
            try:
                db_record = ClimateData(
                    location_id=record.get("location_id"),
                    country_code=record.get("country_code"),
                    state_code=record.get("state_code"),
                    region=record.get("region"),
                    observation_date=self._parse_datetime(record.get("observation_date")),
                    year=record.get("year"),
                    month=record.get("month"),
                    metric_name=record.get("metric_name"),
                    metric_type=record.get("metric_type"),
                    value=record.get("value") or record.get("annual_mean"),
                    unit=record.get("unit"),
                    scenario=record.get("scenario"),
                    period_start=record.get("period_start"),
                    period_end=record.get("period_end"),
                    station_id=record.get("station_id"),
                    source=record.get("source", "unknown"),
                    transformed_at=self._parse_datetime(record.get("transformed_at")),
                    loaded_at=datetime.utcnow(),
                )
                self.session.add(db_record)
                loaded += 1

            except Exception as e:
                failed += 1
                errors.append(f"Climate record: {str(e)}")

        await self.session.commit()

        load_time = (datetime.utcnow() - start_time).total_seconds()

        self.logger.info(
            "climate_loaded",
            loaded=loaded,
            failed=failed,
            time_seconds=load_time,
        )

        return LoadResult(
            success=failed == 0,
            records_loaded=loaded,
            records_failed=failed,
            destination="database:climate_data",
            load_time_seconds=load_time,
            errors=errors[:10],
        )

    async def record_pipeline_run(
        self,
        run_id: str,
        status: str,
        records_extracted: int = 0,
        records_transformed: int = 0,
        records_loaded: int = 0,
        sources: Optional[List[str]] = None,
        errors: Optional[List[str]] = None,
        started_at: Optional[datetime] = None,
    ) -> PipelineRun:
        """Record a pipeline run in the database."""
        run = PipelineRun(
            run_id=run_id,
            status=status,
            started_at=started_at or datetime.utcnow(),
            completed_at=datetime.utcnow() if status in ("success", "failed") else None,
            records_extracted=records_extracted,
            records_transformed=records_transformed,
            records_loaded=records_loaded,
            sources=json.dumps(sources) if sources else None,
            errors=json.dumps(errors[:10]) if errors else None,
            triggered_by="manual",
        )

        self.session.add(run)
        await self.session.commit()

        return run

    def _parse_datetime(self, value: Any) -> Optional[datetime]:
        """Parse datetime from various formats."""
        if value is None:
            return None
        if isinstance(value, datetime):
            return value
        if isinstance(value, str):
            try:
                return datetime.fromisoformat(value.replace("Z", "+00:00"))
            except ValueError:
                return None
        return None
