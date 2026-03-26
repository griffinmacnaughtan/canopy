"""Database initialization and seeding."""

import uuid
from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AssetDB, PortfolioDB, ScenarioDB
from .pipeline_models import ClimateData, EmissionsData, PipelineRun
from .seed import (
    CLIMATE_SCENARIOS,
    REAL_ASSETS,
    SAMPLE_PORTFOLIOS,
    SEED_CLIMATE,
    SEED_EMISSIONS,
    SEED_PIPELINE_RUNS,
)


async def seed_database(session: AsyncSession) -> bool:
    """Seed the database with initial data if empty.

    Returns True if seeding was performed, False if data already exists.
    Checks each entity type independently so a partially-seeded DB
    (e.g. scenarios exist but portfolios don't) never causes a unique-
    constraint violation that silently rolls back the whole commit.
    """
    # Check portfolios (primary seeding gate)
    result = await session.execute(select(PortfolioDB).limit(1))
    if result.scalar_one_or_none() is not None:
        return False  # Already fully seeded

    print("[INIT] Seeding database with real company data...")

    # Create assets
    asset_map = {}  # name -> AssetDB
    for asset_data in REAL_ASSETS:
        asset = AssetDB(
            id=uuid.uuid4(),
            name=asset_data["name"],
            ticker=asset_data.get("ticker"),
            sector=asset_data["sector"],
            region=asset_data["region"],
            revenue_usd_m=asset_data["revenue_usd_m"],
            scope1_tco2e=asset_data["scope1_tco2e"],
            scope2_tco2e=asset_data["scope2_tco2e"],
            scope3_tco2e=asset_data.get("scope3_tco2e", 0),
            green_revenue_pct=asset_data["green_revenue_pct"],
            controversies=asset_data["controversies"],
        )
        session.add(asset)
        asset_map[asset_data["name"]] = asset

    # Create sample portfolios
    for portfolio_data in SAMPLE_PORTFOLIOS:
        portfolio = PortfolioDB(
            id=uuid.uuid4(),
            name=portfolio_data["name"],
            description=portfolio_data["description"],
            is_sample=True,
        )
        for asset_name in portfolio_data["asset_names"]:
            if asset_name in asset_map:
                portfolio.assets.append(asset_map[asset_name])
        session.add(portfolio)

    # Only insert scenarios if none exist — scenarios.name has a unique
    # constraint and a previous partial run may have already committed them.
    result = await session.execute(select(ScenarioDB).limit(1))
    if result.scalar_one_or_none() is None:
        for scenario_data in CLIMATE_SCENARIOS:
            scenario = ScenarioDB(
                id=uuid.uuid4(),
                name=scenario_data["name"],
                description=scenario_data["description"],
                carbon_price=scenario_data["carbon_price"],
                revenue_shock=scenario_data["revenue_shock"],
                is_default=scenario_data["is_default"],
            )
            session.add(scenario)

    # Seed pipeline data (emissions, climate, pipeline runs) so the
    # Data Pipeline Explorer section renders populated on first deploy.
    now = datetime.utcnow()

    result = await session.execute(select(EmissionsData).limit(1))
    if result.scalar_one_or_none() is None:
        for row in SEED_EMISSIONS:
            session.add(
                EmissionsData(
                    facility_id=row["facility_id"],
                    facility_name=row["facility_name"],
                    city=row["city"],
                    state=row["state"],
                    region=row["region"],
                    latitude=row["latitude"],
                    longitude=row["longitude"],
                    industry_type=row["industry_type"],
                    sector=row["sector"],
                    naics_code=row["naics_code"],
                    reporting_year=row["reporting_year"],
                    total_emissions_mt_co2e=row["total_emissions_mt_co2e"],
                    co2_emissions_mt=row["co2_emissions_mt"],
                    methane_emissions_mt_co2e=row["methane_emissions_mt_co2e"],
                    n2o_emissions_mt_co2e=row["n2o_emissions_mt_co2e"],
                    emissions_scope=row["emissions_scope"],
                    source=row["source"],
                    transformed_at=now,
                    loaded_at=now,
                )
            )
        print(f"[INIT] Seeded {len(SEED_EMISSIONS)} emissions records")

    result = await session.execute(select(ClimateData).limit(1))
    if result.scalar_one_or_none() is None:
        for row in SEED_CLIMATE:
            session.add(
                ClimateData(
                    location_id=row.get("location_id"),
                    country_code=row.get("country_code"),
                    state_code=row.get("state_code"),
                    region=row.get("region"),
                    year=row.get("year"),
                    month=row.get("month"),
                    metric_name=row.get("metric_name"),
                    metric_type=row.get("metric_type"),
                    value=row.get("value"),
                    unit=row.get("unit"),
                    scenario=row.get("scenario"),
                    period_start=row.get("period_start"),
                    period_end=row.get("period_end"),
                    source=row["source"],
                    station_id=row.get("station_id"),
                    transformed_at=now,
                    loaded_at=now,
                )
            )
        print(f"[INIT] Seeded {len(SEED_CLIMATE)} climate records")

    result = await session.execute(select(PipelineRun).limit(1))
    if result.scalar_one_or_none() is None:
        for i, row in enumerate(SEED_PIPELINE_RUNS):
            started = now - timedelta(hours=len(SEED_PIPELINE_RUNS) - i)
            session.add(
                PipelineRun(
                    run_id=row["run_id"],
                    status=row["status"],
                    started_at=started,
                    completed_at=started + timedelta(minutes=3),
                    records_extracted=row["records_extracted"],
                    records_transformed=row["records_transformed"],
                    records_loaded=row["records_loaded"],
                    sources=row["sources"],
                    triggered_by=row["triggered_by"],
                )
            )
        print(f"[INIT] Seeded {len(SEED_PIPELINE_RUNS)} pipeline runs")

    await session.commit()
    print(f"[INIT] Seeded {len(REAL_ASSETS)} assets, {len(SAMPLE_PORTFOLIOS)} portfolios")
    return True
