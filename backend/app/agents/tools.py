"""Concrete tools for the climate risk analysis agent.

Each tool is a self-contained async function that queries the application's
data layer and returns a formatted string the agent can reason over.
"""

from __future__ import annotations

import json

from .base import ToolDefinition


async def analyze_portfolio(portfolio_id: str | None = None) -> str:
    """Fetch portfolio holdings, risk scores, and sector breakdown."""
    from ..database.connection import async_session_factory
    from ..database.seed import SECTOR_BASELINES
    from ..risk import score_portfolio
    from ..routes.portfolios import db_asset_to_pydantic, get_portfolio_by_id

    async with async_session_factory() as db:
        portfolio = await get_portfolio_by_id(portfolio_id, db)
        assets = [db_asset_to_pydantic(a) for a in portfolio.assets]
        overall, climate, transition, physical, opportunity, top_risks, quick_wins, sector = (
            score_portfolio(assets, SECTOR_BASELINES)
        )

    asset_summary = []
    for a in assets:
        intensity = (a.scope1_tco2e + a.scope2_tco2e) / a.revenue_usd_m if a.revenue_usd_m > 0 else 0
        asset_summary.append({
            "name": a.name,
            "sector": a.sector,
            "region": a.region,
            "revenue_m": a.revenue_usd_m,
            "emissions_tco2e": a.scope1_tco2e + a.scope2_tco2e,
            "intensity": round(intensity, 2),
            "green_revenue_pct": a.green_revenue_pct,
            "controversies": a.controversies,
        })

    return json.dumps({
        "portfolio": portfolio.name,
        "scores": {
            "overall": overall,
            "climate_risk": climate,
            "transition_risk": transition,
            "physical_risk": physical,
            "opportunity": opportunity,
        },
        "top_risks": top_risks,
        "quick_wins": quick_wins,
        "sector_breakdown": sector,
        "assets": asset_summary,
    }, indent=2)


async def run_scenario(
    portfolio_id: str | None = None,
    scenario_name: str = "Net Zero 2050",
    carbon_price: float | None = None,
    revenue_shock: float | None = None,
) -> str:
    """Run a climate scenario stress test against a portfolio."""
    from ..database.connection import async_session_factory
    from ..risk import scenario_impact
    from ..routes.portfolios import db_asset_to_pydantic, get_portfolio_by_id
    from ..routes.scoring import get_scenarios_dict

    async with async_session_factory() as db:
        portfolio = await get_portfolio_by_id(portfolio_id, db)
        assets = [db_asset_to_pydantic(a) for a in portfolio.assets]
        scenarios = await get_scenarios_dict(db)

    # Use provided params or fall back to named scenario
    if carbon_price is not None and revenue_shock is not None:
        cp, rs = carbon_price, revenue_shock
    elif scenario_name in scenarios:
        cp = scenarios[scenario_name].get("carbon_price", 75)
        rs = scenarios[scenario_name].get("revenue_shock", -5)
    else:
        cp, rs = 75, -5

    ebitda_impact, emissions_delta, hotspots = scenario_impact(assets, cp, rs)

    return json.dumps({
        "scenario": scenario_name,
        "carbon_price_usd": cp,
        "revenue_shock_pct": rs,
        "est_ebitda_impact_pct": ebitda_impact,
        "emissions_delta_pct": emissions_delta,
        "hotspots": hotspots,
    }, indent=2)


async def query_emissions(sector: str | None = None, limit: int = 10) -> str:
    """Query EPA GHGRP emissions data by sector."""
    from sqlalchemy import desc, func, select

    from ..database.connection import async_session_factory
    from ..database.pipeline_models import EmissionsData

    async with async_session_factory() as db:
        query = select(EmissionsData).where(
            EmissionsData.total_emissions_mt_co2e.isnot(None)
        )
        if sector:
            query = query.where(EmissionsData.sector == sector)
        query = query.order_by(desc(EmissionsData.total_emissions_mt_co2e)).limit(limit)
        result = await db.execute(query)
        rows = result.scalars().all()

        if not rows:
            # Return sector summary instead
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
            return json.dumps({
                "message": "No facility data found" + (f" for sector '{sector}'" if sector else ""),
                "available_sectors": [
                    {"sector": r.sector, "total_mt_co2e": float(r.total or 0), "facilities": r.count}
                    for r in sector_rows
                ],
            }, indent=2)

    facilities = []
    for r in rows:
        facilities.append({
            "facility": r.facility_name or "Unknown",
            "state": r.state,
            "sector": r.sector,
            "total_emissions_mt_co2e": float(r.total_emissions_mt_co2e or 0),
            "reporting_year": r.reporting_year,
        })

    return json.dumps({"facilities": facilities, "count": len(facilities)}, indent=2)


async def search_documents(query: str, top_k: int = 5) -> str:
    """Semantic search through uploaded documents using the vector store."""
    from ..vectorstore import get_vector_store

    store = get_vector_store()
    if store.size == 0:
        return json.dumps({"message": "No documents indexed in the vector store.", "results": []})

    results = await store.search(query, top_k=top_k)
    return json.dumps({
        "query": query,
        "results": [
            {
                "text": r.document.text[:500],
                "source": r.document.source,
                "score": round(r.score, 4),
                "metadata": r.document.metadata,
            }
            for r in results
        ],
    }, indent=2)


async def compare_portfolios(portfolio_id_a: str, portfolio_id_b: str) -> str:
    """Compare two portfolios side-by-side on risk scores."""
    from ..database.connection import async_session_factory
    from ..database.seed import SECTOR_BASELINES
    from ..risk import score_portfolio
    from ..routes.portfolios import db_asset_to_pydantic, get_portfolio_by_id

    async with async_session_factory() as db:
        p_a = await get_portfolio_by_id(portfolio_id_a, db)
        p_b = await get_portfolio_by_id(portfolio_id_b, db)
        assets_a = [db_asset_to_pydantic(a) for a in p_a.assets]
        assets_b = [db_asset_to_pydantic(a) for a in p_b.assets]

    scores_a = score_portfolio(assets_a, SECTOR_BASELINES)
    scores_b = score_portfolio(assets_b, SECTOR_BASELINES)

    def _score_dict(name: str, scores: tuple) -> dict:
        return {
            "portfolio": name,
            "overall": scores[0],
            "climate_risk": scores[1],
            "transition_risk": scores[2],
            "physical_risk": scores[3],
            "opportunity": scores[4],
        }

    a = _score_dict(p_a.name, scores_a)
    b = _score_dict(p_b.name, scores_b)

    delta = {k: round(b[k] - a[k], 1) for k in a if k != "portfolio"}

    return json.dumps({"portfolio_a": a, "portfolio_b": b, "delta": delta}, indent=2)


# ── Tool registry ────────────────────────────────────────────────────────

CLIMATE_TOOLS: list[ToolDefinition] = [
    ToolDefinition(
        name="analyze_portfolio",
        description="Retrieve a portfolio's holdings, risk scores (transition, physical, opportunity), "
        "sector breakdown, top risks, and quick wins. Use this as the first step for any "
        "portfolio-related question.",
        parameters={
            "portfolio_id": {
                "type": "string",
                "description": "Portfolio ID. Omit to use the default portfolio.",
            },
        },
        execute=analyze_portfolio,
    ),
    ToolDefinition(
        name="run_scenario",
        description="Run a climate scenario stress test (e.g., Net Zero 2050, Delayed Transition, "
        "Current Policies) to estimate EBITDA impact, emissions changes, and hotspot assets.",
        parameters={
            "portfolio_id": {"type": "string", "description": "Portfolio ID."},
            "scenario_name": {
                "type": "string",
                "description": "Named scenario: 'Net Zero 2050', 'Delayed Transition', 'Current Policies'.",
            },
            "carbon_price": {
                "type": "number",
                "description": "Custom carbon price in USD/tCO2e. Overrides scenario default.",
            },
            "revenue_shock": {
                "type": "number",
                "description": "Custom revenue shock percentage. Overrides scenario default.",
            },
        },
        execute=run_scenario,
    ),
    ToolDefinition(
        name="query_emissions",
        description="Query real EPA GHGRP facility emissions data. Filter by sector to find "
        "top emitters, total emissions, and facility counts.",
        parameters={
            "sector": {
                "type": "string",
                "description": "Filter by sector name (e.g., 'Power Plants', 'Petroleum and Natural Gas Systems').",
            },
            "limit": {"type": "integer", "description": "Max facilities to return (default 10)."},
        },
        execute=query_emissions,
    ),
    ToolDefinition(
        name="search_documents",
        description="Semantic search through uploaded documents (PDFs, reports). Returns the most "
        "relevant text chunks ranked by similarity to the query.",
        parameters={
            "query": {"type": "string", "description": "Search query text."},
            "top_k": {"type": "integer", "description": "Number of results (default 5)."},
        },
        execute=search_documents,
    ),
    ToolDefinition(
        name="compare_portfolios",
        description="Compare two portfolios side-by-side on all risk dimensions. Returns scores "
        "for both and the delta between them.",
        parameters={
            "portfolio_id_a": {"type": "string", "description": "First portfolio ID."},
            "portfolio_id_b": {"type": "string", "description": "Second portfolio ID."},
        },
        execute=compare_portfolios,
    ),
]
