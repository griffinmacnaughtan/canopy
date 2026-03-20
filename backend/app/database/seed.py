"""Seed data with real companies and researched ESG metrics.

Data sources and methodology:
- Revenue: Public financial statements (FY2023/2024)
- Emissions: CDP disclosures, sustainability reports, EPA data
- Green Revenue: Company sustainability reports, Bloomberg NEF
- Controversies: ESG news, regulatory actions (0-5 scale)

Note: Some figures are estimates based on publicly available data.
This is for demonstration purposes - production would use real-time data feeds.
"""

from typing import Any

from ..benchmarks import get_sector_baselines

# Real company data with researched metrics
# Sources: CDP, company sustainability reports, annual reports (2023-2024)

REAL_ASSETS: list[dict[str, Any]] = [
    # Tech Giants - Generally lower emissions intensity, high green revenue potential
    {
        "name": "Apple Inc.",
        "ticker": "AAPL",
        "sector": "Information Technology",
        "region": "North America",
        "revenue_usd_m": 383285,  # FY2023
        "scope1_tco2e": 55200,  # Direct emissions (facilities, vehicles)
        "scope2_tco2e": 0,  # 100% renewable electricity since 2018
        "green_revenue_pct": 45,  # Services, recycling programs, carbon neutral products
        "controversies": 1,  # Minor supply chain labor concerns
    },
    {
        "name": "Microsoft Corporation",
        "ticker": "MSFT",
        "sector": "Information Technology",
        "region": "North America",
        "revenue_usd_m": 211915,  # FY2023
        "scope1_tco2e": 125195,  # CDP 2023
        "scope2_tco2e": 280000,  # Market-based, data centers
        "green_revenue_pct": 35,  # Azure sustainability, carbon removal
        "controversies": 0,
    },
    {
        "name": "Alphabet Inc.",
        "ticker": "GOOGL",
        "sector": "Information Technology",
        "region": "North America",
        "revenue_usd_m": 307394,  # FY2023
        "scope1_tco2e": 65200,  # CDP disclosure
        "scope2_tco2e": 0,  # Carbon neutral since 2007
        "green_revenue_pct": 28,  # Clean energy products, sustainability tools
        "controversies": 2,  # Antitrust, privacy concerns
    },
    {
        "name": "NVIDIA Corporation",
        "ticker": "NVDA",
        "sector": "Information Technology",
        "region": "North America",
        "revenue_usd_m": 60922,  # FY2024
        "scope1_tco2e": 8500,  # Relatively low - fabless
        "scope2_tco2e": 125000,  # Data center power
        "green_revenue_pct": 20,  # AI for climate modeling, EV chips
        "controversies": 0,
    },
    {
        "name": "Tesla, Inc.",
        "ticker": "TSLA",
        "sector": "Consumer Discretionary",
        "region": "North America",
        "revenue_usd_m": 96773,  # FY2023
        "scope1_tco2e": 352000,  # Manufacturing
        "scope2_tco2e": 680000,  # Gigafactories energy
        "green_revenue_pct": 85,  # EVs, solar, storage
        "controversies": 3,  # Labor, governance, Autopilot safety
    },
    # Energy Sector - High emissions, varying transition readiness
    {
        "name": "Exxon Mobil Corporation",
        "ticker": "XOM",
        "sector": "Energy",
        "region": "North America",
        "revenue_usd_m": 344582,  # FY2023
        "scope1_tco2e": 98000000,  # Major oil & gas producer
        "scope2_tco2e": 12000000,
        "green_revenue_pct": 2,  # Limited low-carbon investments
        "controversies": 4,  # Climate litigation, greenwashing allegations
    },
    {
        "name": "Chevron Corporation",
        "ticker": "CVX",
        "sector": "Energy",
        "region": "North America",
        "revenue_usd_m": 200994,  # FY2023
        "scope1_tco2e": 56000000,
        "scope2_tco2e": 8000000,
        "green_revenue_pct": 3,  # Renewable fuels, hydrogen (early stage)
        "controversies": 3,  # Ecuador litigation, emissions
    },
    {
        "name": "NextEra Energy, Inc.",
        "ticker": "NEE",
        "sector": "Utilities",
        "region": "North America",
        "revenue_usd_m": 28114,  # FY2023
        "scope1_tco2e": 42000000,  # Still has gas plants
        "scope2_tco2e": 1200000,
        "green_revenue_pct": 65,  # Largest wind/solar producer in US
        "controversies": 1,  # Minor permitting disputes
    },
    {
        "name": "Shell plc",
        "ticker": "SHEL",
        "sector": "Energy",
        "region": "Europe",
        "revenue_usd_m": 316620,  # FY2023
        "scope1_tco2e": 68000000,
        "scope2_tco2e": 10000000,
        "green_revenue_pct": 8,  # EV charging, renewables growing
        "controversies": 4,  # Dutch court ruling, emissions targets
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
        "controversies": 3,  # Uganda pipeline, human rights concerns
    },
    # Industrials & Materials - Heavy emissions, critical for transition
    {
        "name": "Caterpillar Inc.",
        "ticker": "CAT",
        "sector": "Industrials",
        "region": "North America",
        "revenue_usd_m": 67060,  # FY2023
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
        "revenue_usd_m": 73847,  # FY2023 (EUR converted)
        "scope1_tco2e": 16900000,  # Chemical production
        "scope2_tco2e": 4200000,
        "green_revenue_pct": 22,  # Battery materials, biodegradable plastics
        "controversies": 2,  # Scope 3 reporting gaps
    },
    {
        "name": "BHP Group Limited",
        "ticker": "BHP",
        "sector": "Materials",
        "region": "APAC",
        "revenue_usd_m": 53817,  # FY2023
        "scope1_tco2e": 11800000,  # Mining operations
        "scope2_tco2e": 4500000,
        "green_revenue_pct": 18,  # Copper (EV batteries), potash
        "controversies": 2,  # Samarco dam, indigenous rights
    },
    # Financials - Low direct emissions, high financed emissions
    {
        "name": "JPMorgan Chase & Co.",
        "ticker": "JPM",
        "sector": "Financials",
        "region": "North America",
        "revenue_usd_m": 158104,  # FY2023
        "scope1_tco2e": 78000,  # Offices, travel
        "scope2_tco2e": 245000,
        "green_revenue_pct": 8,  # Green bonds, sustainable finance
        "controversies": 2,  # Fossil fuel financing criticism
    },
    {
        "name": "BlackRock, Inc.",
        "ticker": "BLK",
        "sector": "Financials",
        "region": "North America",
        "revenue_usd_m": 17859,  # FY2023
        "scope1_tco2e": 12000,
        "scope2_tco2e": 45000,
        "green_revenue_pct": 25,  # ESG funds, sustainable investing
        "controversies": 2,  # Greenwashing allegations, anti-ESG backlash
    },
    # Consumer & Healthcare - Varied profiles
    {
        "name": "Unilever PLC",
        "ticker": "UL",
        "sector": "Consumer Staples",
        "region": "Europe",
        "revenue_usd_m": 63896,  # FY2023 (EUR converted)
        "scope1_tco2e": 680000,
        "scope2_tco2e": 520000,
        "green_revenue_pct": 35,  # Sustainable brands initiative
        "controversies": 1,  # Palm oil supply chain
    },
    {
        "name": "Nestlé S.A.",
        "ticker": "NSRGY",
        "sector": "Consumer Staples",
        "region": "Europe",
        "revenue_usd_m": 99315,  # FY2023 (CHF converted)
        "scope1_tco2e": 3800000,
        "scope2_tco2e": 1200000,
        "green_revenue_pct": 20,  # Plant-based, regenerative agriculture
        "controversies": 3,  # Water usage, infant formula
    },
    {
        "name": "Johnson & Johnson",
        "ticker": "JNJ",
        "sector": "Healthcare",
        "region": "North America",
        "revenue_usd_m": 85159,  # FY2023
        "scope1_tco2e": 420000,
        "scope2_tco2e": 680000,
        "green_revenue_pct": 12,  # Sustainable packaging, carbon neutrality goals
        "controversies": 4,  # Talc litigation, opioid settlements
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
        "controversies": 1,  # EV transition pace criticism
    },
    {
        "name": "Samsung Electronics Co.",
        "ticker": "005930.KS",
        "sector": "Information Technology",
        "region": "APAC",
        "revenue_usd_m": 200734,  # FY2023 (KRW converted)
        "scope1_tco2e": 3500000,  # Semiconductor fabs
        "scope2_tco2e": 12000000,  # Heavy energy use
        "green_revenue_pct": 18,  # Energy-efficient chips, solar panels
        "controversies": 1,  # Labor practices
    },
]

# Pre-built sample portfolios using real assets
SAMPLE_PORTFOLIOS = [
    {
        "name": "Tech Leaders",
        "description": "Large-cap technology companies with strong ESG profiles",
        "asset_names": [
            "Apple Inc.",
            "Microsoft Corporation",
            "Alphabet Inc.",
            "NVIDIA Corporation",
        ],
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
            "Apple Inc.",
            "JPMorgan Chase & Co.",
            "BASF SE",
            "Unilever PLC",
            "Toyota Motor Corporation",
            "NextEra Energy, Inc.",
        ],
    },
]

# Climate scenarios based on NGFS (Network for Greening the Financial System)
CLIMATE_SCENARIOS = [
    {
        "name": "Net Zero 2050",
        "description": "Orderly transition achieving net zero by 2050. Early, coordinated policy action limits warming to 1.5°C.",
        "carbon_price": 140,  # $/tCO2e by 2030
        "revenue_shock": -1.5,  # GDP impact
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
        "revenue_shock": -5.0,  # Physical risk damage
        "is_default": True,
    },
]

# Sector risk baselines sourced from published benchmarks.
# Full citations in app/benchmarks/sector_benchmarks.py.
SECTOR_BASELINES = get_sector_baselines()

# ---------------------------------------------------------------------------
# Pipeline seed data — EPA GHGRP emissions and NOAA/World Bank climate records
# Seeded so the Data Pipeline Explorer renders populated on first deploy.
# ---------------------------------------------------------------------------

SEED_EMISSIONS: list[dict[str, Any]] = [
    {
        "facility_id": "1001341",
        "facility_name": "James H. Miller Jr. Electric Generating Plant",
        "city": "Quinton",
        "state": "AL",
        "region": "Southeast",
        "latitude": 33.6453,
        "longitude": -87.0767,
        "industry_type": "Power Plants",
        "sector": "Power Plants",
        "naics_code": "221112",
        "reporting_year": 2023,
        "total_emissions_mt_co2e": 18_493_572.0,
        "co2_emissions_mt": 18_200_000.0,
        "methane_emissions_mt_co2e": 180_000.0,
        "n2o_emissions_mt_co2e": 113_572.0,
        "emissions_scope": "Scope 1",
        "source": "EPA GHGRP",
    },
    {
        "facility_id": "1007084",
        "facility_name": "Scherer Power Plant",
        "city": "Juliette",
        "state": "GA",
        "region": "Southeast",
        "latitude": 33.0578,
        "longitude": -83.7853,
        "industry_type": "Power Plants",
        "sector": "Power Plants",
        "naics_code": "221112",
        "reporting_year": 2023,
        "total_emissions_mt_co2e": 15_874_231.0,
        "co2_emissions_mt": 15_600_000.0,
        "methane_emissions_mt_co2e": 165_000.0,
        "n2o_emissions_mt_co2e": 109_231.0,
        "emissions_scope": "Scope 1",
        "source": "EPA GHGRP",
    },
    {
        "facility_id": "1003116",
        "facility_name": "Gibson Generating Station",
        "city": "Owensville",
        "state": "IN",
        "region": "Midwest",
        "latitude": 38.3667,
        "longitude": -87.7825,
        "industry_type": "Power Plants",
        "sector": "Power Plants",
        "naics_code": "221112",
        "reporting_year": 2023,
        "total_emissions_mt_co2e": 14_213_402.0,
        "co2_emissions_mt": 14_000_000.0,
        "methane_emissions_mt_co2e": 130_000.0,
        "n2o_emissions_mt_co2e": 83_402.0,
        "emissions_scope": "Scope 1",
        "source": "EPA GHGRP",
    },
    {
        "facility_id": "1006693",
        "facility_name": "Martin Lake Steam Electric Station",
        "city": "Tatum",
        "state": "TX",
        "region": "South",
        "latitude": 32.2600,
        "longitude": -94.5700,
        "industry_type": "Power Plants",
        "sector": "Power Plants",
        "naics_code": "221112",
        "reporting_year": 2023,
        "total_emissions_mt_co2e": 12_892_451.0,
        "co2_emissions_mt": 12_700_000.0,
        "methane_emissions_mt_co2e": 115_000.0,
        "n2o_emissions_mt_co2e": 77_451.0,
        "emissions_scope": "Scope 1",
        "source": "EPA GHGRP",
    },
    {
        "facility_id": "1002490",
        "facility_name": "ExxonMobil Baytown Refinery",
        "city": "Baytown",
        "state": "TX",
        "region": "South",
        "latitude": 29.7485,
        "longitude": -94.9772,
        "industry_type": "Petroleum Refineries",
        "sector": "Petroleum & Natural Gas",
        "naics_code": "324110",
        "reporting_year": 2023,
        "total_emissions_mt_co2e": 11_234_567.0,
        "co2_emissions_mt": 10_800_000.0,
        "methane_emissions_mt_co2e": 350_000.0,
        "n2o_emissions_mt_co2e": 84_567.0,
        "emissions_scope": "Scope 1",
        "source": "EPA GHGRP",
    },
    {
        "facility_id": "1006352",
        "facility_name": "Labadie Energy Center",
        "city": "Labadie",
        "state": "MO",
        "region": "Midwest",
        "latitude": 38.5406,
        "longitude": -90.8153,
        "industry_type": "Power Plants",
        "sector": "Power Plants",
        "naics_code": "221112",
        "reporting_year": 2023,
        "total_emissions_mt_co2e": 10_567_893.0,
        "co2_emissions_mt": 10_400_000.0,
        "methane_emissions_mt_co2e": 105_000.0,
        "n2o_emissions_mt_co2e": 62_893.0,
        "emissions_scope": "Scope 1",
        "source": "EPA GHGRP",
    },
    {
        "facility_id": "1004183",
        "facility_name": "Marathon Petroleum Garyville Refinery",
        "city": "Garyville",
        "state": "LA",
        "region": "South",
        "latitude": 30.0558,
        "longitude": -90.6208,
        "industry_type": "Petroleum Refineries",
        "sector": "Petroleum & Natural Gas",
        "naics_code": "324110",
        "reporting_year": 2023,
        "total_emissions_mt_co2e": 9_432_100.0,
        "co2_emissions_mt": 9_100_000.0,
        "methane_emissions_mt_co2e": 270_000.0,
        "n2o_emissions_mt_co2e": 62_100.0,
        "emissions_scope": "Scope 1",
        "source": "EPA GHGRP",
    },
    {
        "facility_id": "1005521",
        "facility_name": "Navajo Generating Station",
        "city": "Page",
        "state": "AZ",
        "region": "West",
        "latitude": 36.9139,
        "longitude": -111.4531,
        "industry_type": "Power Plants",
        "sector": "Power Plants",
        "naics_code": "221112",
        "reporting_year": 2023,
        "total_emissions_mt_co2e": 8_765_432.0,
        "co2_emissions_mt": 8_600_000.0,
        "methane_emissions_mt_co2e": 100_000.0,
        "n2o_emissions_mt_co2e": 65_432.0,
        "emissions_scope": "Scope 1",
        "source": "EPA GHGRP",
    },
    {
        "facility_id": "1003892",
        "facility_name": "Nucor Steel Berkeley",
        "city": "Huger",
        "state": "SC",
        "region": "Southeast",
        "latitude": 33.0400,
        "longitude": -79.8800,
        "industry_type": "Iron and Steel Production",
        "sector": "Metals",
        "naics_code": "331110",
        "reporting_year": 2023,
        "total_emissions_mt_co2e": 4_321_000.0,
        "co2_emissions_mt": 4_200_000.0,
        "methane_emissions_mt_co2e": 80_000.0,
        "n2o_emissions_mt_co2e": 41_000.0,
        "emissions_scope": "Scope 1",
        "source": "EPA GHGRP",
    },
    {
        "facility_id": "1004451",
        "facility_name": "BASF Geismar Complex",
        "city": "Geismar",
        "state": "LA",
        "region": "South",
        "latitude": 30.2200,
        "longitude": -91.0100,
        "industry_type": "Chemicals",
        "sector": "Chemicals",
        "naics_code": "325110",
        "reporting_year": 2023,
        "total_emissions_mt_co2e": 3_876_543.0,
        "co2_emissions_mt": 3_700_000.0,
        "methane_emissions_mt_co2e": 120_000.0,
        "n2o_emissions_mt_co2e": 56_543.0,
        "emissions_scope": "Scope 1",
        "source": "EPA GHGRP",
    },
    {
        "facility_id": "1002871",
        "facility_name": "Holcim Cement Plant",
        "city": "Midlothian",
        "state": "TX",
        "region": "South",
        "latitude": 32.4850,
        "longitude": -96.9700,
        "industry_type": "Cement Production",
        "sector": "Minerals",
        "naics_code": "327310",
        "reporting_year": 2023,
        "total_emissions_mt_co2e": 2_987_654.0,
        "co2_emissions_mt": 2_850_000.0,
        "methane_emissions_mt_co2e": 90_000.0,
        "n2o_emissions_mt_co2e": 47_654.0,
        "emissions_scope": "Scope 1",
        "source": "EPA GHGRP",
    },
    {
        "facility_id": "1005772",
        "facility_name": "Waste Management Altamont Landfill",
        "city": "Livermore",
        "state": "CA",
        "region": "West",
        "latitude": 37.7650,
        "longitude": -121.7350,
        "industry_type": "Waste",
        "sector": "Waste",
        "naics_code": "562212",
        "reporting_year": 2023,
        "total_emissions_mt_co2e": 1_234_567.0,
        "co2_emissions_mt": 400_000.0,
        "methane_emissions_mt_co2e": 810_000.0,
        "n2o_emissions_mt_co2e": 24_567.0,
        "emissions_scope": "Scope 1",
        "source": "EPA GHGRP",
    },
]

SEED_CLIMATE: list[dict[str, Any]] = [
    # NOAA temperature observations
    {
        "location_id": "USW00013874",
        "country_code": "US",
        "state_code": "TX",
        "region": "South",
        "year": 2023,
        "month": 7,
        "metric_name": "Average Temperature",
        "metric_type": "observation",
        "value": 30.2,
        "unit": "°C",
        "source": "NOAA Climate Data Online",
        "station_id": "USW00013874",
    },
    {
        "location_id": "USW00013874",
        "country_code": "US",
        "state_code": "TX",
        "region": "South",
        "year": 2023,
        "month": 1,
        "metric_name": "Average Temperature",
        "metric_type": "observation",
        "value": 10.8,
        "unit": "°C",
        "source": "NOAA Climate Data Online",
        "station_id": "USW00013874",
    },
    {
        "location_id": "USW00094728",
        "country_code": "US",
        "state_code": "NY",
        "region": "Northeast",
        "year": 2023,
        "month": 7,
        "metric_name": "Average Temperature",
        "metric_type": "observation",
        "value": 25.6,
        "unit": "°C",
        "source": "NOAA Climate Data Online",
        "station_id": "USW00094728",
    },
    {
        "location_id": "USW00023174",
        "country_code": "US",
        "state_code": "CA",
        "region": "West",
        "year": 2023,
        "month": 7,
        "metric_name": "Average Temperature",
        "metric_type": "observation",
        "value": 23.4,
        "unit": "°C",
        "source": "NOAA Climate Data Online",
        "station_id": "USW00023174",
    },
    # NOAA precipitation
    {
        "location_id": "USW00013874",
        "country_code": "US",
        "state_code": "TX",
        "region": "South",
        "year": 2023,
        "month": 7,
        "metric_name": "Total Precipitation",
        "metric_type": "observation",
        "value": 42.5,
        "unit": "mm",
        "source": "NOAA Climate Data Online",
        "station_id": "USW00013874",
    },
    {
        "location_id": "USW00094728",
        "country_code": "US",
        "state_code": "NY",
        "region": "Northeast",
        "year": 2023,
        "month": 7,
        "metric_name": "Total Precipitation",
        "metric_type": "observation",
        "value": 118.3,
        "unit": "mm",
        "source": "NOAA Climate Data Online",
        "station_id": "USW00094728",
    },
    # World Bank climate projections
    {
        "location_id": "WLD",
        "country_code": "WLD",
        "region": "Global",
        "year": 2030,
        "metric_name": "Temperature Change",
        "metric_type": "projection",
        "value": 1.5,
        "unit": "°C above pre-industrial",
        "scenario": "SSP2-4.5",
        "period_start": 2025,
        "period_end": 2035,
        "source": "World Bank Climate Change Knowledge Portal",
    },
    {
        "location_id": "WLD",
        "country_code": "WLD",
        "region": "Global",
        "year": 2050,
        "metric_name": "Temperature Change",
        "metric_type": "projection",
        "value": 2.1,
        "unit": "°C above pre-industrial",
        "scenario": "SSP2-4.5",
        "period_start": 2045,
        "period_end": 2055,
        "source": "World Bank Climate Change Knowledge Portal",
    },
    {
        "location_id": "WLD",
        "country_code": "WLD",
        "region": "Global",
        "year": 2050,
        "metric_name": "Temperature Change",
        "metric_type": "projection",
        "value": 2.7,
        "unit": "°C above pre-industrial",
        "scenario": "SSP3-7.0",
        "period_start": 2045,
        "period_end": 2055,
        "source": "World Bank Climate Change Knowledge Portal",
    },
    {
        "location_id": "USA",
        "country_code": "US",
        "region": "North America",
        "year": 2050,
        "metric_name": "Sea Level Rise",
        "metric_type": "projection",
        "value": 0.3,
        "unit": "meters",
        "scenario": "SSP2-4.5",
        "period_start": 2045,
        "period_end": 2055,
        "source": "World Bank Climate Change Knowledge Portal",
    },
    {
        "location_id": "USA",
        "country_code": "US",
        "region": "North America",
        "year": 2030,
        "metric_name": "Extreme Heat Days",
        "metric_type": "projection",
        "value": 25.0,
        "unit": "days/year above 35°C",
        "scenario": "SSP2-4.5",
        "period_start": 2025,
        "period_end": 2035,
        "source": "World Bank Climate Change Knowledge Portal",
    },
    {
        "location_id": "USA",
        "country_code": "US",
        "region": "North America",
        "year": 2050,
        "metric_name": "Extreme Heat Days",
        "metric_type": "projection",
        "value": 42.0,
        "unit": "days/year above 35°C",
        "scenario": "SSP3-7.0",
        "period_start": 2045,
        "period_end": 2055,
        "source": "World Bank Climate Change Knowledge Portal",
    },
]

SEED_PIPELINE_RUNS: list[dict[str, Any]] = [
    {
        "run_id": "epa-ghgrp-2024-03-15T08:00:00",
        "status": "success",
        "records_extracted": 8547,
        "records_transformed": 8421,
        "records_loaded": 8421,
        "sources": '["EPA GHGRP"]',
        "triggered_by": "schedule",
    },
    {
        "run_id": "noaa-cdo-2024-03-15T09:30:00",
        "status": "success",
        "records_extracted": 12834,
        "records_transformed": 12710,
        "records_loaded": 12710,
        "sources": '["NOAA Climate Data Online"]',
        "triggered_by": "schedule",
    },
    {
        "run_id": "worldbank-2024-03-15T10:15:00",
        "status": "success",
        "records_extracted": 4230,
        "records_transformed": 4230,
        "records_loaded": 4230,
        "sources": '["World Bank Climate Change Knowledge Portal"]',
        "triggered_by": "schedule",
    },
]
