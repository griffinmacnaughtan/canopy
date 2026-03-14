"""Emissions data transformers."""

from datetime import datetime
from typing import Any

from .base import BaseTransformer, TransformResult


class EmissionsDataTransformer(BaseTransformer):
    """
    Transform and enrich emissions data from EPA.

    Operations:
    - Unit standardization (all to metric tons CO2e)
    - Sector classification alignment with portfolio sectors
    - Intensity calculations (emissions per revenue proxy)
    - Geographic enrichment
    """

    @property
    def name(self) -> str:
        return "emissions_transformer"

    # EPA industry types to standard portfolio sectors
    INDUSTRY_TO_SECTOR = {
        "POWER PLANTS": "Utilities",
        "ELECTRICITY GENERATION": "Utilities",
        "PETROLEUM AND NATURAL GAS SYSTEMS": "Energy",
        "PETROLEUM REFINERIES": "Energy",
        "OIL AND GAS": "Energy",
        "CHEMICALS": "Materials",
        "CEMENT": "Materials",
        "IRON AND STEEL": "Materials",
        "PULP AND PAPER": "Materials",
        "METALS": "Materials",
        "MANUFACTURING": "Industrials",
        "FOOD PROCESSING": "Consumer Staples",
        "WASTE": "Industrials",
        "LANDFILLS": "Industrials",
    }

    # State to region mapping
    STATE_TO_REGION = {
        "CA": "West",
        "WA": "West",
        "OR": "West",
        "NV": "West",
        "AZ": "West",
        "TX": "South",
        "FL": "South",
        "GA": "South",
        "NC": "South",
        "LA": "South",
        "NY": "Northeast",
        "NJ": "Northeast",
        "PA": "Northeast",
        "MA": "Northeast",
        "IL": "Midwest",
        "OH": "Midwest",
        "MI": "Midwest",
        "IN": "Midwest",
    }

    def transform(self, records: list[dict[str, Any]]) -> TransformResult:
        """Transform emissions records."""
        input_count = len(records)
        transformed = []
        dropped = 0

        for record in records:
            table = record.get("_table", "")

            if table == "ghg_emitter_sector":
                result = self._transform_emitter_record(record)
            elif table == "ghg_emitter_facilities":
                result = self._transform_facility_record(record)
            else:
                result = self._transform_generic_record(record)

            if result:
                transformed.append(result)
            else:
                dropped += 1

        self.logger.info(
            "transformation_complete",
            input_count=input_count,
            output_count=len(transformed),
            dropped=dropped,
        )

        return TransformResult(
            records=transformed,
            source="emissions_data",
            input_count=input_count,
            dropped_count=dropped,
        )

    def _transform_emitter_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Transform EPA GHG emitter record."""
        facility_id = record.get("facility_id")
        if not facility_id:
            return None

        # Map industry to standard sector
        industry_type = self._normalize_string(record.get("industry_type", ""))
        sector = self._map_industry_to_sector(industry_type)

        # Get emissions (already in metric tons from EPA)
        total_emissions = self._safe_float(record.get("total_emissions_mt_co2e"))
        co2_emissions = self._safe_float(record.get("co2_emissions_mt"))
        methane_emissions = self._safe_float(record.get("methane_emissions_mt"))
        n2o_emissions = self._safe_float(record.get("n2o_emissions_mt"))

        # Get state and region
        state = self._normalize_string(record.get("state", ""))
        region = self.STATE_TO_REGION.get(state, "Other")

        # Calculate CO2e if not provided
        if total_emissions == 0 and (co2_emissions > 0 or methane_emissions > 0):
            # GWP factors (100-year): CH4=28, N2O=265
            total_emissions = co2_emissions + (methane_emissions * 28) + (n2o_emissions * 265)

        return {
            "facility_id": str(facility_id),
            "facility_name": self._normalize_string(record.get("facility_name")),
            "state": state,
            "city": self._normalize_string(record.get("city")),
            "region": region,
            "industry_type": industry_type,
            "sector": sector,
            "reporting_year": self._safe_int(record.get("reporting_year")),
            "total_emissions_mt_co2e": round(total_emissions, 2),
            "co2_emissions_mt": round(co2_emissions, 2),
            "methane_emissions_mt_co2e": round(methane_emissions * 28, 2),
            "n2o_emissions_mt_co2e": round(n2o_emissions * 265, 2),
            "emissions_scope": "scope_1",  # EPA GHGRP is direct emissions
            "source": "EPA_ENVIROFACTS",
            "transformed_at": datetime.utcnow().isoformat(),
        }

    def _transform_facility_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Transform EPA facility location record."""
        facility_id = record.get("facility_id")
        if not facility_id:
            return None

        # Parse and validate coordinates
        latitude = self._safe_float(record.get("latitude"))
        longitude = self._safe_float(record.get("longitude"))

        # Basic coordinate validation
        if not (-90 <= latitude <= 90) or not (-180 <= longitude <= 180):
            latitude = None
            longitude = None

        state = self._normalize_string(record.get("state", ""))

        return {
            "facility_id": str(facility_id),
            "facility_name": self._normalize_string(record.get("facility_name")),
            "address": self._normalize_string(record.get("address")),
            "city": self._normalize_string(record.get("city")),
            "state": state,
            "zip_code": self._normalize_string(record.get("zip")),
            "region": self.STATE_TO_REGION.get(state, "Other"),
            "latitude": latitude,
            "longitude": longitude,
            "naics_code": self._normalize_string(record.get("naics_code")),
            "source": "EPA_ENVIROFACTS",
            "record_type": "facility_location",
            "transformed_at": datetime.utcnow().isoformat(),
        }

    def _transform_generic_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Generic transformation for unknown emission records."""
        cleaned = {}
        for key, value in record.items():
            if key.startswith("_"):
                continue
            if isinstance(value, str):
                cleaned[key] = self._normalize_string(value)
            else:
                cleaned[key] = value

        cleaned["source"] = record.get("_source", "unknown")
        cleaned["transformed_at"] = datetime.utcnow().isoformat()

        return cleaned

    def _map_industry_to_sector(self, industry_type: str) -> str:
        """Map EPA industry type to standard sector."""
        industry_upper = industry_type.upper()

        for key, sector in self.INDUSTRY_TO_SECTOR.items():
            if key in industry_upper:
                return sector

        return "Other"

    def calculate_sector_aggregates(
        self,
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Aggregate emissions by sector and year.

        Useful for portfolio-level analysis.
        """
        from collections import defaultdict

        # Group by sector and year
        groups = defaultdict(lambda: {"total_emissions": 0, "facility_count": 0})

        for record in records:
            key = (record.get("sector"), record.get("reporting_year"))
            emissions = record.get("total_emissions_mt_co2e", 0) or 0
            groups[key]["total_emissions"] += emissions
            groups[key]["facility_count"] += 1

        # Build aggregated records
        aggregated = []
        for (sector, year), data in groups.items():
            if sector and year:
                aggregated.append(
                    {
                        "sector": sector,
                        "reporting_year": year,
                        "total_emissions_mt_co2e": round(data["total_emissions"], 2),
                        "facility_count": data["facility_count"],
                        "avg_emissions_per_facility": round(
                            data["total_emissions"] / data["facility_count"], 2
                        )
                        if data["facility_count"] > 0
                        else 0,
                        "aggregation": "sector_yearly",
                        "aggregated_at": datetime.utcnow().isoformat(),
                    }
                )

        return aggregated

    def enrich_with_intensity(
        self,
        records: list[dict[str, Any]],
        revenue_data: dict[str, float],
    ) -> list[dict[str, Any]]:
        """
        Calculate emissions intensity using revenue data.

        Args:
            records: Emissions records
            revenue_data: Dict mapping facility_id to revenue_usd_m

        Returns:
            Enriched records with intensity metrics
        """
        enriched = []

        for record in records:
            facility_id = record.get("facility_id")
            emissions = record.get("total_emissions_mt_co2e", 0) or 0
            revenue = revenue_data.get(facility_id, 0)

            record_copy = record.copy()

            if revenue > 0:
                record_copy["revenue_usd_m"] = revenue
                record_copy["emissions_intensity_tco2e_per_m"] = round(emissions / revenue, 4)
            else:
                record_copy["revenue_usd_m"] = None
                record_copy["emissions_intensity_tco2e_per_m"] = None

            enriched.append(record_copy)

        return enriched
