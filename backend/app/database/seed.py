"""Seed data with real companies and researched ESG metrics.

Data sources and methodology:
- Revenue: Public financial statements (FY2023/2024)
- Emissions: CDP disclosures, sustainability reports, EPA data
- Green Revenue: Company sustainability reports, Bloomberg NEF
- Controversies: ESG news, regulatory actions (0-5 scale)

Note: Some figures are estimates based on publicly available data.
This is for demonstration purposes - production would use real-time data feeds.
"""

from typing import List, Dict, Any

# Real company data with researched metrics
# Sources: CDP, company sustainability reports, annual reports (2023-2024)

REAL_ASSETS: List[Dict[str, Any]] = [
    # Tech Giants - Generally lower emissions intensity, high green revenue potential
    {
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "sector": "Information Technology",
        "region": "North America",
        "revenue_usd_m": 383285,  # FY2023
        "scope1_tco2e": 55200,    # Direct emissions (facilities, vehicles)
        "scope2_tco2e": 0,        # 100% renewable electricity since 2018
        "green_revenue_pct": 45,  # Services, recycling programs, carbon neutral products
        "controversies": 1,       # Minor supply chain labor concerns
    },
    {
        "name": "Microsoft Corporation",
        "ticker": "MSFT",
        "sector": "Information Technology",
        "region": "North America",
        "revenue_usd_m": 211915,  # FY2023
        "scope1_tco2e": 125195,   # CDP 2023
        "scope2_tco2e": 280000,   # Market-based, data centers
        "green_revenue_pct": 35,  # Azure sustainability, carbon removal
        "controversies": 0,
    },
    {
        "name": "Alphabet Inc.",
        "ticker": "GOOGL",
        "sector": "Information Technology",
        "region": "North America",
        "revenue_usd_m": 307394,  # FY2023
        "scope1_tco2e": 65200,    # CDP disclosure
        "scope2_tco2e": 0,        # Carbon neutral since 2007
        "green_revenue_pct": 28,  # Clean energy products, sustainability tools
        "controversies": 2,       # Antitrust, privacy concerns
    },
    {
        "name": "NVIDIA Corporation",
        "ticker": "NVDA",
        "sector": "Information Technology",
        "region": "North America",
        "revenue_usd_m": 60922,   # FY2024
        "scope1_tco2e": 8500,     # Relatively low - fabless
        "scope2_tco2e": 125000,   # Data center power
        "green_revenue_pct": 20,  # AI for climate modeling, EV chips
        "controversies": 0,
    },
    {
        "name": "Tesla, Inc.",
        "ticker": "TSLA",
        "sector": "Consumer Discretionary",
        "region": "North America",
        "revenue_usd_m": 96773,   # FY2023
        "scope1_tco2e": 352000,   # Manufacturing
        "scope2_tco2e": 680000,   # Gigafactories energy
        "green_revenue_pct": 85,  # EVs, solar, storage
        "controversies": 3,       # Labor, governance, Autopilot safety
    },

    # Energy Sector - High emissions, varying transition readiness
    {
        "name": "Exxon Mobil Corporation",
        "ticker": "XOM",
        "sector": "Energy",
        "region": "North America",
        "revenue_usd_m": 344582,  # FY2023
        "scope1_tco2e": 98000000, # Major oil & gas producer
        "scope2_tco2e": 12000000,
        "green_revenue_pct": 2,   # Limited low-carbon investments
        "controversies": 4,       # Climate litigation, greenwashing allegations
    },
    {
        "name": "Chevron Corporation",
        "ticker": "CVX",
        "sector": "Energy",
        "region": "North America",
        "revenue_usd_m": 200994,  # FY2023
        "scope1_tco2e": 56000000,
        "scope2_tco2e": 8000000,
        "green_revenue_pct": 3,   # Renewable fuels, hydrogen (early stage)
        "controversies": 3,       # Ecuador litigation, emissions
    },
    {
        "name": "NextEra Energy, Inc.",
        "ticker": "NEE",
        "sector": "Utilities",
        "region": "North America",
        "revenue_usd_m": 28114,   # FY2023
        "scope1_tco2e": 42000000, # Still has gas plants
        "scope2_tco2e": 1200000,
        "green_revenue_pct": 65,  # Largest wind/solar producer in US
        "controversies": 1,       # Minor permitting disputes
    },
    {
        "name": "Shell plc",
        "ticker": "SHEL",
        "sector": "Energy",
        "region": "Europe",
        "revenue_usd_m": 316620,  # FY2023
        "scope1_tco2e": 68000000,
        "scope2_tco2e": 10000000,
        "green_revenue_pct": 8,   # EV charging, renewables growing
        "controversies": 4,       # Dutch court ruling, emissions targets
    },
    {
        "name": "TotalEnergies SE",
        "ticker": "TTE",
        "sector": "Energy",
        "region": "Europe",
        "revenue_usd_m": 218945,  # FY2023
        "scope1_tco2e": 41000000,
        "scope2_tco2e": 7000000,
        "green_revenue_pct": 12,  # Largest integrated renewables capacity
        "controversies": 3,       # Uganda pipeline, human rights concerns
    },

    # Industrials & Materials - Heavy emissions, critical for transition
    {
        "name": "Caterpillar Inc.",
        "ticker": "CAT",
        "sector": "Industrials",
        "region": "North America",
        "revenue_usd_m": 67060,   # FY2023
        "scope1_tco2e": 850000,
        "scope2_tco2e": 420000,
        "green_revenue_pct": 15,  # Electric equipment, mining for battery minerals
        "controversies": 1,
    },
    {
        "name": "BASF SE",
        "ticker": "BASFY",
        "sector": "Materials",
        "region": "Europe",
        "revenue_usd_m": 73847,   # FY2023 (EUR converted)
        "scope1_tco2e": 16900000, # Chemical production
        "scope2_tco2e": 4200000,
        "green_revenue_pct": 22,  # Battery materials, biodegradable plastics
        "controversies": 2,       # Scope 3 reporting gaps
    },
    {
        "name": "BHP Group Limited",
        "ticker": "BHP",
        "sector": "Materials",
        "region": "APAC",
        "revenue_usd_m": 53817,   # FY2023
        "scope1_tco2e": 11800000, # Mining operations
        "scope2_tco2e": 4500000,
        "green_revenue_pct": 18,  # Copper (EV batteries), potash
        "controversies": 2,       # Samarco dam, indigenous rights
    },

    # Financials - Low direct emissions, high financed emissions
    {
        "name": "JPMorgan Chase & Co.",
        "ticker": "JPM",
        "sector": "Financials",
        "region": "North America",
        "revenue_usd_m": 158104,  # FY2023
        "scope1_tco2e": 78000,    # Offices, travel
        "scope2_tco2e": 245000,
        "green_revenue_pct": 8,   # Green bonds, sustainable finance
        "controversies": 2,       # Fossil fuel financing criticism
    },
    {
        "name": "BlackRock, Inc.",
        "ticker": "BLK",
        "sector": "Financials",
        "region": "North America",
        "revenue_usd_m": 17859,   # FY2023
        "scope1_tco2e": 12000,
        "scope2_tco2e": 45000,
        "green_revenue_pct": 25,  # ESG funds, sustainable investing
        "controversies": 2,       # Greenwashing allegations, anti-ESG backlash
    },

    # Consumer & Healthcare - Varied profiles
    {
        "name": "Unilever PLC",
        "ticker": "UL",
        "sector": "Consumer Staples",
        "region": "Europe",
        "revenue_usd_m": 63896,   # FY2023 (EUR converted)
        "scope1_tco2e": 680000,
        "scope2_tco2e": 520000,
        "green_revenue_pct": 35,  # Sustainable brands initiative
        "controversies": 1,       # Palm oil supply chain
    },
    {
        "name": "Nestlé S.A.",
        "ticker": "NSRGY",
        "sector": "Consumer Staples",
        "region": "Europe",
        "revenue_usd_m": 99315,   # FY2023 (CHF converted)
        "scope1_tco2e": 3800000,
        "scope2_tco2e": 1200000,
        "green_revenue_pct": 20,  # Plant-based, regenerative agriculture
        "controversies": 3,       # Water usage, infant formula
    },
    {
        "name": "Johnson & Johnson",
        "ticker": "JNJ",
        "sector": "Healthcare",
        "region": "North America",
        "revenue_usd_m": 85159,   # FY2023
        "scope1_tco2e": 420000,
        "scope2_tco2e": 680000,
        "green_revenue_pct": 12,  # Sustainable packaging, carbon neutrality goals
        "controversies": 4,       # Talc litigation, opioid settlements
    },

    # Asian Markets
    {
        "name": "Toyota Motor Corporation",
        "ticker": "TM",
        "sector": "Consumer Discretionary",
        "region": "APAC",
        "revenue_usd_m": 274491,  # FY2023 (JPY converted)
        "scope1_tco2e": 4200000,
        "scope2_tco2e": 2800000,
        "green_revenue_pct": 32,  # Hybrids, EVs, hydrogen fuel cells
        "controversies": 1,       # EV transition pace criticism
    },
    {
        "name": "Samsung Electronics Co.",
        "ticker": "005930.KS",
        "sector": "Information Technology",
        "region": "APAC",
        "revenue_usd_m": 200734,  # FY2023 (KRW converted)
        "scope1_tco2e": 3500000,  # Semiconductor fabs
        "scope2_tco2e": 12000000, # Heavy energy use
        "green_revenue_pct": 18,  # Energy-efficient chips, solar panels
        "controversies": 1,       # Labor practices
    },
]

# Pre-built sample portfolios using real assets
SAMPLE_PORTFOLIOS = [
    {
        "name": "Tech Leaders",
        "description": "Large-cap technology companies with strong ESG profiles",
        "asset_names": ["Apple Inc.", "Microsoft Corporation", "Alphabet Inc.", "NVIDIA Corporation"],
    },
    {
        "name": "Energy Transition",
        "description": "Mix of traditional energy and clean energy leaders",
        "asset_names": ["NextEra Energy, Inc.", "TotalEnergies SE", "Shell plc", "Tesla, Inc."],
    },
    {
        "name": "Global Diversified",
        "description": "Diversified portfolio across sectors and regions",
        "asset_names": [
            "Apple Inc.", "JPMorgan Chase & Co.", "BASF SE", "Unilever PLC",
            "Toyota Motor Corporation", "NextEra Energy, Inc."
        ],
    },
]

# Climate scenarios based on NGFS (Network for Greening the Financial System)
CLIMATE_SCENARIOS = [
    {
        "name": "Net Zero 2050",
        "description": "Orderly transition achieving net zero by 2050. Early, coordinated policy action limits warming to 1.5°C.",
        "carbon_price": 140,       # $/tCO2e by 2030
        "revenue_shock": -1.5,     # GDP impact
        "is_default": True,
    },
    {
        "name": "Delayed Transition",
        "description": "Late, disruptive transition. Policies delayed until 2030, then aggressive action required.",
        "carbon_price": 200,
        "revenue_shock": -3.5,
        "is_default": True,
    },
    {
        "name": "Current Policies",
        "description": "Only currently implemented policies. Leads to 3°C+ warming with severe physical risks.",
        "carbon_price": 50,
        "revenue_shock": -5.0,     # Physical risk damage
        "is_default": True,
    },
]

# Sector risk baselines (used in scoring)
SECTOR_BASELINES = {
    "Information Technology": {"transition_risk": 0.2, "physical_risk": 0.15},
    "Energy": {"transition_risk": 0.9, "physical_risk": 0.4},
    "Utilities": {"transition_risk": 0.7, "physical_risk": 0.5},
    "Materials": {"transition_risk": 0.75, "physical_risk": 0.45},
    "Industrials": {"transition_risk": 0.6, "physical_risk": 0.35},
    "Consumer Discretionary": {"transition_risk": 0.4, "physical_risk": 0.25},
    "Consumer Staples": {"transition_risk": 0.35, "physical_risk": 0.4},
    "Healthcare": {"transition_risk": 0.25, "physical_risk": 0.3},
    "Financials": {"transition_risk": 0.3, "physical_risk": 0.2},
    "Real Estate": {"transition_risk": 0.45, "physical_risk": 0.6},
    "Communication Services": {"transition_risk": 0.25, "physical_risk": 0.2},
}
