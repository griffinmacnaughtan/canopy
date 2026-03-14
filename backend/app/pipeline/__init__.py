"""
Climate Data Pipeline

Professional ETL pipeline for ingesting climate and emissions data from
multiple sources (NOAA, EPA, World Bank Climate API).

Architecture:
- Extractors: Pull data from external APIs
- Validators: Schema validation, quality checks, anomaly detection
- Transformers: Clean, normalize, and enrich data
- Loaders: Upsert to staging, then production tables

Orchestration via Prefect with:
- Scheduled runs (configurable cron)
- Incremental loading with watermarks
- Retry logic and error handling
- Observability and alerting
"""

# Flows are imported lazily to avoid pulling the Prefect runtime into the
# package namespace at import time.  Import them directly when needed:
#
#   from app.pipeline.flows import climate_data_flow, run_pipeline
#
# This also prevents Python 3.12 incompatibilities in older Prefect versions
# from breaking test collection of validators/transformers/loaders.


def __getattr__(name: str):  # noqa: ANN202
    """Lazy-load flow symbols to keep prefect out of the base import."""
    if name in ("climate_data_flow", "run_pipeline"):
        from .flows import climate_data_flow, run_pipeline  # noqa: PLC0415

        return {"climate_data_flow": climate_data_flow, "run_pipeline": run_pipeline}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


__all__ = ["climate_data_flow", "run_pipeline"]
