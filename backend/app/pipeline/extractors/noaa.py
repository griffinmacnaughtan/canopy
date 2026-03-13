"""NOAA Climate Data Online API extractor."""

from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
import httpx

from .base import BaseExtractor, ExtractionResult
from ..config import PipelineConfig, NOAA_DATASETS


class NOAAExtractor(BaseExtractor):
    """
    Extract climate data from NOAA Climate Data Online API.

    Data includes:
    - Temperature records (daily/monthly summaries)
    - Precipitation data
    - Extreme weather events
    - Climate normals for risk modeling

    API Docs: https://www.ncdc.noaa.gov/cdo-web/webservices/v2
    """

    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.base_url = config.noaa_base_url
        self.token = config.noaa_api_token

    @property
    def source_name(self) -> str:
        return "NOAA_CDO"

    def _get_headers(self) -> Dict[str, str]:
        """Get request headers with API token."""
        return {"token": self.token}

    async def health_check(self) -> bool:
        """Check NOAA API availability."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                response = await client.get(
                    f"{self.base_url}/datasets",
                    headers=self._get_headers(),
                    params={"limit": 1},
                )
                return response.status_code == 200
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False

    async def extract(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        dataset_id: str = "GHCND",
        location_ids: Optional[List[str]] = None,
        data_types: Optional[List[str]] = None,
        **kwargs,
    ) -> ExtractionResult:
        """
        Extract climate observations from NOAA.

        Args:
            start_date: Start of date range
            end_date: End of date range
            dataset_id: NOAA dataset (GHCND, GSOM, etc.)
            location_ids: List of location IDs (FIPS codes)
            data_types: List of data types (TMAX, TMIN, PRCP, etc.)

        Returns:
            ExtractionResult with climate observations
        """
        # Default to last 30 days if no range specified
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            start_date = end_date - timedelta(days=30)

        # Default data types for climate risk analysis
        if not data_types:
            data_types = ["TMAX", "TMIN", "PRCP", "SNOW", "AWND"]

        # Default to major US cities if no locations specified
        if not location_ids:
            location_ids = [
                "FIPS:06",  # California
                "FIPS:48",  # Texas
                "FIPS:12",  # Florida
                "FIPS:36",  # New York
            ]

        all_records = []
        errors = []

        async with httpx.AsyncClient(
            timeout=self.config.request_timeout_seconds
        ) as client:
            for location_id in location_ids:
                try:
                    records = await self._fetch_data(
                        client,
                        dataset_id=dataset_id,
                        location_id=location_id,
                        start_date=start_date,
                        end_date=end_date,
                        data_types=data_types,
                    )
                    all_records.extend(records)

                    self.logger.info(
                        "location_extracted",
                        location=location_id,
                        record_count=len(records),
                    )

                except Exception as e:
                    error_msg = f"Failed to extract {location_id}: {e}"
                    errors.append(error_msg)
                    self.logger.warning("location_extraction_failed", error=error_msg)

        return ExtractionResult(
            source=self.source_name,
            records=all_records,
            watermark=end_date.isoformat(),
            metadata={
                "dataset_id": dataset_id,
                "location_count": len(location_ids),
                "date_range": f"{start_date.date()} to {end_date.date()}",
            },
            errors=errors,
        )

    async def _fetch_data(
        self,
        client: httpx.AsyncClient,
        dataset_id: str,
        location_id: str,
        start_date: datetime,
        end_date: datetime,
        data_types: List[str],
    ) -> List[Dict[str, Any]]:
        """Fetch data with pagination."""
        records = []
        offset = 0
        limit = 1000  # NOAA max per request

        while True:
            params = {
                "datasetid": dataset_id,
                "locationid": location_id,
                "startdate": start_date.strftime("%Y-%m-%d"),
                "enddate": end_date.strftime("%Y-%m-%d"),
                "datatypeid": ",".join(data_types),
                "limit": limit,
                "offset": offset,
                "units": "metric",
            }

            response = await client.get(
                f"{self.base_url}/data",
                headers=self._get_headers(),
                params=params,
            )

            if response.status_code == 200:
                data = response.json()
                results = data.get("results", [])

                if not results:
                    break

                # Enrich records with source metadata
                for record in results:
                    record["_source"] = self.source_name
                    record["_location_id"] = location_id
                    record["_extracted_at"] = datetime.utcnow().isoformat()

                records.extend(results)
                offset += limit

                # Check if we've got all records
                if len(results) < limit:
                    break

            elif response.status_code == 429:
                # Rate limited - let retry logic handle it
                raise Exception("Rate limited by NOAA API")
            else:
                raise Exception(f"NOAA API error: {response.status_code}")

        return records

    async def extract_extreme_events(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> ExtractionResult:
        """
        Extract extreme weather events for physical risk modeling.

        Focuses on:
        - Record high temperatures
        - Severe precipitation events
        - Storm events
        """
        # Use storm events dataset if available
        return await self.extract(
            start_date=start_date,
            end_date=end_date,
            dataset_id="GHCND",
            data_types=["TMAX", "PRCP", "SNOW", "AWND", "WSF2", "WSF5"],
        )
