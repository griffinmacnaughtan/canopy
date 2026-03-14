"""Schema validation for extracted data."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import structlog

logger = structlog.get_logger()


class FieldType(Enum):
    """Supported field types for validation."""

    STRING = "string"
    INTEGER = "integer"
    FLOAT = "float"
    BOOLEAN = "boolean"
    DATETIME = "datetime"
    LIST = "list"
    DICT = "dict"
    ANY = "any"


@dataclass
class FieldSchema:
    """Schema definition for a single field."""

    name: str
    field_type: FieldType
    required: bool = True
    nullable: bool = True
    min_value: float | None = None
    max_value: float | None = None
    allowed_values: set[Any] | None = None
    pattern: str | None = None


@dataclass
class ValidationResult:
    """Result of schema validation."""

    is_valid: bool
    valid_records: list[dict[str, Any]]
    invalid_records: list[dict[str, Any]]
    errors: list[str]
    warnings: list[str] = field(default_factory=list)
    stats: dict[str, Any] = field(default_factory=dict)

    @property
    def valid_count(self) -> int:
        return len(self.valid_records)

    @property
    def invalid_count(self) -> int:
        return len(self.invalid_records)

    @property
    def total_count(self) -> int:
        return self.valid_count + self.invalid_count

    @property
    def validity_rate(self) -> float:
        if self.total_count == 0:
            return 1.0
        return self.valid_count / self.total_count


# Predefined schemas for different data sources
NOAA_SCHEMA = [
    FieldSchema("date", FieldType.STRING, required=True),
    FieldSchema("datatype", FieldType.STRING, required=True),
    FieldSchema("value", FieldType.FLOAT, required=True),
    FieldSchema("station", FieldType.STRING, required=False),
    FieldSchema("_source", FieldType.STRING, required=True),
    FieldSchema("_extracted_at", FieldType.STRING, required=True),
]

EPA_EMISSIONS_SCHEMA = [
    FieldSchema("facility_id", FieldType.STRING, required=True),
    FieldSchema("facility_name", FieldType.STRING, required=True),
    FieldSchema("state", FieldType.STRING, required=True),
    FieldSchema(
        "reporting_year", FieldType.INTEGER, required=False, min_value=1990, max_value=2030
    ),
    FieldSchema("total_emissions_mt_co2e", FieldType.FLOAT, required=False, min_value=0),
    FieldSchema("_source", FieldType.STRING, required=True),
    FieldSchema("_extracted_at", FieldType.STRING, required=True),
]

WORLDBANK_CLIMATE_SCHEMA = [
    FieldSchema("country", FieldType.STRING, required=True),
    FieldSchema("variable", FieldType.STRING, required=True, allowed_values={"tas", "pr"}),
    FieldSchema("scenario", FieldType.STRING, required=False),
    FieldSchema("period_start", FieldType.INTEGER, required=False),
    FieldSchema("period_end", FieldType.INTEGER, required=False),
    FieldSchema("_source", FieldType.STRING, required=True),
    FieldSchema("_extracted_at", FieldType.STRING, required=True),
]


class SchemaValidator:
    """
    Validate extracted data against predefined schemas.

    Supports:
    - Type checking
    - Required field validation
    - Range validation (min/max)
    - Allowed values (enum-like)
    - Null handling
    """

    def __init__(self, schema: list[FieldSchema]):
        self.schema = {field.name: field for field in schema}
        self.logger = logger.bind(validator="schema")

    def validate(self, records: list[dict[str, Any]]) -> ValidationResult:
        """
        Validate a list of records against the schema.

        Args:
            records: List of data records to validate

        Returns:
            ValidationResult with valid/invalid records and error details
        """
        valid_records = []
        invalid_records = []
        all_errors = []
        warnings = []
        field_error_counts: dict[str, int] = {}

        for i, record in enumerate(records):
            record_errors = self._validate_record(record, i)

            if record_errors:
                invalid_records.append(record)
                all_errors.extend(record_errors)

                # Track which fields have errors
                for error in record_errors:
                    field_name = error.split("'")[1] if "'" in error else "unknown"
                    field_error_counts[field_name] = field_error_counts.get(field_name, 0) + 1
            else:
                valid_records.append(record)

        # Generate warnings for frequently problematic fields
        for field_name, count in field_error_counts.items():
            if count > len(records) * 0.1:  # More than 10% errors
                warnings.append(
                    f"Field '{field_name}' has errors in {count}/{len(records)} records ({count / len(records) * 100:.1f}%)"
                )

        is_valid = len(invalid_records) == 0

        self.logger.info(
            "validation_complete",
            total=len(records),
            valid=len(valid_records),
            invalid=len(invalid_records),
        )

        return ValidationResult(
            is_valid=is_valid,
            valid_records=valid_records,
            invalid_records=invalid_records,
            errors=all_errors[:100],  # Limit error messages
            warnings=warnings,
            stats={
                "total_records": len(records),
                "valid_records": len(valid_records),
                "invalid_records": len(invalid_records),
                "validity_rate": len(valid_records) / len(records) if records else 1.0,
                "field_error_counts": field_error_counts,
            },
        )

    def _validate_record(self, record: dict[str, Any], index: int) -> list[str]:
        """Validate a single record."""
        errors = []

        # Check required fields
        for field_name, field_schema in self.schema.items():
            if field_schema.required and field_name not in record:
                errors.append(f"Record {index}: Missing required field '{field_name}'")
                continue

            if field_name not in record:
                continue

            value = record[field_name]

            # Check nullable
            if value is None:
                if not field_schema.nullable:
                    errors.append(f"Record {index}: Field '{field_name}' cannot be null")
                continue

            # Type validation
            type_error = self._validate_type(value, field_schema, index)
            if type_error:
                errors.append(type_error)
                continue

            # Range validation
            if field_schema.min_value is not None and isinstance(value, (int, float)) and value < field_schema.min_value:
                errors.append(
                    f"Record {index}: Field '{field_name}' value {value} below minimum {field_schema.min_value}"
                )

            if field_schema.max_value is not None and isinstance(value, (int, float)) and value > field_schema.max_value:
                errors.append(
                    f"Record {index}: Field '{field_name}' value {value} above maximum {field_schema.max_value}"
                )

            # Allowed values validation
            if field_schema.allowed_values is not None and value not in field_schema.allowed_values:
                errors.append(
                        f"Record {index}: Field '{field_name}' value '{value}' not in allowed values"
                    )

        return errors

    def _validate_type(
        self,
        value: Any,
        field_schema: FieldSchema,
        index: int,
    ) -> str | None:
        """Validate field type."""
        expected = field_schema.field_type
        field_name = field_schema.name

        if expected == FieldType.ANY:
            return None

        type_map = {
            FieldType.STRING: str,
            FieldType.INTEGER: int,
            FieldType.FLOAT: (int, float),
            FieldType.BOOLEAN: bool,
            FieldType.LIST: list,
            FieldType.DICT: dict,
        }

        expected_type = type_map.get(expected)
        if expected_type and not isinstance(value, expected_type):
            return (
                f"Record {index}: Field '{field_name}' expected {expected.value}, "
                f"got {type(value).__name__}"
            )

        return None

    @classmethod
    def for_source(cls, source: str) -> "SchemaValidator":
        """Get validator for a specific data source."""
        schemas = {
            "NOAA_CDO": NOAA_SCHEMA,
            "EPA_ENVIROFACTS": EPA_EMISSIONS_SCHEMA,
            "WORLDBANK_CLIMATE": WORLDBANK_CLIMATE_SCHEMA,
        }

        schema = schemas.get(source, [])
        return cls(schema)
