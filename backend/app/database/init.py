"""Database initialization and seeding."""

import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import AssetDB, PortfolioDB, ScenarioDB
from .seed import REAL_ASSETS, SAMPLE_PORTFOLIOS, CLIMATE_SCENARIOS


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

    await session.commit()
    print(f"[INIT] Seeded {len(REAL_ASSETS)} assets, {len(SAMPLE_PORTFOLIOS)} portfolios")
    return True
