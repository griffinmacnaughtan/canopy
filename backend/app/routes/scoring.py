"""Scoring and scenario endpoints."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_db
from ..database.models import ScenarioDB
from ..database.seed import SECTOR_BASELINES
from ..models import ScenarioRequest, ScenarioResponse, ScoreResponse
from ..risk import scenario_impact, score_portfolio
from .portfolios import db_asset_to_pydantic, get_portfolio_by_id

router = APIRouter()


async def get_scenarios_dict(db: AsyncSession) -> dict:
    """Get scenarios as a dict for backward compatibility."""
    result = await db.execute(select(ScenarioDB))
    scenarios = result.scalars().all()
    return {
        s.name: {
            "carbon_price": s.carbon_price,
            "revenue_shock": s.revenue_shock,
        }
        for s in scenarios
    }


@router.get("/score", response_model=ScoreResponse)
async def portfolio_score(
    portfolio_id: str | None = Query(None, description="Portfolio ID"),
    db: AsyncSession = Depends(get_db),
):
    """Calculate and return portfolio risk scores."""
    portfolio = await get_portfolio_by_id(portfolio_id, db)
    pydantic_assets = [db_asset_to_pydantic(a) for a in portfolio.assets]

    overall, climate, transition, physical, opportunity, top_risks, quick_wins, sector = (
        score_portfolio(pydantic_assets, SECTOR_BASELINES)
    )

    return ScoreResponse(
        portfolio_id=str(portfolio.id),
        overall_score=overall,
        climate_risk=climate,
        transition_risk=transition,
        physical_risk=physical,
        opportunity_score=opportunity,
        top_risks=top_risks,
        quick_wins=quick_wins,
        sector_breakdown=sector,
    )


@router.get("/scenarios")
async def list_scenarios(db: AsyncSession = Depends(get_db)):
    """List all available climate scenarios."""
    return await get_scenarios_dict(db)


@router.post("/scenario", response_model=ScenarioResponse)
async def run_scenario(
    request: ScenarioRequest,
    db: AsyncSession = Depends(get_db),
):
    """Run a climate scenario stress test on the portfolio."""
    portfolio = await get_portfolio_by_id(request.portfolio_id, db)
    pydantic_assets = [db_asset_to_pydantic(a) for a in portfolio.assets]

    scenarios = await get_scenarios_dict(db)
    baseline = scenarios.get(request.scenario)

    if baseline:
        carbon_price = request.carbon_price_usd or baseline["carbon_price"]
        revenue_shock = (
            request.revenue_shock_pct
            if request.revenue_shock_pct is not None
            else baseline["revenue_shock"]
        )
    else:
        carbon_price = request.carbon_price_usd or 100
        revenue_shock = request.revenue_shock_pct or -2.5

    ebitda_impact, emissions_delta, hotspots = scenario_impact(
        pydantic_assets, carbon_price, revenue_shock
    )
    summary = (
        f"Scenario '{request.scenario}' applies a ${carbon_price}/tCO2e price and {revenue_shock}% revenue shock. "
        f"Estimated EBITDA impact {ebitda_impact}% with emissions change {emissions_delta}%."
    )

    return ScenarioResponse(
        portfolio_id=str(portfolio.id),
        scenario=request.scenario,
        impact_summary=summary,
        est_ebitda_impact_pct=ebitda_impact,
        emissions_delta_pct=emissions_delta,
        hotspots=hotspots,
    )
