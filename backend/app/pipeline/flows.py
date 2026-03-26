"""
Prefect flows for climate data pipeline orchestration.

This module defines the main data pipeline flows using Prefect 2.x.
Flows can be scheduled, monitored, and run from the CLI or Prefect Cloud.

Usage:
    # Run once
    python -m app.pipeline.flows

    # Schedule with Prefect
    prefect deployment build app/pipeline/flows.py:climate_data_flow --name daily-climate
    prefect deployment apply climate_data_flow-deployment.yaml
"""

import asyncio
from datetime import datetime, timedelta

import structlog

try:
    from prefect import flow, get_run_logger, task
    from prefect.tasks import task_input_hash

    PREFECT_AVAILABLE = True
except ImportError:
    # Fallback for environments without Prefect
    PREFECT_AVAILABLE = False

    def flow(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def task(*args, **kwargs):
        def decorator(func):
            return func

        return decorator

    def get_run_logger():
        return structlog.get_logger()

    def task_input_hash(*args, **kwargs):
        return None


from .config import PipelineConfig
from .extractors import EPAExtractor, NOAAExtractor, SECEdgarExtractor, WorldBankClimateExtractor
from .loaders import DatabaseLoader, PostgresLoader, StagingLoader
from .transformers import ClimateDataTransformer, EmissionsDataTransformer
from .validators import DataQualityValidator, SchemaValidator

logger = structlog.get_logger()

# Import database session for app integration
_db_session_factory = None


def get_db_session_factory():
    """Lazy import of database session factory to avoid circular imports."""
    global _db_session_factory
    if _db_session_factory is None:
        try:
            from ..database.connection import async_session_factory

            _db_session_factory = async_session_factory
        except ImportError:
            pass
    return _db_session_factory


# ============================================================================
# TASKS
# ============================================================================


@task(
    name="extract_noaa_data",
    retries=3,
    retry_delay_seconds=60,
    cache_key_fn=task_input_hash if PREFECT_AVAILABLE else None,
    cache_expiration=timedelta(hours=6),
)
async def extract_noaa_data(
    config: PipelineConfig,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """Extract climate data from NOAA."""
    log = get_run_logger() if PREFECT_AVAILABLE else logger

    extractor = NOAAExtractor(config)

    if not await extractor.health_check():
        log.warning("NOAA API unavailable, skipping extraction")
        return {"source": "NOAA_CDO", "records": [], "status": "skipped"}

    result = await extractor.extract_with_retry(
        max_retries=config.max_retries,
        start_date=start_date,
        end_date=end_date,
    )

    log.info(f"NOAA extraction complete: {result.record_count} records")

    return {
        "source": result.source,
        "records": result.records,
        "watermark": result.watermark,
        "errors": result.errors,
        "status": "success" if not result.errors else "partial",
    }


@task(
    name="extract_epa_data",
    retries=3,
    retry_delay_seconds=60,
)
async def extract_epa_data(
    config: PipelineConfig,
    start_date: datetime | None = None,
    end_date: datetime | None = None,
):
    """Extract emissions data from EPA."""
    log = get_run_logger() if PREFECT_AVAILABLE else logger

    extractor = EPAExtractor(config)

    if not await extractor.health_check():
        log.warning("EPA API unavailable, skipping extraction")
        return {"source": "EPA_ENVIROFACTS", "records": [], "status": "skipped"}

    result = await extractor.extract_with_retry(
        max_retries=config.max_retries,
        start_date=start_date,
        end_date=end_date,
    )

    log.info(f"EPA extraction complete: {result.record_count} records")

    return {
        "source": result.source,
        "records": result.records,
        "watermark": result.watermark,
        "errors": result.errors,
        "status": "success" if not result.errors else "partial",
    }


@task(
    name="extract_worldbank_data",
    retries=2,
    retry_delay_seconds=30,
)
async def extract_worldbank_data(
    config: PipelineConfig,
    scenarios: list | None = None,
):
    """Extract climate projections from World Bank."""
    log = get_run_logger() if PREFECT_AVAILABLE else logger

    extractor = WorldBankClimateExtractor(config)

    if not await extractor.health_check():
        log.warning("World Bank API unavailable, skipping extraction")
        return {"source": "WORLDBANK_CLIMATE", "records": [], "status": "skipped"}

    result = await extractor.extract_with_retry(
        max_retries=config.max_retries,
        scenarios=scenarios or ["rcp45", "rcp85"],
    )

    log.info(f"World Bank extraction complete: {result.record_count} records")

    return {
        "source": result.source,
        "records": result.records,
        "watermark": result.watermark,
        "errors": result.errors,
        "status": "success" if not result.errors else "partial",
    }


@task(
    name="extract_sec_filings",
    retries=2,
    retry_delay_seconds=30,
)
async def extract_sec_filings(
    config: PipelineConfig,
    tickers: list | None = None,
):
    """Extract climate risk sections from SEC 10-K/20-F filings."""
    log = get_run_logger() if PREFECT_AVAILABLE else logger

    extractor = SECEdgarExtractor(config)

    if not await extractor.health_check():
        log.warning("SEC EDGAR API unavailable, skipping extraction")
        return {"source": "SEC_EDGAR", "records": [], "status": "skipped"}

    result = await extractor.extract(tickers=tickers)

    log.info(f"SEC EDGAR extraction complete: {result.record_count} filings")

    return {
        "source": result.source,
        "records": result.records,
        "watermark": result.watermark,
        "errors": result.errors,
        "status": "success" if not result.errors else "partial",
    }


@task(name="validate_schema")
def validate_schema(data: dict):
    """Validate extracted data against schema."""
    log = get_run_logger() if PREFECT_AVAILABLE else logger

    source = data.get("source", "unknown")
    records = data.get("records", [])

    if not records:
        return {**data, "validation": {"status": "skipped", "reason": "no records"}}

    validator = SchemaValidator.for_source(source)
    result = validator.validate(records)

    log.info(
        f"Schema validation: {result.valid_count}/{result.total_count} valid "
        f"({result.validity_rate:.1%})"
    )

    return {
        "source": source,
        "records": result.valid_records,
        "invalid_records": result.invalid_records,
        "validation": {
            "status": "passed" if result.is_valid else "partial",
            "valid_count": result.valid_count,
            "invalid_count": result.invalid_count,
            "validity_rate": result.validity_rate,
            "errors": result.errors[:10],
        },
    }


@task(name="validate_quality")
def validate_quality(data: dict):
    """Run data quality checks."""
    log = get_run_logger() if PREFECT_AVAILABLE else logger

    records = data.get("records", [])

    if not records:
        return {**data, "quality": {"status": "skipped"}}

    validator = DataQualityValidator(
        max_null_rate=0.15,
        max_duplicate_rate=0.05,
        anomaly_threshold=3.0,
    )

    # Determine key fields based on source
    source = data.get("source", "")
    if "EPA" in source:
        key_fields = ["facility_id", "reporting_year"]
        numeric_fields = ["total_emissions_mt_co2e"]
    elif "NOAA" in source:
        key_fields = ["station", "date", "datatype"]
        numeric_fields = ["value"]
    elif "WORLDBANK" in source:
        key_fields = ["country", "variable", "scenario", "period"]
        numeric_fields = ["annual_mean"]
    elif "SEC" in source:
        key_fields = ["ticker", "form_type"]
        numeric_fields = ["char_count"]
    else:
        key_fields = None
        numeric_fields = None

    report = validator.validate(
        records,
        key_fields=key_fields,
        numeric_fields=numeric_fields,
    )

    log.info(f"Quality validation: score={report.quality_score:.1f}/100, passed={report.passed}")

    return {
        **data,
        "quality": {
            "status": "passed" if report.passed else "warning",
            "score": report.quality_score,
            "checks": {
                name: {"passed": check.passed, "score": check.score}
                for name, check in report.checks.items()
            },
            "recommendations": report.recommendations,
        },
    }


@task(name="transform_climate_data")
def transform_climate_data(data: dict):
    """Transform climate data."""
    log = get_run_logger() if PREFECT_AVAILABLE else logger

    records = data.get("records", [])

    if not records:
        return {**data, "transform": {"status": "skipped"}}

    transformer = ClimateDataTransformer()
    result = transformer.transform(records)

    log.info(f"Climate transformation: {result.input_count} -> {result.output_count} records")

    return {
        "source": data.get("source"),
        "records": result.records,
        "transform": {
            "status": "success",
            "input_count": result.input_count,
            "output_count": result.output_count,
            "dropped_count": result.dropped_count,
        },
    }


@task(name="transform_emissions_data")
def transform_emissions_data(data: dict):
    """Transform emissions data."""
    log = get_run_logger() if PREFECT_AVAILABLE else logger

    records = data.get("records", [])

    if not records:
        return {**data, "transform": {"status": "skipped"}}

    transformer = EmissionsDataTransformer()
    result = transformer.transform(records)

    log.info(f"Emissions transformation: {result.input_count} -> {result.output_count} records")

    return {
        "source": data.get("source"),
        "records": result.records,
        "transform": {
            "status": "success",
            "input_count": result.input_count,
            "output_count": result.output_count,
            "dropped_count": result.dropped_count,
        },
    }


@task(name="load_to_staging")
def load_to_staging(data: dict, batch_id: str):
    """Load data to staging area."""
    log = get_run_logger() if PREFECT_AVAILABLE else logger

    records = data.get("records", [])
    source = data.get("source", "unknown")

    if not records:
        return {**data, "staging": {"status": "skipped"}}

    loader = StagingLoader()
    result = loader.load(records, source, batch_id)

    log.info(f"Staging: {result.records_loaded} records to {result.destination}")

    return {
        **data,
        "staging": {
            "status": "success" if result.success else "failed",
            "records_loaded": result.records_loaded,
            "destination": result.destination,
            "errors": result.errors,
        },
    }


@task(name="load_to_database")
async def load_to_database(data: dict, source_name: str):
    """Load data to the app's database using SQLAlchemy ORM."""
    log = get_run_logger() if PREFECT_AVAILABLE else logger

    records = data.get("records", [])
    source = data.get("source", source_name)

    if not records:
        return {**data, "database": {"status": "skipped"}}

    session_factory = get_db_session_factory()
    if not session_factory:
        log.warning("Database session not available")
        return {**data, "database": {"status": "skipped", "reason": "no session"}}

    async with session_factory() as session:
        loader = DatabaseLoader(session)

        try:
            if "EPA" in source or "emissions" in source.lower():
                result = await loader.load_emissions(records)
            else:
                result = await loader.load_climate(records)

            log.info(
                f"Database load: {result.records_loaded} records, {result.records_failed} failed"
            )

            return {
                **data,
                "database": {
                    "status": "success" if result.success else "partial",
                    "records_loaded": result.records_loaded,
                    "records_failed": result.records_failed,
                    "errors": result.errors,
                },
            }
        except Exception as e:
            log.error(f"Database load failed: {e}")
            return {**data, "database": {"status": "failed", "error": str(e)}}


@task(name="load_to_production")
async def load_to_production(data: dict, config: PipelineConfig):
    """Load data from staging to production database (PostgreSQL only)."""
    log = get_run_logger() if PREFECT_AVAILABLE else logger

    records = data.get("records", [])
    source = data.get("source", "unknown")

    if not records:
        return {**data, "production": {"status": "skipped"}}

    if not config.database_url or "sqlite" in config.database_url:
        log.info("Skipping production load (no PostgreSQL configured)")
        return {**data, "production": {"status": "skipped", "reason": "no postgres"}}

    loader = PostgresLoader(config.database_url)

    try:
        if "EPA" in source or "emissions" in source.lower():
            result = await loader.load_emissions_data(records)
        else:
            result = await loader.load_climate_data(records)

        log.info(
            f"Production load: {result.records_loaded} records, {result.records_failed} failed"
        )

        return {
            **data,
            "production": {
                "status": "success" if result.success else "partial",
                "records_loaded": result.records_loaded,
                "records_failed": result.records_failed,
                "errors": result.errors,
            },
        }

    finally:
        await loader.close()


# ============================================================================
# FLOWS
# ============================================================================


@flow(
    name="climate-data-pipeline",
    description="Extract, transform, and load climate data from NOAA, EPA, and World Bank",
    version="1.0.0",
)
async def climate_data_flow(
    load_to_db: bool = False,
    include_noaa: bool = True,
    include_epa: bool = True,
    include_worldbank: bool = True,
    include_sec: bool = True,
    days_back: int = 30,
):
    """
    Main climate data pipeline flow.

    Orchestrates extraction from multiple sources, validation,
    transformation, and loading to staging/production.

    Args:
        load_to_db: Whether to load to production database (requires PostgreSQL)
        include_noaa: Include NOAA climate data
        include_epa: Include EPA emissions data
        include_worldbank: Include World Bank climate projections
        include_sec: Include SEC EDGAR filing extraction
        days_back: Number of days of historical data to fetch

    Returns:
        Summary of pipeline execution
    """
    log = get_run_logger() if PREFECT_AVAILABLE else logger
    log.info("Starting climate data pipeline")

    config = PipelineConfig.from_env()
    batch_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    end_date = datetime.utcnow()
    start_date = end_date - timedelta(days=days_back)

    results = {
        "batch_id": batch_id,
        "started_at": datetime.utcnow().isoformat(),
        "sources": {},
    }

    # =========================================================================
    # EXTRACTION (parallel)
    # =========================================================================

    extraction_tasks = []

    if include_noaa:
        extraction_tasks.append(("NOAA", extract_noaa_data(config, start_date, end_date)))

    if include_epa:
        extraction_tasks.append(("EPA", extract_epa_data(config, start_date, end_date)))

    if include_worldbank:
        extraction_tasks.append(("WorldBank", extract_worldbank_data(config)))

    if include_sec:
        extraction_tasks.append(("SEC", extract_sec_filings(config)))

    async def _safe_extract(name: str, coro):
        """Run a single extractor, catching errors to avoid aborting the whole batch."""
        try:
            return name, await coro
        except Exception as e:
            log.error(f"Extraction failed for {name}: {e}")
            return name, {
                "source": name,
                "records": [],
                "status": "error",
                "error": str(e),
            }

    extraction_results = await asyncio.gather(*[_safe_extract(n, c) for n, c in extraction_tasks])
    extracted_data = dict(extraction_results)

    # =========================================================================
    # VALIDATION
    # =========================================================================

    validated_data = {}
    for name, data in extracted_data.items():
        if data.get("records"):
            schema_valid = validate_schema(data)
            quality_valid = validate_quality(schema_valid)
            validated_data[name] = quality_valid
        else:
            validated_data[name] = data

    # =========================================================================
    # TRANSFORMATION
    # =========================================================================

    transformed_data = {}
    for name, data in validated_data.items():
        if data.get("records"):
            if name == "EPA":
                transformed_data[name] = transform_emissions_data(data)
            elif name == "SEC":
                # SEC filings go to the vector store, not the DB pipeline.
                # Pass through without transformation.
                transformed_data[name] = data
            else:
                transformed_data[name] = transform_climate_data(data)
        else:
            transformed_data[name] = data

    # =========================================================================
    # LOADING
    # =========================================================================

    final_results = {}
    total_loaded = 0
    total_extracted = 0
    total_transformed = 0

    # Create a single PostgresLoader to reuse across all sources (avoids
    # creating one engine + connection pool per source).
    _prod_loader: PostgresLoader | None = None
    if load_to_db and config.database_url and "sqlite" not in config.database_url:
        _prod_loader = PostgresLoader(config.database_url)

    try:
        for name, data in transformed_data.items():
            # Stage all data
            staged = load_to_staging(data, batch_id)

            # Load to app database (works with SQLite and PostgreSQL)
            db_loaded = await load_to_database(staged, name)

            # Optionally load to production PostgreSQL
            if _prod_loader:
                final = await load_to_production(db_loaded, config)
            else:
                final = db_loaded

            final_results[name] = final

            extracted_count = len(extracted_data.get(name, {}).get("records", []))
            transformed_count = len(data.get("records", []))
            loaded_count = final.get("database", {}).get("records_loaded", 0)

            total_extracted += extracted_count
            total_transformed += transformed_count
            total_loaded += loaded_count

            results["sources"][name] = {
                "records_extracted": extracted_count,
                "records_transformed": transformed_count,
                "records_loaded": loaded_count,
                "staging_status": final.get("staging", {}).get("status"),
                "database_status": final.get("database", {}).get("status"),
                "production_status": final.get("production", {}).get("status")
                if load_to_db
                else "skipped",
            }
    finally:
        if _prod_loader:
            await _prod_loader.close()

    results["completed_at"] = datetime.utcnow().isoformat()
    results["status"] = "success"
    results["totals"] = {
        "extracted": total_extracted,
        "transformed": total_transformed,
        "loaded": total_loaded,
    }

    # Clean up staging files older than 7 days
    try:
        staging = StagingLoader()
        cleared = staging.clear_staged(before_date=datetime.utcnow() - timedelta(days=7))
        if cleared:
            log.info(f"Cleared {cleared} old staging files")
    except Exception:
        pass

    # Record pipeline run in database
    session_factory = get_db_session_factory()
    if session_factory:
        try:
            async with session_factory() as session:
                loader = DatabaseLoader(session)
                await loader.record_pipeline_run(
                    run_id=batch_id,
                    status="success",
                    records_extracted=total_extracted,
                    records_transformed=total_transformed,
                    records_loaded=total_loaded,
                    sources=list(results["sources"].keys()),
                    started_at=datetime.fromisoformat(results["started_at"]),
                )
        except Exception as e:
            log.warning(f"Failed to record pipeline run: {e}")

    log.info(f"Pipeline complete: {results}")

    return results


@flow(name="epa-emissions-only")
async def epa_emissions_flow(load_to_db: bool = False):
    """Standalone EPA emissions extraction flow."""
    return await climate_data_flow(
        load_to_db=load_to_db,
        include_noaa=False,
        include_epa=True,
        include_worldbank=False,
    )


@flow(name="noaa-climate-only")
async def noaa_climate_flow(load_to_db: bool = False, days_back: int = 30):
    """Standalone NOAA climate extraction flow."""
    return await climate_data_flow(
        load_to_db=load_to_db,
        include_noaa=True,
        include_epa=False,
        include_worldbank=False,
        days_back=days_back,
    )


# ============================================================================
# CLI ENTRY POINT
# ============================================================================


def run_pipeline(
    load_to_db: bool = False,
    include_noaa: bool = True,
    include_epa: bool = True,
    include_worldbank: bool = True,
    include_sec: bool = True,
):
    """Run the pipeline from the command line."""
    return asyncio.run(
        climate_data_flow(
            load_to_db=load_to_db,
            include_noaa=include_noaa,
            include_epa=include_epa,
            include_worldbank=include_worldbank,
            include_sec=include_sec,
        )
    )


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run climate data pipeline")
    parser.add_argument("--load-to-db", action="store_true", help="Load to production database")
    parser.add_argument("--no-noaa", action="store_true", help="Skip NOAA extraction")
    parser.add_argument("--no-epa", action="store_true", help="Skip EPA extraction")
    parser.add_argument("--no-worldbank", action="store_true", help="Skip World Bank extraction")
    parser.add_argument("--no-sec", action="store_true", help="Skip SEC EDGAR extraction")
    parser.add_argument("--days-back", type=int, default=30, help="Days of historical data")

    args = parser.parse_args()

    result = asyncio.run(
        climate_data_flow(
            load_to_db=args.load_to_db,
            include_noaa=not args.no_noaa,
            include_epa=not args.no_epa,
            include_worldbank=not args.no_worldbank,
            include_sec=not args.no_sec,
            days_back=args.days_back,
        )
    )

    print(f"\nPipeline completed: {result['status']}")
    for source, stats in result["sources"].items():
        print(
            f"  {source}: {stats['records_extracted']} extracted -> {stats['records_transformed']} transformed"
        )
