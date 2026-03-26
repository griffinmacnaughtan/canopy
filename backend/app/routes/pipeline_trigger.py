"""Pipeline trigger endpoints — run data pipelines on demand.

These endpoints allow running the data pipeline from the frontend,
Railway dashboard, or a scheduled cron job, instead of only at boot.
"""

import asyncio
from datetime import datetime

import structlog
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from ..config import get_settings
from ..database.connection import get_db
from ..database.pipeline_models import PipelineRun

logger = structlog.get_logger()
router = APIRouter(prefix="/pipeline", tags=["Pipeline Trigger"])

# Simple lock to prevent concurrent pipeline runs
_pipeline_lock = asyncio.Lock()


class PipelineTriggerRequest(BaseModel):
    """Request to trigger a pipeline run."""

    include_noaa: bool = Field(True, description="Include NOAA climate data")
    include_epa: bool = Field(True, description="Include EPA emissions data")
    include_worldbank: bool = Field(True, description="Include World Bank projections")
    include_sec: bool = Field(True, description="Include SEC EDGAR filings")
    load_to_db: bool = Field(True, description="Load results to database")
    days_back: int = Field(365, ge=1, le=3650, description="Days of historical data")


class PipelineTriggerResponse(BaseModel):
    """Response from pipeline trigger."""

    status: str
    batch_id: str
    message: str
    totals: dict | None = None
    errors: list[str] | None = None


@router.post("/trigger", response_model=PipelineTriggerResponse)
async def trigger_pipeline(
    request: PipelineTriggerRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Trigger a full pipeline run on demand.

    This runs the EPA, NOAA, World Bank, and SEC EDGAR extractors,
    validates and transforms the data, and loads it into the database.

    Only one pipeline can run at a time. If a pipeline is already
    running, returns 409 Conflict.
    """
    # Atomic check-and-acquire: if the lock is already held, reject immediately.
    # Both the check and the run-record creation happen inside the lock to
    # prevent TOCTOU races and orphaned "running" records.
    if _pipeline_lock.locked():
        raise HTTPException(
            status_code=409,
            detail="A pipeline is already running. Please wait for it to complete.",
        )

    req = request or PipelineTriggerRequest()
    batch_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")

    async with _pipeline_lock:
        # Record the run INSIDE the lock so it can't be orphaned
        run = PipelineRun(
            run_id=f"manual-{batch_id}",
            status="running",
            started_at=datetime.utcnow(),
            triggered_by="manual",
        )
        db.add(run)
        await db.commit()

        try:
            from ..pipeline.flows import climate_data_flow

            result = await climate_data_flow(
                load_to_db=req.load_to_db,
                include_noaa=req.include_noaa,
                include_epa=req.include_epa,
                include_worldbank=req.include_worldbank,
                include_sec=req.include_sec,
                days_back=req.days_back,
            )

            # Update run record
            run.status = result.get("status", "success")
            run.completed_at = datetime.utcnow()
            run.records_extracted = result.get("totals", {}).get("extracted", 0)
            run.records_transformed = result.get("totals", {}).get("transformed", 0)
            run.records_loaded = result.get("totals", {}).get("loaded", 0)
            run.sources = str(list(result.get("sources", {}).keys()))
            await db.commit()

            return PipelineTriggerResponse(
                status="success",
                batch_id=batch_id,
                message=f"Pipeline completed: {run.records_extracted} extracted, "
                f"{run.records_loaded} loaded",
                totals=result.get("totals"),
            )

        except Exception as e:
            logger.error("pipeline_trigger_failed", error=str(e))
            run.status = "failed"
            run.completed_at = datetime.utcnow()
            run.errors = str(e)
            await db.commit()

            return PipelineTriggerResponse(
                status="failed",
                batch_id=batch_id,
                message=f"Pipeline failed: {e}",
                errors=[str(e)],
            )


@router.post("/trigger/epa-only", response_model=PipelineTriggerResponse)
async def trigger_epa_only(db: AsyncSession = Depends(get_db)):
    """Quick trigger for EPA emissions data only."""
    return await trigger_pipeline(
        PipelineTriggerRequest(
            include_noaa=False,
            include_epa=True,
            include_worldbank=False,
            include_sec=False,
        ),
        db=db,
    )


@router.post("/trigger/climate-only", response_model=PipelineTriggerResponse)
async def trigger_climate_only(db: AsyncSession = Depends(get_db)):
    """Quick trigger for NOAA + World Bank climate data only."""
    return await trigger_pipeline(
        PipelineTriggerRequest(
            include_noaa=True,
            include_epa=False,
            include_worldbank=True,
            include_sec=False,
        ),
        db=db,
    )
