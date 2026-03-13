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

from .flows import climate_data_flow, run_pipeline

__all__ = ["climate_data_flow", "run_pipeline"]
