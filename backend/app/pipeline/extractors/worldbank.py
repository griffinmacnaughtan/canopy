"""World Bank Climate API extractor."""

from datetime import datetime
from typing import Any, Dict, List, Optional
import httpx

from .base import BaseExtractor, ExtractionResult
from ..config import PipelineConfig, CLIMATE_REGIONS


class WorldBankClimateExtractor(BaseExtractor):
    """
    Extract climate projection data from World Bank Climate API.

    Data includes:
    - Temperature projections by country/region
    - Precipitation projections
    - Climate model ensemble data (CMIP5/CMIP6)
    - Historical climate baselines

    Useful for:
    - Physical risk scenario modeling
    - Regional climate exposure analysis
    - Long-term transition planning

    API Docs: https://datahelpdesk.worldbank.org/knowledgebase/articles/902061-climate-data-api
    """

    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.base_url = config.worldbank_base_url

    @property
    def source_name(self) -> str:
        return "WORLDBANK_CLIMATE"

    async def health_check(self) -> bool:
        """Check World Bank Climate API availability."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/country/USA/mavg/tas/1980/2000"
                )
                return response.status_code == 200
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False

    async def extract(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        countries: Optional[List[str]] = None,
        variables: Optional[List[str]] = None,
        scenarios: Optional[List[str]] = None,
        **kwargs,
    ) -> ExtractionResult:
        """
        Extract climate projection data.

        Args:
            start_date: Projection start year
            end_date: Projection end year
            countries: ISO 3166-1 alpha-3 country codes
            variables: Climate variables (tas=temp, pr=precip)
            scenarios: RCP scenarios (rcp26, rcp45, rcp85)

        Returns:
            ExtractionResult with climate projections
        """
        # Defaults for climate risk analysis
        if not countries:
            # Major economies with significant portfolio exposure
            countries = ["USA", "GBR", "DEU", "CHN", "JPN", "AUS", "IND", "BRA"]

        if not variables:
            variables = ["tas", "pr"]  # Temperature and precipitation

        if not scenarios:
            scenarios = ["rcp45", "rcp85"]  # Moderate and high warming

        # Default time periods
        start_year = start_date.year if start_date else 2020
        end_year = end_date.year if end_date else 2100

        all_records = []
        errors = []

        async with httpx.AsyncClient(
            timeout=self.config.request_timeout_seconds
        ) as client:
            for country in countries:
                for variable in variables:
                    for scenario in scenarios:
                        try:
                            records = await self._fetch_projection(
                                client,
                                country=country,
                                variable=variable,
                                scenario=scenario,
                                start_year=start_year,
                                end_year=end_year,
                            )
                            all_records.extend(records)

                            self.logger.info(
                                "projection_extracted",
                                country=country,
                                variable=variable,
                                scenario=scenario,
                                record_count=len(records),
                            )

                        except Exception as e:
                            error_msg = f"Failed {country}/{variable}/{scenario}: {e}"
                            errors.append(error_msg)
                            self.logger.warning("projection_failed", error=error_msg)

        return ExtractionResult(
            source=self.source_name,
            records=all_records,
            watermark=f"{end_year}",
            metadata={
                "countries": countries,
                "variables": variables,
                "scenarios": scenarios,
                "time_range": f"{start_year}-{end_year}",
            },
            errors=errors,
        )

    async def _fetch_projection(
        self,
        client: httpx.AsyncClient,
        country: str,
        variable: str,
        scenario: str,
        start_year: int,
        end_year: int,
    ) -> List[Dict[str, Any]]:
        """Fetch climate projection for a specific combination."""
        records = []

        # World Bank API uses specific time periods
        time_periods = [
            (2020, 2039),
            (2040, 2059),
            (2060, 2079),
            (2080, 2099),
        ]

        for period_start, period_end in time_periods:
            if period_start < start_year or period_end > end_year:
                continue

            # Fetch annual projections
            url = f"{self.base_url}/country/annualavg/{scenario}/{variable}/{period_start}/{period_end}/{country}"

            try:
                response = await client.get(url)

                if response.status_code == 200:
                    data = response.json()

                    if isinstance(data, list):
                        for item in data:
                            record = {
                                "country": country,
                                "variable": variable,
                                "scenario": scenario,
                                "period_start": period_start,
                                "period_end": period_end,
                                "gcm": item.get("gcm"),  # Global Climate Model
                                "annual_mean": item.get("annualData", [None])[0] if item.get("annualData") else None,
                                "monthly_data": item.get("monthVals"),
                                "_source": self.source_name,
                                "_extracted_at": datetime.utcnow().isoformat(),
                            }
                            records.append(record)

            except Exception as e:
                self.logger.warning(
                    "period_fetch_failed",
                    country=country,
                    period=f"{period_start}-{period_end}",
                    error=str(e),
                )

        return records

    async def extract_historical_baseline(
        self,
        countries: Optional[List[str]] = None,
    ) -> ExtractionResult:
        """
        Extract historical climate baseline (1980-2000).

        Used as reference for calculating climate deltas.
        """
        if not countries:
            countries = ["USA", "GBR", "DEU", "CHN", "JPN", "AUS"]

        all_records = []
        errors = []

        async with httpx.AsyncClient(
            timeout=self.config.request_timeout_seconds
        ) as client:
            for country in countries:
                for variable in ["tas", "pr"]:
                    try:
                        url = f"{self.base_url}/country/mavg/{variable}/1980/2000/{country}"
                        response = await client.get(url)

                        if response.status_code == 200:
                            data = response.json()

                            if isinstance(data, list):
                                for item in data:
                                    record = {
                                        "country": country,
                                        "variable": variable,
                                        "period": "historical_baseline",
                                        "period_start": 1980,
                                        "period_end": 2000,
                                        "monthly_data": item.get("monthVals"),
                                        "_source": self.source_name,
                                        "_extracted_at": datetime.utcnow().isoformat(),
                                    }
                                    all_records.append(record)

                    except Exception as e:
                        errors.append(f"Failed {country}/{variable}: {e}")

        return ExtractionResult(
            source=self.source_name,
            records=all_records,
            metadata={"type": "historical_baseline", "period": "1980-2000"},
            errors=errors,
        )

    async def extract_temperature_anomalies(
        self,
        countries: Optional[List[str]] = None,
        scenario: str = "rcp85",
    ) -> ExtractionResult:
        """
        Calculate temperature anomalies (delta from baseline).

        Key metric for physical risk assessment.
        """
        baseline_result = await self.extract_historical_baseline(countries)
        projection_result = await self.extract(
            countries=countries,
            variables=["tas"],
            scenarios=[scenario],
        )

        # Calculate anomalies
        anomaly_records = []

        baseline_by_country = {}
        for record in baseline_result.records:
            if record["variable"] == "tas":
                country = record["country"]
                if country not in baseline_by_country:
                    baseline_by_country[country] = []
                baseline_by_country[country].append(record)

        for record in projection_result.records:
            country = record["country"]
            baseline_temps = baseline_by_country.get(country, [])

            if baseline_temps and record.get("annual_mean") is not None:
                # Average baseline temperature
                baseline_avg = sum(
                    sum(b.get("monthly_data", [0]) or [0]) / 12
                    for b in baseline_temps
                ) / len(baseline_temps)

                anomaly = record["annual_mean"] - baseline_avg

                anomaly_records.append({
                    "country": country,
                    "scenario": scenario,
                    "period_start": record["period_start"],
                    "period_end": record["period_end"],
                    "temperature_anomaly_c": round(anomaly, 2),
                    "baseline_temp_c": round(baseline_avg, 2),
                    "projected_temp_c": record["annual_mean"],
                    "_source": self.source_name,
                    "_extracted_at": datetime.utcnow().isoformat(),
                })

        return ExtractionResult(
            source=self.source_name,
            records=anomaly_records,
            metadata={"type": "temperature_anomalies", "scenario": scenario},
            errors=baseline_result.errors + projection_result.errors,
        )
