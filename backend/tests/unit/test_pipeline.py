"""Tests for the data pipeline components."""

import pytest
from datetime import datetime

from app.pipeline.validators.schema import SchemaValidator, FieldSchema, FieldType, ValidationResult
from app.pipeline.validators.quality import DataQualityValidator
from app.pipeline.transformers.climate import ClimateDataTransformer
from app.pipeline.transformers.emissions import EmissionsDataTransformer
from app.pipeline.loaders.staging import StagingLoader


class TestSchemaValidator:
    """Tests for schema validation."""

    def test_valid_records(self):
        """Test validation of valid records."""
        schema = [
            FieldSchema("name", FieldType.STRING, required=True),
            FieldSchema("value", FieldType.FLOAT, required=True),
        ]
        validator = SchemaValidator(schema)

        records = [
            {"name": "test1", "value": 1.5},
            {"name": "test2", "value": 2.5},
        ]

        result = validator.validate(records)

        assert result.is_valid
        assert result.valid_count == 2
        assert result.invalid_count == 0

    def test_missing_required_field(self):
        """Test validation catches missing required fields."""
        schema = [
            FieldSchema("name", FieldType.STRING, required=True),
            FieldSchema("value", FieldType.FLOAT, required=True),
        ]
        validator = SchemaValidator(schema)

        records = [
            {"name": "test1"},  # Missing value
        ]

        result = validator.validate(records)

        assert not result.is_valid
        assert result.invalid_count == 1
        assert any("value" in error for error in result.errors)

    def test_type_validation(self):
        """Test type validation."""
        schema = [
            FieldSchema("count", FieldType.INTEGER, required=True),
        ]
        validator = SchemaValidator(schema)

        records = [
            {"count": "not_a_number"},
        ]

        result = validator.validate(records)

        assert not result.is_valid
        assert any("expected integer" in error for error in result.errors)

    def test_range_validation(self):
        """Test min/max value validation."""
        schema = [
            FieldSchema("year", FieldType.INTEGER, min_value=2000, max_value=2030),
        ]
        validator = SchemaValidator(schema)

        records = [
            {"year": 2025},  # Valid
            {"year": 1990},  # Below min
            {"year": 2050},  # Above max
        ]

        result = validator.validate(records)

        assert result.valid_count == 1
        assert result.invalid_count == 2


class TestDataQualityValidator:
    """Tests for data quality validation."""

    def test_completeness_check(self):
        """Test completeness validation."""
        validator = DataQualityValidator(max_null_rate=0.1)

        records = [
            {"name": "test1", "value": 1.0},
            {"name": "test2", "value": None},
            {"name": "test3", "value": 3.0},
            {"name": "test4", "value": 4.0},
        ]

        report = validator.validate(records)

        # 1 out of 4 is 25% null rate for 'value' field
        # But average completeness across all fields should be considered
        assert report.total_records == 4
        assert "completeness" in report.checks

    def test_uniqueness_check(self):
        """Test duplicate detection."""
        validator = DataQualityValidator(max_duplicate_rate=0.05)

        records = [
            {"id": "1", "name": "test1"},
            {"id": "1", "name": "test1"},  # Duplicate
            {"id": "2", "name": "test2"},
        ]

        report = validator.validate(records, key_fields=["id"])

        assert "uniqueness" in report.checks
        uniqueness = report.checks["uniqueness"]
        assert uniqueness.affected_records == 1

    def test_anomaly_detection(self):
        """Test statistical anomaly detection."""
        validator = DataQualityValidator(anomaly_threshold=2.0)

        # Normal values around 100, one outlier at 1000
        records = [
            {"value": 100},
            {"value": 102},
            {"value": 98},
            {"value": 101},
            {"value": 99},
            {"value": 100},
            {"value": 101},
            {"value": 99},
            {"value": 100},
            {"value": 1000},  # Anomaly
        ]

        report = validator.validate(records, numeric_fields=["value"])

        assert "anomalies" in report.checks


class TestClimateTransformer:
    """Tests for climate data transformation."""

    def test_noaa_transformation(self):
        """Test NOAA record transformation."""
        transformer = ClimateDataTransformer()

        records = [
            {
                "_source": "NOAA_CDO",
                "datatype": "TMAX",
                "value": 320,  # 32.0 degrees (stored in tenths)
                "date": "2024-01-15",
                "station": "GHCND:USW00014732",
                "_location_id": "FIPS:06",
            }
        ]

        result = transformer.transform(records)

        assert result.output_count == 1
        transformed = result.records[0]
        assert transformed["metric_name"] == "temperature"
        assert transformed["value"] == 32.0  # Scaled from tenths
        assert transformed["state_code"] == "06"
        assert transformed["region"] == "West"

    def test_worldbank_transformation(self):
        """Test World Bank record transformation."""
        transformer = ClimateDataTransformer()

        records = [
            {
                "_source": "WORLDBANK_CLIMATE",
                "country": "USA",
                "variable": "tas",
                "scenario": "rcp45",
                "annual_mean": 15.5,
            }
        ]

        result = transformer.transform(records)

        assert result.output_count == 1
        transformed = result.records[0]
        assert transformed["metric_name"] == "temperature"
        assert transformed["country_code"] == "USA"

    def test_dropped_records(self):
        """Test that invalid records are dropped."""
        transformer = ClimateDataTransformer()

        records = [
            {"_source": "NOAA_CDO", "datatype": "UNKNOWN"},  # Invalid datatype
            {"_source": "NOAA_CDO"},  # Missing datatype
        ]

        result = transformer.transform(records)

        assert result.dropped_count == 2


class TestEmissionsTransformer:
    """Tests for emissions data transformation."""

    def test_sector_mapping(self):
        """Test industry to sector mapping."""
        transformer = EmissionsDataTransformer()

        records = [
            {
                "_table": "ghg_emitter_sector",
                "facility_id": "123",
                "facility_name": "Test Power Plant",
                "industry_type": "POWER PLANTS",
                "state": "CA",
                "total_emissions_mt_co2e": 500000,
            }
        ]

        result = transformer.transform(records)

        assert result.output_count == 1
        transformed = result.records[0]
        assert transformed["sector"] == "Utilities"
        assert transformed["region"] == "West"

    def test_co2e_calculation(self):
        """Test GWP-weighted emissions calculation."""
        transformer = EmissionsDataTransformer()

        records = [
            {
                "_table": "ghg_emitter_sector",
                "facility_id": "456",
                "facility_name": "Test Gas Plant",
                "state": "TX",
                "total_emissions_mt_co2e": 0,  # Not provided
                "co2_emissions_mt": 100,
                "methane_emissions_mt": 10,
                "n2o_emissions_mt": 1,
            }
        ]

        result = transformer.transform(records)

        transformed = result.records[0]
        # CO2 + (CH4 * 28) + (N2O * 265) = 100 + 280 + 265 = 645
        assert transformed["total_emissions_mt_co2e"] == 645


class TestStagingLoader:
    """Tests for staging loader."""

    def test_load_records(self, tmp_path):
        """Test loading records to staging."""
        loader = StagingLoader(staging_dir=tmp_path / "staging")

        records = [
            {"id": "1", "value": 100},
            {"id": "2", "value": 200},
        ]

        result = loader.load(records, "test_source", "batch_001")

        assert result.success
        assert result.records_loaded == 2
        assert (tmp_path / "staging" / "test_source_batch_001.json").exists()

    def test_watermark_tracking(self, tmp_path):
        """Test watermark tracking for incremental loading."""
        loader = StagingLoader(staging_dir=tmp_path / "staging")

        records = [
            {"_extracted_at": "2024-01-15T10:00:00", "value": 1},
            {"_extracted_at": "2024-01-16T10:00:00", "value": 2},
        ]

        loader.load(records, "test_source")
        watermark = loader.get_watermark("test_source")

        assert watermark == "2024-01-16T10:00:00"

    def test_list_staged_batches(self, tmp_path):
        """Test listing staged batches."""
        loader = StagingLoader(staging_dir=tmp_path / "staging")

        loader.load([{"value": 1}], "source_a", "batch_001")
        loader.load([{"value": 2}], "source_b", "batch_002")

        batches = loader.get_staged_batches()
        assert len(batches) == 2

        # Filter by source
        batches_a = loader.get_staged_batches(source="source_a")
        assert len(batches_a) == 1
