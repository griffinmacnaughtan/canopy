"""Pipeline trigger endpoints — run data pipelines on demand.

These endpoints allow running the data pipeline from the frontend,
Railway dashboard, or a scheduled cron job, instead of only at boot.
"""

import asyncio
from datetime import datetime

import structlog
from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import async_session_factory, get_db
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


async def _run_pipeline_background(run_id: str, req: PipelineTriggerRequest) -> None:
    """Run the pipeline in the background and update the run record on completion.

    The session is intentionally NOT held open during the pipeline run — that
    can take several minutes of idle time (HTTP calls to external APIs) which
    causes Railway to drop the connection.  Instead we run the flow first, then
    open a short-lived session just to persist the result.
    """
    status = "failed"
    errors: str | None = None
    records_extracted = records_transformed = records_loaded = 0
    sources: list[str] = []

    try:
        from ..pipeline.flows import climate_data_flow

        flow_result = await climate_data_flow(
            load_to_db=req.load_to_db,
            include_noaa=req.include_noaa,
            include_epa=req.include_epa,
            include_worldbank=req.include_worldbank,
            include_sec=req.include_sec,
            days_back=req.days_back,
        )

        status = flow_result.get("status", "success")
        totals = flow_result.get("totals", {})
        records_extracted = totals.get("extracted", 0)
        records_transformed = totals.get("transformed", 0)
        records_loaded = totals.get("loaded", 0)
        sources = list(flow_result.get("sources", {}).keys())
        logger.info("pipeline_completed", run_id=run_id, records_loaded=records_loaded)
    except Exception as e:
        logger.error("pipeline_background_failed", run_id=run_id, error=str(e))
        errors = str(e)
    finally:
        _pipeline_lock.release()

    # Persist result in a fresh, short-lived session
    async with async_session_factory() as db:
        result = await db.execute(select(PipelineRun).where(PipelineRun.run_id == run_id))
        run = result.scalar_one_or_none()
        if run:
            run.status = status
            run.completed_at = datetime.utcnow()
            run.records_extracted = records_extracted
            run.records_transformed = records_transformed
            run.records_loaded = records_loaded
            run.sources = str(sources)
            if errors:
                run.errors = errors
            await db.commit()


@router.post("/trigger", response_model=PipelineTriggerResponse)
async def trigger_pipeline(
    background_tasks: BackgroundTasks,
    request: PipelineTriggerRequest | None = None,
    db: AsyncSession = Depends(get_db),
):
    """Trigger a full pipeline run on demand.

    Returns immediately with status "started". Poll GET /pipeline/runs to
    track progress. Only one pipeline can run at a time (409 if busy).
    """
    if _pipeline_lock.locked():
        raise HTTPException(
            status_code=409,
            detail="A pipeline is already running. Please wait for it to complete.",
        )

    req = request or PipelineTriggerRequest()
    batch_id = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    run_id = f"manual-{batch_id}"

    # Acquire the lock before returning so the background task holds it
    await _pipeline_lock.acquire()

    run = PipelineRun(
        run_id=run_id,
        status="running",
        started_at=datetime.utcnow(),
        triggered_by="manual",
    )
    db.add(run)
    await db.commit()

    background_tasks.add_task(_run_pipeline_background, run_id, req)

    return PipelineTriggerResponse(
        status="started",
        batch_id=batch_id,
        message="Pipeline started in background. Poll /pipeline/runs for status.",
    )


@router.post("/trigger/epa-only", response_model=PipelineTriggerResponse)
async def trigger_epa_only(background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)):
    """Quick trigger for EPA emissions data only."""
    return await trigger_pipeline(
        background_tasks,
        PipelineTriggerRequest(
            include_noaa=False,
            include_epa=True,
            include_worldbank=False,
            include_sec=False,
        ),
        db=db,
    )


@router.post("/trigger/climate-only", response_model=PipelineTriggerResponse)
async def trigger_climate_only(
    background_tasks: BackgroundTasks, db: AsyncSession = Depends(get_db)
):
    """Quick trigger for NOAA + World Bank climate data only."""
    return await trigger_pipeline(
        background_tasks,
        PipelineTriggerRequest(
            include_noaa=True,
            include_epa=False,
            include_worldbank=True,
            include_sec=False,
        ),
        db=db,
    )
