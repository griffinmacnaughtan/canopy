"""Pipeline configuration."""

import os
from dataclasses import dataclass


@dataclass
class PipelineConfig:
    """Configuration for the data pipeline."""

    # NOAA Climate Data Online API
    # Register at: https://www.ncdc.noaa.gov/cdo-web/token
    noaa_api_token: str = ""
    noaa_base_url: str = "https://www.ncdc.noaa.gov/cdo-web/api/v2"

    # EPA Envirofacts API (no auth required)
    epa_base_url: str = "https://data.epa.gov/efservice"

    # World Bank CCKP API — CMIP6 climate projections (no auth required)
    # Old URL (deprecated/dead): http://climatedataapi.worldbank.org/climateweb/rest/v1
    worldbank_base_url: str = "https://cckpapi.worldbank.org/cckp/v1"

    # Database
    database_url: str = ""

    # Pipeline settings
    batch_size: int = 1000
    max_retries: int = 3
    retry_delay_seconds: int = 5
    request_timeout_seconds: int = 30

    # Data quality thresholds
    max_null_percentage: float = 0.1  # 10% max nulls
    anomaly_std_threshold: float = 3.0  # 3 sigma for anomaly detection

    # SEC EDGAR (no auth required, just User-Agent)
    sec_user_agent: str = "Canopy Climate Risk Platform research@canopy-demo.com"
    sec_efts_base_url: str = "https://efts.sec.gov/LATEST"
    sec_archives_base_url: str = "https://www.sec.gov/Archives/edgar/data"
    sec_rate_limit_seconds: float = 0.11  # SEC requires <=10 req/s

    @classmethod
    def from_env(cls) -> "PipelineConfig":
        """Load configuration from environment variables."""
        return cls(
            noaa_api_token=os.getenv("NOAA_API_TOKEN", ""),
            database_url=os.getenv("DATABASE_URL", ""),
            sec_user_agent=os.getenv(
                "SEC_USER_AGENT",
                "Canopy Climate Risk Platform research@canopy-demo.com",
            ),
        )


# Mapping of sectors to relevant EPA facility types
SECTOR_EPA_MAPPING = {
    "Energy": ["POWER PLANTS", "OIL AND GAS"],
    "Utilities": ["POWER PLANTS", "WATER UTILITIES"],
    "Materials": ["CEMENT", "STEEL", "CHEMICALS"],
    "Industrials": ["MANUFACTURING", "CONSTRUCTION"],
    "Real Estate": ["COMMERCIAL BUILDINGS"],
}

# NOAA dataset IDs for climate data
NOAA_DATASETS = {
    "daily_summaries": "GHCND",
    "global_summary": "GSOM",
    "climate_normals": "NORMAL_DLY",
}

# Regions for World Bank climate data
CLIMATE_REGIONS = {
    "North America": ["USA", "CAN", "MEX"],
    "Europe": ["GBR", "DEU", "FRA", "NLD"],
    "Asia Pacific": ["CHN", "JPN", "IND", "AUS"],
}
