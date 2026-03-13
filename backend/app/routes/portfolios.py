"""Portfolio management endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from ..database.connection import get_db
from ..database.models import PortfolioDB, AssetDB
from ..models import (
    PortfolioSummary,
    PortfolioListResponse,
    CreatePortfolioRequest,
    CreatePortfolioResponse,
    Portfolio,
    Asset,
)
from ..exceptions import PortfolioNotFoundError, InvalidPortfolioIdError

router = APIRouter()


# =============================================================================
# Helper Functions
# =============================================================================


def db_asset_to_pydantic(asset: AssetDB) -> Asset:
    """Convert database asset to Pydantic model."""
    return Asset(
        id=str(asset.id),
        name=asset.name,
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
    portfolio_id: Optional[str],
    db: AsyncSession,
) -> PortfolioDB:
    """Get portfolio by ID, falling back to first portfolio if not specified."""
    if portfolio_id:
        try:
            pid = uuid.UUID(portfolio_id)
        except ValueError:
            raise InvalidPortfolioIdError(portfolio_id)

        result = await db.execute(
            select(PortfolioDB).where(PortfolioDB.id == pid)
        )
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


# =============================================================================
# Routes
# =============================================================================


@router.get("/portfolios", response_model=PortfolioListResponse)
async def list_portfolios(db: AsyncSession = Depends(get_db)):
    """List all available portfolios."""
    result = await db.execute(select(PortfolioDB))
    portfolios = result.scalars().all()

    summaries = [
        PortfolioSummary(
            id=str(p.id),
            name=p.name,
            description=p.description or "",
            asset_count=len(p.assets),
        )
        for p in portfolios
    ]
    return PortfolioListResponse(portfolios=summaries)


@router.get("/portfolios/{portfolio_id}")
async def get_portfolio_by_id_endpoint(
    portfolio_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a specific portfolio by ID."""
    portfolio = await get_portfolio_by_id(portfolio_id, db)
    return db_portfolio_to_pydantic(portfolio)


@router.post("/portfolios", response_model=CreatePortfolioResponse)
async def create_portfolio(
    request: CreatePortfolioRequest,
    db: AsyncSession = Depends(get_db),
):
    """Create a new custom portfolio."""
    # Create assets
    db_assets = []
    for asset in request.assets:
        db_asset = AssetDB(
            id=uuid.uuid4(),
            name=asset.name,
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

    # Create portfolio
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

    return CreatePortfolioResponse(
        success=True,
        portfolio=PortfolioSummary(
            id=str(portfolio_id),
            name=db_portfolio.name,
            description=db_portfolio.description or "",
            asset_count=len(db_assets),
        ),
        message=f"Successfully created portfolio '{request.name}' with {len(request.assets)} assets",
    )


@router.get("/assets")
async def list_assets(
    portfolio_id: Optional[str] = Query(None, description="Portfolio ID"),
    db: AsyncSession = Depends(get_db),
):
    """List all portfolio assets."""
    portfolio = await get_portfolio_by_id(portfolio_id, db)
    return [db_asset_to_pydantic(a) for a in portfolio.assets]


@router.get("/portfolio")
async def get_portfolio(
    portfolio_id: Optional[str] = Query(None, description="Portfolio ID"),
    db: AsyncSession = Depends(get_db),
):
    """Get the full portfolio with all assets."""
    portfolio = await get_portfolio_by_id(portfolio_id, db)
    return db_portfolio_to_pydantic(portfolio)
