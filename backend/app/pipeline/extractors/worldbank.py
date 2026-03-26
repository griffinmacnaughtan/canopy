"""World Bank Climate Change Knowledge Portal (CCKP) API extractor.

Replaces the deprecated climatedataapi.worldbank.org with the current
CCKP v1 API backed by CMIP6 data.

API endpoint pattern (11 segments):
    {base}/cckp/v1/{collection}_{type}_{variable}_{product}_{aggregation}_{period}_{percentile}_{scenario}_{model}_{model_calc}_{statistic}/{geo_code}?_format=json

Example:
    https://cckpapi.worldbank.org/cckp/v1/cmip6-x0.25_climatology_tas_climatology_annual_2040-2059_median_ssp245_ensemble_all_mean/USA?_format=json

No authentication required.
"""

from datetime import datetime
from typing import Any

import httpx

from ..config import PipelineConfig
from .base import BaseExtractor, ExtractionResult

# New CCKP v1 API base
_CCKP_BASE = "https://cckpapi.worldbank.org/cckp/v1"

# CMIP6 SSP scenarios mapped from old RCP names
_SCENARIO_MAP = {
    "rcp26": "ssp126",
    "rcp45": "ssp245",
    "rcp85": "ssp585",
    "ssp126": "ssp126",
    "ssp245": "ssp245",
    "ssp370": "ssp370",
    "ssp585": "ssp585",
}

# Time periods available in CCKP
_PROJECTION_PERIODS = [
    ("2020-2039", 2020, 2039),
    ("2040-2059", 2040, 2059),
    ("2060-2079", 2060, 2079),
    ("2080-2099", 2080, 2099),
]

_HISTORICAL_PERIOD = "1995-2014"


class WorldBankClimateExtractor(BaseExtractor):
    """
    Extract climate projection data from World Bank CCKP API (CMIP6).

    Data includes:
    - Temperature projections by country (tas = near-surface air temperature)
    - Precipitation projections by country (pr = precipitation)
    - Historical baselines for anomaly calculation
    - Multiple SSP scenarios (SSP1-2.6, SSP2-4.5, SSP5-8.5)

    Useful for:
    - Physical risk scenario modelling
    - Regional climate exposure analysis
    - Long-term transition planning
    """

    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.base_url = _CCKP_BASE

    @property
    def source_name(self) -> str:
        return "WORLDBANK_CLIMATE"

    async def health_check(self) -> bool:
        """Check CCKP API availability."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                url = (
                    f"{self.base_url}/cmip6-x0.25_climatology_tas_climatology"
                    f"_annual_{_HISTORICAL_PERIOD}_median_historical_ensemble"
                    f"_all_mean/USA?_format=json"
                )
                response = await client.get(url)
                if response.status_code == 200:
                    data = response.json()
                    return data.get("metadata", {}).get("status") == "success"
                return False
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False

    async def extract(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        countries: list[str] | None = None,
        variables: list[str] | None = None,
        scenarios: list[str] | None = None,
        **kwargs,
    ) -> ExtractionResult:
        """
        Extract climate projection data from CCKP.

        Args:
            start_date: Not used (period-based API), kept for interface compat.
            end_date: Not used.
            countries: ISO 3166-1 alpha-3 country codes.
            variables: Climate variables (tas=temp, pr=precip).
            scenarios: SSP or RCP scenario names (auto-mapped to SSP).

        Returns:
            ExtractionResult with climate projections.
        """
        if not countries:
            countries = ["USA", "GBR", "DEU", "CHN", "JPN", "AUS", "IND", "BRA"]

        if not variables:
            variables = ["tas", "pr"]

        if not scenarios:
            scenarios = ["ssp245", "ssp585"]

        # Map any old RCP names to SSP
        mapped_scenarios = [_SCENARIO_MAP.get(s, s) for s in scenarios]

        all_records: list[dict[str, Any]] = []
        errors: list[str] = []

        async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
            # Fetch historical baseline
            for country in countries:
                for variable in variables:
                    try:
                        baseline = await self._fetch_cckp(
                            client,
                            country=country,
                            variable=variable,
                            period=_HISTORICAL_PERIOD,
                            scenario="historical",
                        )
                        if baseline is not None:
                            all_records.append({
                                "country": country,
                                "variable": variable,
                                "scenario": "historical",
                                "period": _HISTORICAL_PERIOD,
                                "period_start": 1995,
                                "period_end": 2014,
                                "annual_mean": baseline,
                                "_source": self.source_name,
                                "_extracted_at": datetime.utcnow().isoformat(),
                            })
                    except Exception as e:
                        errors.append(f"Baseline {country}/{variable}: {e}")

            # Fetch projections
            for country in countries:
                for variable in variables:
                    for scenario in mapped_scenarios:
                        for period_str, p_start, p_end in _PROJECTION_PERIODS:
                            try:
                                value = await self._fetch_cckp(
                                    client,
                                    country=country,
                                    variable=variable,
                                    period=period_str,
                                    scenario=scenario,
                                )
                                if value is not None:
                                    all_records.append({
                                        "country": country,
                                        "variable": variable,
                                        "scenario": scenario,
                                        "period": period_str,
                                        "period_start": p_start,
                                        "period_end": p_end,
                                        "annual_mean": value,
                                        "_source": self.source_name,
                                        "_extracted_at": datetime.utcnow().isoformat(),
                                    })

                                    self.logger.info(
                                        "projection_extracted",
                                        country=country,
                                        variable=variable,
                                        scenario=scenario,
                                        period=period_str,
                                        value=value,
                                    )
                            except Exception as e:
                                msg = f"{country}/{variable}/{scenario}/{period_str}: {e}"
                                errors.append(msg)
                                self.logger.warning("projection_failed", error=msg)

        return ExtractionResult(
            source=self.source_name,
            records=all_records,
            watermark="2099",
            metadata={
                "countries": countries,
                "variables": variables,
                "scenarios": mapped_scenarios,
                "api": "CCKP v1 (CMIP6)",
            },
            errors=errors,
        )

    async def _fetch_cckp(
        self,
        client: httpx.AsyncClient,
        country: str,
        variable: str,
        period: str,
        scenario: str,
    ) -> float | None:
        """Fetch a single data point from the CCKP API.

        URL pattern:
            /cmip6-x0.25_climatology_{var}_climatology_annual_{period}_median_{scenario}_ensemble_all_mean/{country}?_format=json

        Returns the annual mean value, or None if not available.
        """
        url = (
            f"{self.base_url}/cmip6-x0.25_climatology_{variable}_climatology"
            f"_annual_{period}_median_{scenario}_ensemble_all_mean"
            f"/{country}?_format=json"
        )

        response = await client.get(url)

        if response.status_code != 200:
            return None

        data = response.json()
        meta = data.get("metadata", {})
        if meta.get("status") != "success":
            return None

        country_data = data.get("data", {}).get(country, {})
        if not country_data:
            return None

        # The API returns {period-month: value} — extract the single value
        values = list(country_data.values())
        if values:
            try:
                return round(float(values[0]), 2)
            except (ValueError, TypeError):
                return None

        return None

    async def extract_historical_baseline(
        self,
        countries: list[str] | None = None,
    ) -> ExtractionResult:
        """
        Extract historical climate baseline (1995-2014, CMIP6 reference period).

        Used as reference for calculating climate anomalies/deltas.
        """
        return await self.extract(
            countries=countries,
            variables=["tas", "pr"],
            scenarios=["historical"],
        )

    async def extract_temperature_anomalies(
        self,
        countries: list[str] | None = None,
        scenario: str = "ssp585",
    ) -> ExtractionResult:
        """
        Calculate temperature anomalies (delta from 1995-2014 baseline).

        Key metric for physical risk assessment.
        """
        full_result = await self.extract(
            countries=countries,
            variables=["tas"],
            scenarios=[scenario],
        )

        # Separate baselines from projections
        baselines: dict[str, float] = {}
        projections: list[dict[str, Any]] = []

        for record in full_result.records:
            if record["scenario"] == "historical":
                baselines[record["country"]] = record["annual_mean"]
            else:
                projections.append(record)

        # Calculate anomalies
        anomaly_records = []
        for record in projections:
            country = record["country"]
            baseline_temp = baselines.get(country)
            if baseline_temp is not None and record.get("annual_mean") is not None:
                anomaly = record["annual_mean"] - baseline_temp
                anomaly_records.append({
                    "country": country,
                    "scenario": scenario,
                    "period_start": record["period_start"],
                    "period_end": record["period_end"],
                    "temperature_anomaly_c": round(anomaly, 2),
                    "baseline_temp_c": baseline_temp,
                    "projected_temp_c": record["annual_mean"],
                    "_source": self.source_name,
                    "_extracted_at": datetime.utcnow().isoformat(),
                })

        return ExtractionResult(
            source=self.source_name,
            records=anomaly_records,
            metadata={"type": "temperature_anomalies", "scenario": scenario},
            errors=full_result.errors,
        )
