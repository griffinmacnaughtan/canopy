"""Database models for pipeline data."""

from datetime import datetime
from typing import Optional
from sqlalchemy import (
    Column,
    String,
    Integer,
    Float,
    DateTime,
    Index,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column

from .models import Base


class ClimateData(Base):
    """Climate observations and projections from NOAA/World Bank."""

    __tablename__ = "climate_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Location
    location_id: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    country_code: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    state_code: Mapped[Optional[str]] = mapped_column(String(10))
    region: Mapped[Optional[str]] = mapped_column(String(50))

    # Time
    observation_date: Mapped[Optional[datetime]] = mapped_column(DateTime)
    year: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    month: Mapped[Optional[int]] = mapped_column(Integer)

    # Metrics
    metric_name: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    metric_type: Mapped[Optional[str]] = mapped_column(String(50))
    value: Mapped[Optional[float]] = mapped_column(Float)
    unit: Mapped[Optional[str]] = mapped_column(String(50))

    # Projections
    scenario: Mapped[Optional[str]] = mapped_column(String(50))
    period_start: Mapped[Optional[int]] = mapped_column(Integer)
    period_end: Mapped[Optional[int]] = mapped_column(Integer)

    # Metadata
    source: Mapped[str] = mapped_column(String(100), index=True)
    station_id: Mapped[Optional[str]] = mapped_column(String(100))
    transformed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    loaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_climate_location_date", "location_id", "observation_date"),
    )


class EmissionsData(Base):
    """Facility-level emissions data from EPA GHGRP."""

    __tablename__ = "emissions_data"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    # Facility info
    facility_id: Mapped[str] = mapped_column(String(100), index=True)
    facility_name: Mapped[Optional[str]] = mapped_column(String(500))

    # Location
    city: Mapped[Optional[str]] = mapped_column(String(200))
    state: Mapped[Optional[str]] = mapped_column(String(10), index=True)
    region: Mapped[Optional[str]] = mapped_column(String(50))
    latitude: Mapped[Optional[float]] = mapped_column(Float)
    longitude: Mapped[Optional[float]] = mapped_column(Float)

    # Classification
    industry_type: Mapped[Optional[str]] = mapped_column(String(200))
    sector: Mapped[Optional[str]] = mapped_column(String(100), index=True)
    naics_code: Mapped[Optional[str]] = mapped_column(String(20))

    # Emissions
    reporting_year: Mapped[Optional[int]] = mapped_column(Integer, index=True)
    total_emissions_mt_co2e: Mapped[Optional[float]] = mapped_column(Float)
    co2_emissions_mt: Mapped[Optional[float]] = mapped_column(Float)
    methane_emissions_mt_co2e: Mapped[Optional[float]] = mapped_column(Float)
    n2o_emissions_mt_co2e: Mapped[Optional[float]] = mapped_column(Float)
    emissions_scope: Mapped[Optional[str]] = mapped_column(String(50))

    # Metadata
    source: Mapped[str] = mapped_column(String(100))
    transformed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)
    loaded_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    __table_args__ = (
        Index("idx_emissions_facility_year", "facility_id", "reporting_year"),
    )


class PipelineRun(Base):
    """Track pipeline execution history."""

    __tablename__ = "pipeline_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    run_id: Mapped[str] = mapped_column(String(100), unique=True, index=True)
    status: Mapped[str] = mapped_column(String(50))  # running, success, failed

    started_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime)

    # Stats
    records_extracted: Mapped[int] = mapped_column(Integer, default=0)
    records_transformed: Mapped[int] = mapped_column(Integer, default=0)
    records_loaded: Mapped[int] = mapped_column(Integer, default=0)

    # Sources processed
    sources: Mapped[Optional[str]] = mapped_column(Text)  # JSON list
    errors: Mapped[Optional[str]] = mapped_column(Text)  # JSON list

    # Metadata
    triggered_by: Mapped[Optional[str]] = mapped_column(String(100))  # manual, schedule
