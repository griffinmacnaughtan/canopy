"""EPA Envirofacts API extractor for emissions data."""

from datetime import datetime
from typing import Any

import httpx

from ..config import PipelineConfig
from .base import BaseExtractor, ExtractionResult


class EPAExtractor(BaseExtractor):
    """
    Extract emissions and environmental data from EPA Envirofacts.

    Data includes:
    - Greenhouse Gas Reporting Program (GHGRP) emissions
    - Facility-level emissions by sector
    - Air quality data
    - Toxic Release Inventory (TRI)

    API Docs: https://www.epa.gov/enviro/web-services
    """

    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.base_url = config.epa_base_url

    @property
    def source_name(self) -> str:
        return "EPA_ENVIROFACTS"

    async def health_check(self) -> bool:
        """Check EPA API availability."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                # Test with a simple query
                response = await client.get(f"{self.base_url}/ghg_emitter_sector/rows/0:1/json")
                return response.status_code == 200
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False

    async def extract(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        sectors: list[str] | None = None,
        states: list[str] | None = None,
        **kwargs,
    ) -> ExtractionResult:
        """
        Extract emissions data from EPA GHGRP.

        Args:
            start_date: Reporting year start
            end_date: Reporting year end
            sectors: Industry sectors to filter
            states: US state codes to filter

        Returns:
            ExtractionResult with facility emissions data
        """
        all_records = []
        errors = []

        # Extract from multiple EPA tables
        tables = [
            ("ghg_emitter_sector", self._extract_ghg_emitters),
            ("ghg_emitter_facilities", self._extract_facilities),
        ]

        async with httpx.AsyncClient(timeout=self.config.request_timeout_seconds) as client:
            for table_name, extract_fn in tables:
                try:
                    records = await extract_fn(
                        client,
                        start_date=start_date,
                        end_date=end_date,
                        sectors=sectors,
                        states=states,
                    )
                    all_records.extend(records)

                    self.logger.info(
                        "table_extracted",
                        table=table_name,
                        record_count=len(records),
                    )

                except Exception as e:
                    error_msg = f"Failed to extract {table_name}: {e}"
                    errors.append(error_msg)
                    self.logger.warning("table_extraction_failed", error=error_msg)

        # Determine watermark from data
        watermark = None
        if all_records:
            years = [r.get("reporting_year") for r in all_records if r.get("reporting_year")]
            if years:
                watermark = str(max(years))

        return ExtractionResult(
            source=self.source_name,
            records=all_records,
            watermark=watermark,
            metadata={
                "sectors": sectors or "all",
                "states": states or "all",
            },
            errors=errors,
        )

    async def _extract_ghg_emitters(
        self,
        client: httpx.AsyncClient,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        sectors: list[str] | None = None,
        states: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Extract GHG emitter data by sector."""
        records = []
        offset = 0
        batch_size = self.config.batch_size

        # Build year filter
        year_filter = ""
        if start_date and end_date:
            start_year = start_date.year
            end_year = end_date.year
            year_filter = f"/reporting_year/{start_year}:{end_year}"

        while True:
            url = f"{self.base_url}/ghg_emitter_sector{year_filter}/rows/{offset}:{offset + batch_size}/json"

            response = await client.get(url)

            if response.status_code != 200:
                raise Exception(f"EPA API error: {response.status_code}")

            data = response.json()

            if not data:
                break

            # Filter and enrich records
            for record in data:
                # Apply sector filter if specified
                if sectors:
                    record_sector = record.get("industry_type", "")
                    if not any(s.lower() in record_sector.lower() for s in sectors):
                        continue

                # Apply state filter if specified
                if states:
                    record_state = record.get("state", "")
                    if record_state not in states:
                        continue

                # Normalize field names
                normalized = {
                    "facility_id": record.get("facility_id"),
                    "facility_name": record.get("facility_name"),
                    "state": record.get("state"),
                    "city": record.get("city"),
                    "industry_type": record.get("industry_type"),
                    "reporting_year": record.get("reporting_year"),
                    "total_emissions_mt_co2e": self._parse_float(
                        record.get("total_reported_direct_emissions")
                    ),
                    "co2_emissions_mt": self._parse_float(record.get("co2_emissions")),
                    "methane_emissions_mt": self._parse_float(record.get("methane_emissions")),
                    "n2o_emissions_mt": self._parse_float(record.get("n2o_emissions")),
                    "_source": self.source_name,
                    "_table": "ghg_emitter_sector",
                    "_extracted_at": datetime.utcnow().isoformat(),
                }

                records.append(normalized)

            offset += batch_size

            # Safety limit
            if offset > 50000:
                self.logger.warning("extraction_limit_reached", offset=offset)
                break

        return records

    async def _extract_facilities(
        self,
        client: httpx.AsyncClient,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        sectors: list[str] | None = None,
        states: list[str] | None = None,
    ) -> list[dict[str, Any]]:
        """Extract facility-level details."""
        records = []
        offset = 0
        batch_size = self.config.batch_size

        while True:
            url = f"{self.base_url}/ghg_emitter_facilities/rows/{offset}:{offset + batch_size}/json"

            response = await client.get(url)

            if response.status_code != 200:
                raise Exception(f"EPA API error: {response.status_code}")

            data = response.json()

            if not data:
                break

            for record in data:
                # Apply filters
                if states and record.get("state") not in states:
                    continue

                normalized = {
                    "facility_id": record.get("facility_id"),
                    "facility_name": record.get("facility_name"),
                    "address": record.get("address"),
                    "city": record.get("city"),
                    "state": record.get("state"),
                    "zip": record.get("zip"),
                    "latitude": self._parse_float(record.get("latitude")),
                    "longitude": self._parse_float(record.get("longitude")),
                    "naics_code": record.get("primary_naics_code"),
                    "_source": self.source_name,
                    "_table": "ghg_emitter_facilities",
                    "_extracted_at": datetime.utcnow().isoformat(),
                }

                records.append(normalized)

            offset += batch_size

            # Safety limit
            if offset > 20000:
                break

        return records

    def _parse_float(self, value: Any) -> float | None:
        """Safely parse float values."""
        if value is None:
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    async def extract_by_sector(
        self,
        sector: str,
        states: list[str] | None = None,
    ) -> ExtractionResult:
        """
        Extract emissions data for a specific sector.

        Useful for sector-specific risk analysis.
        """
        return await self.extract(sectors=[sector], states=states)
