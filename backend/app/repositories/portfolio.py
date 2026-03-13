"""Portfolio repository for database operations."""

from typing import List, Optional
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from ..database.models import PortfolioDB, AssetDB


class PortfolioRepository:
    """Repository for Portfolio database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> List[PortfolioDB]:
        """Get all portfolios with their assets."""
        result = await self.session.execute(
            select(PortfolioDB)
            .options(selectinload(PortfolioDB.assets))
            .order_by(PortfolioDB.name)
        )
        return list(result.scalars().all())

    async def get_by_id(self, portfolio_id: UUID) -> Optional[PortfolioDB]:
        """Get a portfolio by ID with its assets."""
        result = await self.session.execute(
            select(PortfolioDB)
            .options(selectinload(PortfolioDB.assets))
            .where(PortfolioDB.id == portfolio_id)
        )
        return result.scalar_one_or_none()

    async def get_by_user_id(self, user_id: UUID) -> List[PortfolioDB]:
        """Get portfolios by user ID."""
        result = await self.session.execute(
            select(PortfolioDB)
            .options(selectinload(PortfolioDB.assets))
            .where(PortfolioDB.user_id == user_id)
            .order_by(PortfolioDB.name)
        )
        return list(result.scalars().all())

    async def get_default(self) -> Optional[PortfolioDB]:
        """Get the first available portfolio (default for demo)."""
        result = await self.session.execute(
            select(PortfolioDB)
            .options(selectinload(PortfolioDB.assets))
            .order_by(PortfolioDB.created_at)
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def create(self, portfolio: PortfolioDB) -> PortfolioDB:
        """Create a new portfolio."""
        self.session.add(portfolio)
        await self.session.flush()
        return portfolio

    async def add_asset(self, portfolio_id: UUID, asset: AssetDB) -> Optional[PortfolioDB]:
        """Add an asset to a portfolio."""
        portfolio = await self.get_by_id(portfolio_id)
        if portfolio:
            portfolio.assets.append(asset)
            await self.session.flush()
        return portfolio

    async def remove_asset(self, portfolio_id: UUID, asset_id: UUID) -> Optional[PortfolioDB]:
        """Remove an asset from a portfolio."""
        portfolio = await self.get_by_id(portfolio_id)
        if portfolio:
            portfolio.assets = [a for a in portfolio.assets if a.id != asset_id]
            await self.session.flush()
        return portfolio

    async def update(self, portfolio: PortfolioDB) -> PortfolioDB:
        """Update an existing portfolio."""
        await self.session.flush()
        return portfolio

    async def delete(self, portfolio_id: UUID) -> bool:
        """Delete a portfolio by ID."""
        portfolio = await self.get_by_id(portfolio_id)
        if portfolio:
            await self.session.delete(portfolio)
            await self.session.flush()
            return True
        return False
