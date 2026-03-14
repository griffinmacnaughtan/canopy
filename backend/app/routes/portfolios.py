"""Portfolio management endpoints."""

import csv
import io
import uuid
from datetime import UTC, datetime

import structlog
from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.connection import get_db
from ..database.models import AssetDB, PortfolioDB
from ..database.seed import SECTOR_BASELINES
from ..exceptions import (
    InvalidPortfolioIdError,
    PortfolioNotFoundError,
    ValidationError,
)
from ..models import (
    Asset,
    ComparePortfoliosResponse,
    CreatePortfolioRequest,
    CreatePortfolioResponse,
    CsvImportResponse,
    DeletePortfolioResponse,
    Portfolio,
    PortfolioExportReport,
    PortfolioListResponse,
    PortfolioScoreSummary,
    PortfolioSummary,
    ScenarioImpactItem,
)
from ..risk import scenario_impact, score_portfolio

router = APIRouter()
logger = structlog.get_logger()

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

CSV_REQUIRED_COLUMNS = {
    "name",
    "sector",
    "region",
    "revenue_usd_m",
    "scope1_tco2e",
    "scope2_tco2e",
    "green_revenue_pct",
    "controversies",
}

VALID_SECTORS = {
    "Information Technology",
    "Energy",
    "Utilities",
    "Materials",
    "Industrials",
    "Consumer Discretionary",
    "Consumer Staples",
    "Healthcare",
    "Financials",
    "Real Estate",
    "Communication Services",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def db_asset_to_pydantic(asset: AssetDB) -> Asset:
    """Convert database asset to Pydantic model."""
    return Asset(
        id=str(asset.id),
        name=asset.name,
        ticker=asset.ticker,
        sector=asset.sector,
        region=asset.region,
        revenue_usd_m=asset.revenue_usd_m,
        scope1_tco2e=asset.scope1_tco2e,
        scope2_tco2e=asset.scope2_tco2e,
        green_revenue_pct=asset.green_revenue_pct,
        controversies=asset.controversies,
    )


def db_portfolio_to_pydantic(portfolio: PortfolioDB) -> Portfolio:
    """Convert database portfolio to Pydantic model."""
    return Portfolio(
        id=str(portfolio.id),
        name=portfolio.name,
        description=portfolio.description,
        assets=[db_asset_to_pydantic(a) for a in portfolio.assets],
    )


async def get_portfolio_by_id(
    portfolio_id: str | None,
    db: AsyncSession,
) -> PortfolioDB:
    """Get portfolio by ID, falling back to first portfolio if not specified."""
    if portfolio_id:
        try:
            pid = uuid.UUID(portfolio_id)
        except ValueError as e:
            raise InvalidPortfolioIdError(portfolio_id) from e

        result = await db.execute(select(PortfolioDB).where(PortfolioDB.id == pid))
        portfolio = result.scalar_one_or_none()
        if not portfolio:
            raise PortfolioNotFoundError(portfolio_id)
        return portfolio

    # Default to first portfolio
    result = await db.execute(select(PortfolioDB).limit(1))
    portfolio = result.scalar_one_or_none()
    if not portfolio:
        raise PortfolioNotFoundError("default")
    return portfolio


def _build_score_summary(portfolio: PortfolioDB) -> PortfolioScoreSummary:
    """Compute risk scores and return a compact summary object."""
    assets = [db_asset_to_pydantic(a) for a in portfolio.assets]
    overall, climate, transition, physical, opportunity, _, _, sector = score_portfolio(
        assets, SECTOR_BASELINES
    )
    total_emissions = sum(a.scope1_tco2e + a.scope2_tco2e for a in assets)
    avg_green = sum(a.green_revenue_pct for a in assets) / len(assets) if assets else 0.0
    return PortfolioScoreSummary(
        portfolio_id=str(portfolio.id),
        portfolio_name=portfolio.name,
        overall_score=overall,
        climate_risk=climate,
        transition_risk=transition,
        physical_risk=physical,
        opportunity_score=opportunity,
        asset_count=len(assets),
        total_emissions_tco2e=round(total_emissions, 0),
        avg_green_revenue_pct=round(avg_green, 1),
        sector_breakdown=sector,
    )


# ---------------------------------------------------------------------------
# Routes — List / Get
# ---------------------------------------------------------------------------


@router.get("/portfolios", response_model=PortfolioListResponse)
async def list_portfolios(db: AsyncSession = Depends(get_db)):
    """List all available portfolios."""
    result = await db.execute(select(PortfolioDB))
    portfolios = result.scalars().all()

    summaries = [
        PortfolioSummary(
            id=str(p.id),
            name=p.name,
            description=p.description,
            asset_count=len(p.assets),
            is_sample=p.is_sample,
        )
        for p in portfolios
    ]
    return PortfolioListResponse(portfolios=summaries)


@router.get("/portfolios/{portfolio_id}", response_model=Portfolio)
async def get_portfolio_by_id_endpoint(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific portfolio by ID."""
    portfolio = await get_portfolio_by_id(portfolio_id, db)
    return db_portfolio_to_pydantic(portfolio)


@router.get("/portfolio")
async def get_portfolio(
    portfolio_id: str | None = Query(None, description="Portfolio ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get the full portfolio with all assets (legacy endpoint)."""
    portfolio = await get_portfolio_by_id(portfolio_id, db)
    return db_portfolio_to_pydantic(portfolio)


@router.get("/assets")
async def list_assets(
    portfolio_id: str | None = Query(None, description="Portfolio ID"),
    db: AsyncSession = Depends(get_db),
):
    """List all portfolio assets."""
    portfolio = await get_portfolio_by_id(portfolio_id, db)
    return [db_asset_to_pydantic(a) for a in portfolio.assets]


# ---------------------------------------------------------------------------
# Routes — Create
# ---------------------------------------------------------------------------


@router.post("/portfolios", response_model=CreatePortfolioResponse)
async def create_portfolio(
    request: CreatePortfolioRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new custom portfolio."""
    db_assets = []
    for asset in request.assets:
        db_asset = AssetDB(
            id=uuid.uuid4(),
            name=asset.name,
            ticker=asset.ticker,
            sector=asset.sector,
            region=asset.region,
            revenue_usd_m=asset.revenue_usd_m,
            scope1_tco2e=asset.scope1_tco2e,
            scope2_tco2e=asset.scope2_tco2e,
            green_revenue_pct=asset.green_revenue_pct,
            controversies=asset.controversies,
        )
        db.add(db_asset)
        db_assets.append(db_asset)

    portfolio_id = uuid.uuid4()
    db_portfolio = PortfolioDB(
        id=portfolio_id,
        name=request.name,
        description=request.description or f"Custom portfolio with {len(request.assets)} assets",
        is_sample=False,
        assets=db_assets,
    )
    db.add(db_portfolio)
    await db.commit()

    logger.info("portfolio_created", portfolio_id=str(portfolio_id), name=request.name)

    return CreatePortfolioResponse(
        success=True,
        portfolio=PortfolioSummary(
            id=str(portfolio_id),
            name=db_portfolio.name,
            description=db_portfolio.description,
            asset_count=len(db_assets),
            is_sample=False,
        ),
        message=f"Successfully created portfolio '{request.name}' with {len(request.assets)} assets",
    )


# ---------------------------------------------------------------------------
# Routes — Delete
# ---------------------------------------------------------------------------


@router.delete("/portfolios/{portfolio_id}", response_model=DeletePortfolioResponse)
async def delete_portfolio(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Delete a custom portfolio.

    Sample portfolios are protected and cannot be deleted — only portfolios
    created by users (``is_sample=False``) may be removed.
    """
    portfolio = await get_portfolio_by_id(portfolio_id, db)

    if portfolio.is_sample:
        raise ValidationError(
            f"Sample portfolio '{portfolio.name}' cannot be deleted. "
            "Only custom portfolios may be removed."
        )

    name = portfolio.name
    await db.delete(portfolio)
    await db.commit()

    logger.info("portfolio_deleted", portfolio_id=portfolio_id, name=name)

    return DeletePortfolioResponse(
        success=True,
        message=f"Portfolio '{name}' has been deleted.",
    )


# ---------------------------------------------------------------------------
# Routes — Compare
# ---------------------------------------------------------------------------


@router.get("/portfolios/compare/diff", response_model=ComparePortfoliosResponse)
async def compare_portfolios(
    a: str = Query(..., description="First portfolio ID"),
    b: str = Query(..., description="Second portfolio ID"),
    db: AsyncSession = Depends(get_db),
):
    """
    Compare two portfolios side-by-side.

    Returns risk scores for both portfolios and a **delta** (B − A) for each
    numeric metric, making it easy to quantify the climate-risk difference
    between two investment strategies.
    """
    if a == b:
        raise ValidationError("Portfolio IDs must be different for comparison.")

    portfolio_a = await get_portfolio_by_id(a, db)
    portfolio_b = await get_portfolio_by_id(b, db)

    summary_a = _build_score_summary(portfolio_a)
    summary_b = _build_score_summary(portfolio_b)

    delta: dict[str, float] = {
        "overall_score": round(summary_b.overall_score - summary_a.overall_score, 1),
        "climate_risk": round(summary_b.climate_risk - summary_a.climate_risk, 1),
        "transition_risk": round(summary_b.transition_risk - summary_a.transition_risk, 1),
        "physical_risk": round(summary_b.physical_risk - summary_a.physical_risk, 1),
        "opportunity_score": round(summary_b.opportunity_score - summary_a.opportunity_score, 1),
        "total_emissions_tco2e": round(
            summary_b.total_emissions_tco2e - summary_a.total_emissions_tco2e, 0
        ),
    }

    # Plain-English recommendation
    if delta["climate_risk"] < -5:
        rec = (
            f"'{summary_b.portfolio_name}' carries materially lower climate risk "
            f"({abs(delta['climate_risk']):.1f} pts) and is better positioned for a "
            "carbon-constrained transition."
        )
    elif delta["climate_risk"] > 5:
        rec = (
            f"'{summary_a.portfolio_name}' carries materially lower climate risk "
            f"({abs(delta['climate_risk']):.1f} pts). Consider rebalancing "
            f"'{summary_b.portfolio_name}' toward lower-carbon sectors."
        )
    else:
        opp_delta = delta["opportunity_score"]
        rec = (
            "Both portfolios have similar climate risk profiles. "
            f"'{summary_b.portfolio_name}' offers "
            + (
                f"{opp_delta:+.1f} pts on opportunity score."
                if abs(opp_delta) >= 1
                else "comparable opportunity exposure."
            )
        )

    return ComparePortfoliosResponse(
        portfolio_a=summary_a,
        portfolio_b=summary_b,
        delta=delta,
        recommendation=rec,
    )


# ---------------------------------------------------------------------------
# Routes — Export / Report
# ---------------------------------------------------------------------------


@router.get("/portfolios/{portfolio_id}/export", response_model=PortfolioExportReport)
async def export_portfolio_report(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db),
):
    """
    Export a comprehensive risk report for a portfolio.

    Includes full risk scores, per-asset details (with emissions intensity),
    and stress-test results across all available NGFS-aligned scenarios.
    The response is structured for downstream consumption — PDF rendering,
    spreadsheet export, or BI tool ingestion.
    """
    from ..database.models import ScenarioDB as ScenDB

    portfolio = await get_portfolio_by_id(portfolio_id, db)
    assets = [db_asset_to_pydantic(a) for a in portfolio.assets]

    overall, climate, transition, physical, opportunity, top_risks, quick_wins, sector = (
        score_portfolio(assets, SECTOR_BASELINES)
    )

    # Run all stored scenarios
    result = await db.execute(select(ScenDB))
    scenarios = result.scalars().all()

    scenario_impacts: list[ScenarioImpactItem] = []
    for s in scenarios:
        ebitda, emissions_delta, hotspots = scenario_impact(assets, s.carbon_price, s.revenue_shock)
        scenario_impacts.append(
            ScenarioImpactItem(
                scenario=s.name,
                est_ebitda_impact_pct=ebitda,
                emissions_delta_pct=emissions_delta,
                hotspots=hotspots,
            )
        )

    asset_dicts = [
        {
            "id": a.id,
            "name": a.name,
            "ticker": a.ticker,
            "sector": a.sector,
            "region": a.region,
            "revenue_usd_m": a.revenue_usd_m,
            "scope1_tco2e": a.scope1_tco2e,
            "scope2_tco2e": a.scope2_tco2e,
            "total_emissions_tco2e": a.scope1_tco2e + a.scope2_tco2e,
            "emissions_intensity_tco2e_per_m_revenue": round(
                (a.scope1_tco2e + a.scope2_tco2e) / a.revenue_usd_m, 4
            )
            if a.revenue_usd_m > 0
            else 0,
            "green_revenue_pct": a.green_revenue_pct,
            "controversies": a.controversies,
        }
        for a in assets
    ]

    return PortfolioExportReport(
        generated_at=datetime.now(UTC).isoformat(),
        portfolio_id=str(portfolio.id),
        portfolio_name=portfolio.name,
        description=portfolio.description,
        asset_count=len(assets),
        overall_score=overall,
        climate_risk=climate,
        transition_risk=transition,
        physical_risk=physical,
        opportunity_score=opportunity,
        top_risks=top_risks,
        quick_wins=quick_wins,
        sector_breakdown=sector,
        assets=asset_dicts,
        scenario_impacts=scenario_impacts,
    )


# ---------------------------------------------------------------------------
# Routes — CSV Import
# ---------------------------------------------------------------------------


@router.post("/portfolios/import/csv", response_model=CsvImportResponse)
async def import_portfolio_from_csv(
    file: UploadFile = File(..., description="CSV file with asset data"),
    name: str | None = Query(None, description="Portfolio name (defaults to filename)"),
    db: AsyncSession = Depends(get_db),
):
    """
    Import a portfolio from a CSV file.

    ## Expected CSV columns
    | Column | Type | Required | Description |
    |---|---|---|---|
    | name | string | ✅ | Company name |
    | ticker | string | — | Stock ticker (optional) |
    | sector | string | ✅ | GICS sector name |
    | region | string | ✅ | Geographic region |
    | revenue_usd_m | float | ✅ | Annual revenue ($M) |
    | scope1_tco2e | float | ✅ | Scope 1 emissions (tCO2e) |
    | scope2_tco2e | float | ✅ | Scope 2 emissions (tCO2e) |
    | green_revenue_pct | float | ✅ | Green revenue % (0–100) |
    | controversies | int | ✅ | ESG controversy score (0–5) |

    Invalid rows are skipped with a warning; the import succeeds as long as
    at least one valid row exists.
    """
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise ValidationError("Only .csv files are accepted for bulk import.")

    content = await file.read()
    if len(content) > 5 * 1024 * 1024:  # 5 MB guard
        raise ValidationError("CSV file must be smaller than 5 MB.")

    try:
        text = content.decode("utf-8-sig")  # handle BOM from Excel exports
    except UnicodeDecodeError as e:
        raise ValidationError("CSV file must be UTF-8 encoded.") from e

    reader = csv.DictReader(io.StringIO(text))
    if reader.fieldnames is None:
        raise ValidationError("CSV file appears to be empty.")

    headers = {h.strip().lower() for h in reader.fieldnames if h}
    missing = CSV_REQUIRED_COLUMNS - headers
    if missing:
        raise ValidationError(
            f"CSV is missing required columns: {', '.join(sorted(missing))}. "
            f"Expected: {', '.join(sorted(CSV_REQUIRED_COLUMNS))}"
        )

    db_assets: list[AssetDB] = []
    warnings: list[str] = []
    rows_skipped = 0

    for row_num, raw_row in enumerate(reader, start=2):
        row = {k.strip().lower(): (v.strip() if v else "") for k, v in raw_row.items() if k}

        asset_name = row.get("name", "")
        if not asset_name:
            warnings.append(f"Row {row_num}: skipped — 'name' is empty.")
            rows_skipped += 1
            continue

        try:
            revenue = float(row["revenue_usd_m"])
            scope1 = float(row["scope1_tco2e"])
            scope2 = float(row["scope2_tco2e"])
            green_pct = float(row["green_revenue_pct"])
            controversies = int(float(row["controversies"]))
        except (ValueError, KeyError) as exc:
            warnings.append(f"Row {row_num} ({asset_name!r}): skipped — {exc}.")
            rows_skipped += 1
            continue

        if revenue <= 0:
            warnings.append(f"Row {row_num} ({asset_name!r}): skipped — revenue_usd_m must be > 0.")
            rows_skipped += 1
            continue

        # Clamp values to valid ranges
        green_pct = max(0.0, min(100.0, green_pct))
        controversies = max(0, min(5, controversies))
        scope1 = max(0.0, scope1)
        scope2 = max(0.0, scope2)

        sector = row.get("sector", "")
        if sector not in VALID_SECTORS:
            warnings.append(
                f"Row {row_num} ({asset_name!r}): unknown sector '{sector}' — "
                "keeping value but risk scoring will use fallback baseline."
            )

        db_asset = AssetDB(
            id=uuid.uuid4(),
            name=asset_name,
            ticker=row.get("ticker") or None,
            sector=sector,
            region=row.get("region", ""),
            revenue_usd_m=revenue,
            scope1_tco2e=scope1,
            scope2_tco2e=scope2,
            green_revenue_pct=green_pct,
            controversies=controversies,
        )
        db.add(db_asset)
        db_assets.append(db_asset)

    if not db_assets:
        raise ValidationError(
            "No valid rows found in CSV. "
            + (f"First warning: {warnings[0]}" if warnings else "Check the column format.")
        )

    portfolio_name = (
        (name or "").strip()
        or (file.filename.replace(".csv", "").replace("_", " ").strip())
        or "Imported Portfolio"
    )

    portfolio_id = uuid.uuid4()
    db_portfolio = PortfolioDB(
        id=portfolio_id,
        name=portfolio_name,
        description=f"Imported from {file.filename} — {len(db_assets)} assets",
        is_sample=False,
        assets=db_assets,
    )
    db.add(db_portfolio)
    await db.commit()

    logger.info(
        "portfolio_csv_imported",
        portfolio_id=str(portfolio_id),
        rows_imported=len(db_assets),
        rows_skipped=rows_skipped,
    )

    return CsvImportResponse(
        success=True,
        portfolio=PortfolioSummary(
            id=str(portfolio_id),
            name=portfolio_name,
            description=db_portfolio.description,
            asset_count=len(db_assets),
            is_sample=False,
        ),
        rows_imported=len(db_assets),
        rows_skipped=rows_skipped,
        warnings=warnings,
        message=(
            f"Successfully imported {len(db_assets)} assets into "
            f"portfolio '{portfolio_name}'."
            + (f" {rows_skipped} rows were skipped." if rows_skipped else "")
        ),
    )
