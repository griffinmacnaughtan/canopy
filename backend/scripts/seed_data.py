"""Seed script to populate the database with initial data."""

import sys
from pathlib import Path

# Add the backend directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.config import get_settings
from app.database.models import AssetDB, PortfolioDB, ScenarioDB, UserDB


def seed_database():
    """Seed the database with initial demo data."""
    settings = get_settings()
    engine = create_engine(settings.database_sync_url)

    with Session(engine) as session:
        # Check if data already exists
        existing_assets = session.query(AssetDB).first()
        if existing_assets:
            print("Database already seeded. Skipping...")
            return

        print("Seeding database...")

        # Create demo user
        demo_user = UserDB(
            email="demo@esg-copilot.com",
            name="Demo User",
        )
        session.add(demo_user)
        session.flush()

        # Create assets
        assets = [
            AssetDB(
                name="NorthGrid Utilities",
                sector="Utilities",
                region="North America",
                revenue_usd_m=4200,
                scope1_tco2e=8_200_000,
                scope2_tco2e=1_100_000,
                green_revenue_pct=12,
                controversies=2,
            ),
            AssetDB(
                name="BlueSteel Manufacturing",
                sector="Materials",
                region="Europe",
                revenue_usd_m=2800,
                scope1_tco2e=4_600_000,
                scope2_tco2e=900_000,
                green_revenue_pct=6,
                controversies=3,
            ),
            AssetDB(
                name="Riverline Logistics",
                sector="Industrials",
                region="North America",
                revenue_usd_m=1900,
                scope1_tco2e=1_200_000,
                scope2_tco2e=380_000,
                green_revenue_pct=8,
                controversies=1,
            ),
            AssetDB(
                name="Sunshore Real Assets",
                sector="Real Estate",
                region="APAC",
                revenue_usd_m=1400,
                scope1_tco2e=420_000,
                scope2_tco2e=250_000,
                green_revenue_pct=22,
                controversies=0,
            ),
            AssetDB(
                name="Photonix Tech",
                sector="Information Technology",
                region="Europe",
                revenue_usd_m=3100,
                scope1_tco2e=120_000,
                scope2_tco2e=380_000,
                green_revenue_pct=34,
                controversies=0,
            ),
        ]
        session.add_all(assets)
        session.flush()

        # Create portfolio
        portfolio = PortfolioDB(
            name="Global Infrastructure Growth",
            user_id=demo_user.id,
        )
        portfolio.assets = assets
        session.add(portfolio)
        session.flush()

        # Create scenarios
        scenarios = [
            ScenarioDB(
                name="Orderly Net Zero 2050",
                description="An orderly transition to net zero by 2050 with early, coordinated policy action.",
                carbon_price=120,
                revenue_shock=-1.8,
                is_default=True,
            ),
            ScenarioDB(
                name="Delayed Transition",
                description="Delayed policy action leads to higher carbon prices and abrupt transition.",
                carbon_price=180,
                revenue_shock=-3.1,
                is_default=True,
            ),
            ScenarioDB(
                name="Hot House World",
                description="Limited policy action results in severe physical risks from climate change.",
                carbon_price=40,
                revenue_shock=-4.4,
                is_default=True,
            ),
        ]
        session.add_all(scenarios)

        session.commit()
        print("Database seeded successfully!")
        print("  - Created 1 demo user")
        print(f"  - Created {len(assets)} assets")
        print("  - Created 1 portfolio")
        print(f"  - Created {len(scenarios)} scenarios")


if __name__ == "__main__":
    seed_database()
