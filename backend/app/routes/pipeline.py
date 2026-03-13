"""Pipeline data endpoints - exposes real climate and emissions data."""

from typing import Optional, List
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, desc

from ..database.connection import get_db
from ..database.pipeline_models import ClimateData, EmissionsData, PipelineRun

router = APIRouter(prefix="/pipeline", tags=["Pipeline Data"])


# =============================================================================
# Response Models
# =============================================================================


class EmissionsFacility(BaseModel):
    """EPA facility emissions data."""
    facility_id: str
    facility_name: Optional[str]
    city: Optional[str]
    state: Optional[str]
    sector: Optional[str]
    reporting_year: Optional[int]
    total_emissions_mt_co2e: Optional[float]
    emissions_intensity: Optional[float] = None  # Computed if revenue available

    class Config:
        from_attributes = True


class ClimateObservation(BaseModel):
    """Climate data point."""
    location_id: Optional[str]
    country_code: Optional[str]
    region: Optional[str]
    year: Optional[int]
    month: Optional[int]
    metric_name: Optional[str]
    value: Optional[float]
    unit: Optional[str]
    scenario: Optional[str]
    source: str

    class Config:
        from_attributes = True


class SectorEmissionsSummary(BaseModel):
    """Aggregated emissions by sector."""
    sector: str
    total_emissions_mt_co2e: float
    facility_count: int
    avg_emissions_per_facility: float


class PipelineStats(BaseModel):
    """Pipeline data statistics."""
    total_emissions_records: int
    total_climate_records: int
    emissions_by_sector: List[SectorEmissionsSummary]
    latest_emissions_year: Optional[int]
    states_covered: int
    data_sources: List[str]
    last_updated: Optional[datetime]


class PipelineRunInfo(BaseModel):
    """Pipeline run information."""
    run_id: str
    status: str
    started_at: datetime
    completed_at: Optional[datetime]
    records_extracted: int
    records_loaded: int

    class Config:
        from_attributes = True


# =============================================================================
# Routes
# =============================================================================


@router.get("/stats", response_model=PipelineStats)
async def get_pipeline_stats(db: AsyncSession = Depends(get_db)):
    """Get overall pipeline data statistics."""

    # Count emissions records
    emissions_count = await db.execute(
        select(func.count()).select_from(EmissionsData)
    )
    total_emissions = emissions_count.scalar() or 0

    # Count climate records
    climate_count = await db.execute(
        select(func.count()).select_from(ClimateData)
    )
    total_climate = climate_count.scalar() or 0

    # Emissions by sector
    sector_query = await db.execute(
        select(
            EmissionsData.sector,
            func.sum(EmissionsData.total_emissions_mt_co2e).label("total"),
            func.count().label("count"),
        )
        .where(EmissionsData.sector.isnot(None))
        .group_by(EmissionsData.sector)
        .order_by(desc("total"))
    )
    sector_rows = sector_query.all()

    emissions_by_sector = [
        SectorEmissionsSummary(
            sector=row.sector,
            total_emissions_mt_co2e=row.total or 0,
            facility_count=row.count,
            avg_emissions_per_facility=(row.total or 0) / row.count if row.count > 0 else 0,
        )
        for row in sector_rows
    ]

    # Latest year
    latest_year_query = await db.execute(
        select(func.max(EmissionsData.reporting_year))
    )
    latest_year = latest_year_query.scalar()

    # States covered
    states_query = await db.execute(
        select(func.count(func.distinct(EmissionsData.state)))
    )
    states_covered = states_query.scalar() or 0

    # Data sources
    sources_query = await db.execute(
        select(func.distinct(EmissionsData.source))
    )
    emissions_sources = [row[0] for row in sources_query.all() if row[0]]

    climate_sources_query = await db.execute(
        select(func.distinct(ClimateData.source))
    )
    climate_sources = [row[0] for row in climate_sources_query.all() if row[0]]

    all_sources = list(set(emissions_sources + climate_sources))

    # Last updated
    last_updated_query = await db.execute(
        select(func.max(EmissionsData.loaded_at))
    )
    last_updated = last_updated_query.scalar()

    return PipelineStats(
        total_emissions_records=total_emissions,
        total_climate_records=total_climate,
        emissions_by_sector=emissions_by_sector,
        latest_emissions_year=latest_year,
        states_covered=states_covered,
        data_sources=all_sources,
        last_updated=last_updated,
    )


@router.get("/emissions", response_model=List[EmissionsFacility])
async def get_emissions_data(
    sector: Optional[str] = Query(None, description="Filter by sector"),
    state: Optional[str] = Query(None, description="Filter by state"),
    year: Optional[int] = Query(None, description="Filter by reporting year"),
    limit: int = Query(50, le=500, description="Max records to return"),
    offset: int = Query(0, description="Offset for pagination"),
    db: AsyncSession = Depends(get_db),
):
    """Get facility-level emissions data from EPA GHGRP."""

    query = select(EmissionsData)

    if sector:
        query = query.where(EmissionsData.sector == sector)
    if state:
        query = query.where(EmissionsData.state == state)
    if year:
        query = query.where(EmissionsData.reporting_year == year)

    query = query.order_by(desc(EmissionsData.total_emissions_mt_co2e))
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()

    return [
        EmissionsFacility(
            facility_id=r.facility_id,
            facility_name=r.facility_name,
            city=r.city,
            state=r.state,
            sector=r.sector,
            reporting_year=r.reporting_year,
            total_emissions_mt_co2e=r.total_emissions_mt_co2e,
        )
        for r in records
    ]


@router.get("/emissions/top-emitters", response_model=List[EmissionsFacility])
async def get_top_emitters(
    limit: int = Query(10, le=100),
    db: AsyncSession = Depends(get_db),
):
    """Get top emitting facilities."""

    result = await db.execute(
        select(EmissionsData)
        .where(EmissionsData.total_emissions_mt_co2e.isnot(None))
        .order_by(desc(EmissionsData.total_emissions_mt_co2e))
        .limit(limit)
    )
    records = result.scalars().all()

    return [
        EmissionsFacility(
            facility_id=r.facility_id,
            facility_name=r.facility_name,
            city=r.city,
            state=r.state,
            sector=r.sector,
            reporting_year=r.reporting_year,
            total_emissions_mt_co2e=r.total_emissions_mt_co2e,
        )
        for r in records
    ]


@router.get("/climate", response_model=List[ClimateObservation])
async def get_climate_data(
    country: Optional[str] = Query(None, description="Filter by country code"),
    metric: Optional[str] = Query(None, description="Filter by metric name"),
    scenario: Optional[str] = Query(None, description="Filter by climate scenario"),
    limit: int = Query(50, le=500),
    offset: int = Query(0),
    db: AsyncSession = Depends(get_db),
):
    """Get climate observations and projections."""

    query = select(ClimateData)

    if country:
        query = query.where(ClimateData.country_code == country)
    if metric:
        query = query.where(ClimateData.metric_name == metric)
    if scenario:
        query = query.where(ClimateData.scenario == scenario)

    query = query.order_by(desc(ClimateData.year))
    query = query.offset(offset).limit(limit)

    result = await db.execute(query)
    records = result.scalars().all()

    return [
        ClimateObservation(
            location_id=r.location_id,
            country_code=r.country_code,
            region=r.region,
            year=r.year,
            month=r.month,
            metric_name=r.metric_name,
            value=r.value,
            unit=r.unit,
            scenario=r.scenario,
            source=r.source,
        )
        for r in records
    ]


@router.get("/runs", response_model=List[PipelineRunInfo])
async def get_pipeline_runs(
    limit: int = Query(10, le=50),
    db: AsyncSession = Depends(get_db),
):
    """Get recent pipeline run history."""

    result = await db.execute(
        select(PipelineRun)
        .order_by(desc(PipelineRun.started_at))
        .limit(limit)
    )
    runs = result.scalars().all()

    return [
        PipelineRunInfo(
            run_id=r.run_id,
            status=r.status,
            started_at=r.started_at,
            completed_at=r.completed_at,
            records_extracted=r.records_extracted,
            records_loaded=r.records_loaded,
        )
        for r in runs
    ]


@router.get("/sectors")
async def get_available_sectors(db: AsyncSession = Depends(get_db)):
    """Get list of sectors with emissions data."""

    result = await db.execute(
        select(
            EmissionsData.sector,
            func.count().label("facility_count"),
        )
        .where(EmissionsData.sector.isnot(None))
        .group_by(EmissionsData.sector)
        .order_by(desc("facility_count"))
    )
    rows = result.all()

    return [
        {"sector": row.sector, "facility_count": row.facility_count}
        for row in rows
    ]
