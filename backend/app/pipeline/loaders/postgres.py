"""PostgreSQL loader for production data."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Type
import structlog
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.dialects.postgresql import insert as pg_insert

from .staging import LoadResult

logger = structlog.get_logger()


class PostgresLoader:
    """
    Load data from staging to production PostgreSQL tables.

    Features:
    - Upsert (insert or update on conflict)
    - Batch loading for performance
    - Transaction management
    - Incremental updates
    """

    def __init__(self, database_url: str, batch_size: int = 1000):
        self.database_url = database_url
        self.batch_size = batch_size
        self.logger = logger.bind(loader="postgres")

        # Create async engine
        self.engine = create_async_engine(
            database_url,
            echo=False,
            pool_size=5,
            max_overflow=10,
        )
        self.session_factory = async_sessionmaker(
            self.engine,
            class_=AsyncSession,
            expire_on_commit=False,
        )

    async def load_climate_data(
        self,
        records: List[Dict[str, Any]],
        upsert: bool = True,
    ) -> LoadResult:
        """
        Load climate data to production table.

        Creates table if it doesn't exist.
        """
        start_time = datetime.utcnow()
        loaded = 0
        failed = 0
        errors = []

        async with self.session_factory() as session:
            try:
                # Ensure table exists
                await self._ensure_climate_table(session)

                # Load in batches
                for i in range(0, len(records), self.batch_size):
                    batch = records[i:i + self.batch_size]
                    try:
                        if upsert:
                            await self._upsert_climate_batch(session, batch)
                        else:
                            await self._insert_climate_batch(session, batch)
                        loaded += len(batch)
                    except Exception as e:
                        failed += len(batch)
                        errors.append(f"Batch {i//self.batch_size}: {str(e)}")

                await session.commit()

            except Exception as e:
                await session.rollback()
                self.logger.error("load_failed", error=str(e))
                return LoadResult(
                    success=False,
                    records_loaded=0,
                    records_failed=len(records),
                    destination="postgres:climate_data",
                    errors=[str(e)],
                )

        load_time = (datetime.utcnow() - start_time).total_seconds()

        self.logger.info(
            "load_complete",
            table="climate_data",
            loaded=loaded,
            failed=failed,
            time_seconds=load_time,
        )

        return LoadResult(
            success=failed == 0,
            records_loaded=loaded,
            records_failed=failed,
            destination="postgres:climate_data",
            load_time_seconds=load_time,
            errors=errors,
        )

    async def load_emissions_data(
        self,
        records: List[Dict[str, Any]],
        upsert: bool = True,
    ) -> LoadResult:
        """Load emissions data to production table."""
        start_time = datetime.utcnow()
        loaded = 0
        failed = 0
        errors = []

        async with self.session_factory() as session:
            try:
                await self._ensure_emissions_table(session)

                for i in range(0, len(records), self.batch_size):
                    batch = records[i:i + self.batch_size]
                    try:
                        if upsert:
                            await self._upsert_emissions_batch(session, batch)
                        else:
                            await self._insert_emissions_batch(session, batch)
                        loaded += len(batch)
                    except Exception as e:
                        failed += len(batch)
                        errors.append(f"Batch {i//self.batch_size}: {str(e)}")

                await session.commit()

            except Exception as e:
                await session.rollback()
                return LoadResult(
                    success=False,
                    records_loaded=0,
                    records_failed=len(records),
                    destination="postgres:emissions_data",
                    errors=[str(e)],
                )

        load_time = (datetime.utcnow() - start_time).total_seconds()

        return LoadResult(
            success=failed == 0,
            records_loaded=loaded,
            records_failed=failed,
            destination="postgres:emissions_data",
            load_time_seconds=load_time,
            errors=errors,
        )

    async def _ensure_climate_table(self, session: AsyncSession) -> None:
        """Create climate_data table if it doesn't exist."""
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS climate_data (
                id SERIAL PRIMARY KEY,
                observation_date DATE,
                year INTEGER,
                month INTEGER,
                metric_name VARCHAR(100),
                metric_type VARCHAR(50),
                value DECIMAL(12, 4),
                unit VARCHAR(50),
                station_id VARCHAR(100),
                location_id VARCHAR(100),
                state_code VARCHAR(10),
                region VARCHAR(50),
                country_code VARCHAR(10),
                scenario VARCHAR(50),
                period_start INTEGER,
                period_end INTEGER,
                source VARCHAR(100),
                transformed_at TIMESTAMP,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(location_id, observation_date, metric_type, source)
            )
        """))

        # Create indexes
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_climate_date ON climate_data(observation_date)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_climate_location ON climate_data(location_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_climate_metric ON climate_data(metric_name)
        """))

    async def _ensure_emissions_table(self, session: AsyncSession) -> None:
        """Create emissions_data table if it doesn't exist."""
        await session.execute(text("""
            CREATE TABLE IF NOT EXISTS emissions_data (
                id SERIAL PRIMARY KEY,
                facility_id VARCHAR(100),
                facility_name VARCHAR(500),
                state VARCHAR(10),
                city VARCHAR(200),
                region VARCHAR(50),
                industry_type VARCHAR(200),
                sector VARCHAR(100),
                reporting_year INTEGER,
                total_emissions_mt_co2e DECIMAL(15, 4),
                co2_emissions_mt DECIMAL(15, 4),
                methane_emissions_mt_co2e DECIMAL(15, 4),
                n2o_emissions_mt_co2e DECIMAL(15, 4),
                emissions_scope VARCHAR(50),
                latitude DECIMAL(10, 6),
                longitude DECIMAL(10, 6),
                naics_code VARCHAR(20),
                source VARCHAR(100),
                transformed_at TIMESTAMP,
                loaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(facility_id, reporting_year, source)
            )
        """))

        # Create indexes
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_emissions_facility ON emissions_data(facility_id)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_emissions_sector ON emissions_data(sector)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_emissions_year ON emissions_data(reporting_year)
        """))
        await session.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_emissions_state ON emissions_data(state)
        """))

    async def _upsert_climate_batch(
        self,
        session: AsyncSession,
        records: List[Dict[str, Any]],
    ) -> None:
        """Upsert climate records (insert or update on conflict)."""
        for record in records:
            await session.execute(text("""
                INSERT INTO climate_data (
                    observation_date, year, month, metric_name, metric_type,
                    value, unit, station_id, location_id, state_code, region,
                    country_code, scenario, period_start, period_end, source, transformed_at
                ) VALUES (
                    :observation_date, :year, :month, :metric_name, :metric_type,
                    :value, :unit, :station_id, :location_id, :state_code, :region,
                    :country_code, :scenario, :period_start, :period_end, :source, :transformed_at
                )
                ON CONFLICT (location_id, observation_date, metric_type, source)
                DO UPDATE SET
                    value = EXCLUDED.value,
                    transformed_at = EXCLUDED.transformed_at,
                    loaded_at = CURRENT_TIMESTAMP
            """), {
                "observation_date": record.get("observation_date"),
                "year": record.get("year"),
                "month": record.get("month"),
                "metric_name": record.get("metric_name"),
                "metric_type": record.get("metric_type"),
                "value": record.get("value") or record.get("annual_mean"),
                "unit": record.get("unit"),
                "station_id": record.get("station_id"),
                "location_id": record.get("location_id") or record.get("country_code"),
                "state_code": record.get("state_code"),
                "region": record.get("region"),
                "country_code": record.get("country_code"),
                "scenario": record.get("scenario"),
                "period_start": record.get("period_start"),
                "period_end": record.get("period_end"),
                "source": record.get("source"),
                "transformed_at": record.get("transformed_at"),
            })

    async def _insert_climate_batch(
        self,
        session: AsyncSession,
        records: List[Dict[str, Any]],
    ) -> None:
        """Insert climate records (ignore conflicts)."""
        for record in records:
            try:
                await session.execute(text("""
                    INSERT INTO climate_data (
                        observation_date, year, month, metric_name, metric_type,
                        value, unit, station_id, location_id, state_code, region,
                        source, transformed_at
                    ) VALUES (
                        :observation_date, :year, :month, :metric_name, :metric_type,
                        :value, :unit, :station_id, :location_id, :state_code, :region,
                        :source, :transformed_at
                    )
                    ON CONFLICT DO NOTHING
                """), record)
            except Exception:
                pass  # Skip duplicates

    async def _upsert_emissions_batch(
        self,
        session: AsyncSession,
        records: List[Dict[str, Any]],
    ) -> None:
        """Upsert emissions records."""
        for record in records:
            await session.execute(text("""
                INSERT INTO emissions_data (
                    facility_id, facility_name, state, city, region,
                    industry_type, sector, reporting_year,
                    total_emissions_mt_co2e, co2_emissions_mt,
                    methane_emissions_mt_co2e, n2o_emissions_mt_co2e,
                    emissions_scope, latitude, longitude, naics_code,
                    source, transformed_at
                ) VALUES (
                    :facility_id, :facility_name, :state, :city, :region,
                    :industry_type, :sector, :reporting_year,
                    :total_emissions_mt_co2e, :co2_emissions_mt,
                    :methane_emissions_mt_co2e, :n2o_emissions_mt_co2e,
                    :emissions_scope, :latitude, :longitude, :naics_code,
                    :source, :transformed_at
                )
                ON CONFLICT (facility_id, reporting_year, source)
                DO UPDATE SET
                    facility_name = EXCLUDED.facility_name,
                    total_emissions_mt_co2e = EXCLUDED.total_emissions_mt_co2e,
                    transformed_at = EXCLUDED.transformed_at,
                    loaded_at = CURRENT_TIMESTAMP
            """), {
                "facility_id": record.get("facility_id"),
                "facility_name": record.get("facility_name"),
                "state": record.get("state"),
                "city": record.get("city"),
                "region": record.get("region"),
                "industry_type": record.get("industry_type"),
                "sector": record.get("sector"),
                "reporting_year": record.get("reporting_year"),
                "total_emissions_mt_co2e": record.get("total_emissions_mt_co2e"),
                "co2_emissions_mt": record.get("co2_emissions_mt"),
                "methane_emissions_mt_co2e": record.get("methane_emissions_mt_co2e"),
                "n2o_emissions_mt_co2e": record.get("n2o_emissions_mt_co2e"),
                "emissions_scope": record.get("emissions_scope"),
                "latitude": record.get("latitude"),
                "longitude": record.get("longitude"),
                "naics_code": record.get("naics_code"),
                "source": record.get("source"),
                "transformed_at": record.get("transformed_at"),
            })

    async def _insert_emissions_batch(
        self,
        session: AsyncSession,
        records: List[Dict[str, Any]],
    ) -> None:
        """Insert emissions records."""
        for record in records:
            try:
                await session.execute(text("""
                    INSERT INTO emissions_data (
                        facility_id, facility_name, state, city, region,
                        industry_type, sector, reporting_year,
                        total_emissions_mt_co2e, source, transformed_at
                    ) VALUES (
                        :facility_id, :facility_name, :state, :city, :region,
                        :industry_type, :sector, :reporting_year,
                        :total_emissions_mt_co2e, :source, :transformed_at
                    )
                    ON CONFLICT DO NOTHING
                """), record)
            except Exception:
                pass

    async def get_latest_year(self, table: str) -> Optional[int]:
        """Get the latest reporting year in a table (for incremental loading)."""
        async with self.session_factory() as session:
            if table == "emissions_data":
                result = await session.execute(text(
                    "SELECT MAX(reporting_year) FROM emissions_data"
                ))
            elif table == "climate_data":
                result = await session.execute(text(
                    "SELECT MAX(year) FROM climate_data"
                ))
            else:
                return None

            row = result.fetchone()
            return row[0] if row and row[0] else None

    async def close(self) -> None:
        """Close database connections."""
        await self.engine.dispose()
