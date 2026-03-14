"""Asset repository for database operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import AssetDB


class AssetRepository:
    """Repository for Asset database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[AssetDB]:
        """Get all assets."""
        result = await self.session.execute(select(AssetDB).order_by(AssetDB.name))
        return list(result.scalars().all())

    async def get_by_id(self, asset_id: UUID) -> AssetDB | None:
        """Get an asset by ID."""
        result = await self.session.execute(select(AssetDB).where(AssetDB.id == asset_id))
        return result.scalar_one_or_none()

    async def get_by_sector(self, sector: str) -> list[AssetDB]:
        """Get assets by sector."""
        result = await self.session.execute(
            select(AssetDB).where(AssetDB.sector == sector).order_by(AssetDB.name)
        )
        return list(result.scalars().all())

    async def get_by_region(self, region: str) -> list[AssetDB]:
        """Get assets by region."""
        result = await self.session.execute(
            select(AssetDB).where(AssetDB.region == region).order_by(AssetDB.name)
        )
        return list(result.scalars().all())

    async def create(self, asset: AssetDB) -> AssetDB:
        """Create a new asset."""
        self.session.add(asset)
        await self.session.flush()
        return asset

    async def create_many(self, assets: list[AssetDB]) -> list[AssetDB]:
        """Create multiple assets."""
        self.session.add_all(assets)
        await self.session.flush()
        return assets

    async def update(self, asset: AssetDB) -> AssetDB:
        """Update an existing asset."""
        await self.session.flush()
        return asset

    async def delete(self, asset_id: UUID) -> bool:
        """Delete an asset by ID."""
        asset = await self.get_by_id(asset_id)
        if asset:
            await self.session.delete(asset)
            await self.session.flush()
            return True
        return False
