"""Scenario repository for database operations."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import ScenarioDB


class ScenarioRepository:
    """Repository for Scenario database operations."""

    def __init__(self, session: AsyncSession):
        self.session = session

    async def get_all(self) -> list[ScenarioDB]:
        """Get all scenarios."""
        result = await self.session.execute(select(ScenarioDB).order_by(ScenarioDB.name))
        return list(result.scalars().all())

    async def get_by_id(self, scenario_id: UUID) -> ScenarioDB | None:
        """Get a scenario by ID."""
        result = await self.session.execute(select(ScenarioDB).where(ScenarioDB.id == scenario_id))
        return result.scalar_one_or_none()

    async def get_by_name(self, name: str) -> ScenarioDB | None:
        """Get a scenario by name."""
        result = await self.session.execute(select(ScenarioDB).where(ScenarioDB.name == name))
        return result.scalar_one_or_none()

    async def get_defaults(self) -> list[ScenarioDB]:
        """Get all default scenarios."""
        result = await self.session.execute(
            select(ScenarioDB).where(ScenarioDB.is_default).order_by(ScenarioDB.name)
        )
        return list(result.scalars().all())

    async def create(self, scenario: ScenarioDB) -> ScenarioDB:
        """Create a new scenario."""
        self.session.add(scenario)
        await self.session.flush()
        return scenario

    async def create_many(self, scenarios: list[ScenarioDB]) -> list[ScenarioDB]:
        """Create multiple scenarios."""
        self.session.add_all(scenarios)
        await self.session.flush()
        return scenarios

    async def update(self, scenario: ScenarioDB) -> ScenarioDB:
        """Update an existing scenario."""
        await self.session.flush()
        return scenario

    async def delete(self, scenario_id: UUID) -> bool:
        """Delete a scenario by ID."""
        scenario = await self.get_by_id(scenario_id)
        if scenario:
            await self.session.delete(scenario)
            await self.session.flush()
            return True
        return False
