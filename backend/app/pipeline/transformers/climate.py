"""Climate data transformers."""

import statistics
from datetime import datetime
from typing import Any

from .base import BaseTransformer, TransformResult


class ClimateDataTransformer(BaseTransformer):
    """
    Transform and enrich climate data from NOAA and World Bank.

    Operations:
    - Unit normalization (all temps to Celsius, precip to mm)
    - Aggregation (daily -> monthly)
    - Anomaly calculation (deviation from baseline)
    - Region mapping for portfolio alignment
    """

    @property
    def name(self) -> str:
        return "climate_transformer"

    # NOAA data type mappings
    DATA_TYPE_UNITS = {
        "TMAX": ("temperature", "celsius", 0.1),  # Stored in tenths of degree
        "TMIN": ("temperature", "celsius", 0.1),
        "TAVG": ("temperature", "celsius", 0.1),
        "PRCP": ("precipitation", "mm", 0.1),
        "SNOW": ("snowfall", "mm", 1.0),
        "AWND": ("wind_speed", "mps", 0.1),
    }

    # US FIPS state codes to regions (for portfolio alignment)
    STATE_TO_REGION = {
        "06": "West",  # California
        "48": "South",  # Texas
        "12": "South",  # Florida
        "36": "Northeast",  # New York
        "17": "Midwest",  # Illinois
        "04": "West",  # Arizona
        "53": "West",  # Washington
    }

    def transform(self, records: list[dict[str, Any]]) -> TransformResult:
        """Transform climate records."""
        input_count = len(records)
        transformed = []
        dropped = 0

        for record in records:
            source = record.get("_source", "")

            if source == "NOAA_CDO":
                result = self._transform_noaa_record(record)
            elif source == "WORLDBANK_CLIMATE":
                result = self._transform_worldbank_record(record)
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
            source="climate_data",
            input_count=input_count,
            dropped_count=dropped,
        )

    def _transform_noaa_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Transform NOAA climate observation."""
        data_type = record.get("datatype")
        value = record.get("value")

        if data_type not in self.DATA_TYPE_UNITS or value is None:
            return None

        metric_name, unit, scale = self.DATA_TYPE_UNITS[data_type]

        # Convert to standard units
        scaled_value = self._safe_float(value) * scale

        # Parse date
        date_str = record.get("date", "")
        observation_date = self._parse_date(date_str)

        if not observation_date:
            return None

        # Extract location info
        location_id = record.get("_location_id", "")
        state_code = location_id.replace("FIPS:", "") if location_id.startswith("FIPS:") else ""
        region = self.STATE_TO_REGION.get(state_code, "Unknown")

        return {
            "observation_date": observation_date.isoformat(),
            "year": observation_date.year,
            "month": observation_date.month,
            "metric_name": metric_name,
            "metric_type": data_type,
            "value": round(scaled_value, 2),
            "unit": unit,
            "station_id": record.get("station"),
            "location_id": location_id,
            "state_code": state_code,
            "region": region,
            "source": "NOAA_CDO",
            "transformed_at": datetime.utcnow().isoformat(),
        }

    def _transform_worldbank_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Transform World Bank climate projection."""
        country = record.get("country")
        variable = record.get("variable")

        if not country or not variable:
            return None

        # Map variable to metric name
        variable_map = {
            "tas": ("temperature", "celsius"),
            "pr": ("precipitation", "mm"),
        }

        if variable not in variable_map:
            return None

        metric_name, unit = variable_map[variable]

        # Get projection value
        annual_mean = record.get("annual_mean")
        monthly_data = record.get("monthly_data", [])

        # Calculate annual average if only monthly data available
        if annual_mean is None and monthly_data:
            annual_mean = (
                statistics.mean(v for v in monthly_data if v is not None)
                if any(v is not None for v in monthly_data)
                else None
            )

        return {
            "country_code": country,
            "metric_name": metric_name,
            "variable": variable,
            "scenario": record.get("scenario"),
            "period_start": record.get("period_start"),
            "period_end": record.get("period_end"),
            "annual_mean": round(annual_mean, 2) if annual_mean else None,
            "monthly_values": monthly_data,
            "gcm_model": record.get("gcm"),
            "unit": unit,
            "source": "WORLDBANK_CLIMATE",
            "transformed_at": datetime.utcnow().isoformat(),
        }

    def _transform_generic_record(self, record: dict[str, Any]) -> dict[str, Any] | None:
        """Generic transformation for unknown sources."""
        # Pass through with basic cleanup
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

    def aggregate_monthly(
        self,
        records: list[dict[str, Any]],
    ) -> list[dict[str, Any]]:
        """
        Aggregate daily climate observations to monthly summaries.

        Groups by: location, year, month, metric
        Calculates: mean, min, max, count
        """
        from collections import defaultdict

        # Group records
        groups = defaultdict(list)

        for record in records:
            key = (
                record.get("location_id"),
                record.get("year"),
                record.get("month"),
                record.get("metric_name"),
            )
            value = record.get("value")
            if value is not None:
                groups[key].append(value)

        # Aggregate
        aggregated = []
        for (location_id, year, month, metric_name), values in groups.items():
            if not values:
                continue

            aggregated.append(
                {
                    "location_id": location_id,
                    "year": year,
                    "month": month,
                    "metric_name": metric_name,
                    "mean_value": round(statistics.mean(values), 2),
                    "min_value": round(min(values), 2),
                    "max_value": round(max(values), 2),
                    "observation_count": len(values),
                    "aggregation": "monthly",
                    "aggregated_at": datetime.utcnow().isoformat(),
                }
            )

        return aggregated
