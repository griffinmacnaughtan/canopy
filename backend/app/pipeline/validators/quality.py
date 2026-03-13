"""Data quality validation and anomaly detection."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Set
import statistics
import structlog

logger = structlog.get_logger()


@dataclass
class QualityReport:
    """Comprehensive data quality report."""
    passed: bool
    total_records: int
    quality_score: float  # 0-100
    checks: Dict[str, "QualityCheckResult"]
    recommendations: List[str]
    timestamp: datetime = field(default_factory=datetime.utcnow)


@dataclass
class QualityCheckResult:
    """Result of a single quality check."""
    name: str
    passed: bool
    score: float  # 0-100
    details: str
    affected_records: int = 0
    affected_fields: List[str] = field(default_factory=list)


class DataQualityValidator:
    """
    Comprehensive data quality validation.

    Checks:
    - Completeness: Null/missing value rates
    - Uniqueness: Duplicate detection
    - Consistency: Value range and format
    - Timeliness: Data freshness
    - Anomalies: Statistical outlier detection
    """

    def __init__(
        self,
        max_null_rate: float = 0.1,
        max_duplicate_rate: float = 0.05,
        anomaly_threshold: float = 3.0,
    ):
        self.max_null_rate = max_null_rate
        self.max_duplicate_rate = max_duplicate_rate
        self.anomaly_threshold = anomaly_threshold
        self.logger = logger.bind(validator="quality")

    def validate(
        self,
        records: List[Dict[str, Any]],
        key_fields: Optional[List[str]] = None,
        numeric_fields: Optional[List[str]] = None,
        date_field: Optional[str] = None,
    ) -> QualityReport:
        """
        Run all quality checks on the data.

        Args:
            records: Data records to validate
            key_fields: Fields that should be unique (for duplicate check)
            numeric_fields: Fields to check for anomalies
            date_field: Field to check for timeliness

        Returns:
            QualityReport with all check results
        """
        if not records:
            return QualityReport(
                passed=False,
                total_records=0,
                quality_score=0,
                checks={},
                recommendations=["No data to validate"],
            )

        checks = {}

        # Completeness check
        checks["completeness"] = self._check_completeness(records)

        # Uniqueness check
        if key_fields:
            checks["uniqueness"] = self._check_uniqueness(records, key_fields)

        # Anomaly detection
        if numeric_fields:
            checks["anomalies"] = self._check_anomalies(records, numeric_fields)

        # Timeliness check
        if date_field:
            checks["timeliness"] = self._check_timeliness(records, date_field)

        # Value consistency
        checks["consistency"] = self._check_consistency(records)

        # Calculate overall score
        scores = [c.score for c in checks.values()]
        quality_score = sum(scores) / len(scores) if scores else 0

        # Determine pass/fail
        passed = all(c.passed for c in checks.values())

        # Generate recommendations
        recommendations = self._generate_recommendations(checks)

        self.logger.info(
            "quality_validation_complete",
            total_records=len(records),
            quality_score=quality_score,
            passed=passed,
        )

        return QualityReport(
            passed=passed,
            total_records=len(records),
            quality_score=quality_score,
            checks=checks,
            recommendations=recommendations,
        )

    def _check_completeness(self, records: List[Dict[str, Any]]) -> QualityCheckResult:
        """Check for null/missing values."""
        if not records:
            return QualityCheckResult(
                name="completeness",
                passed=False,
                score=0,
                details="No records to check",
            )

        # Collect all field names
        all_fields: Set[str] = set()
        for record in records:
            all_fields.update(record.keys())

        # Count nulls per field
        null_counts: Dict[str, int] = {field: 0 for field in all_fields}
        total_records = len(records)

        for record in records:
            for field_name in all_fields:
                value = record.get(field_name)
                if value is None or value == "" or value == []:
                    null_counts[field_name] += 1

        # Calculate null rates
        null_rates = {
            field: count / total_records
            for field, count in null_counts.items()
        }

        # Find problematic fields (excluding internal fields)
        problem_fields = [
            field for field, rate in null_rates.items()
            if rate > self.max_null_rate and not field.startswith("_")
        ]

        # Calculate completeness score
        avg_completeness = 1 - (sum(null_rates.values()) / len(null_rates))
        score = avg_completeness * 100

        passed = len(problem_fields) == 0

        details = f"Average completeness: {avg_completeness:.1%}"
        if problem_fields:
            details += f". High null rates in: {', '.join(problem_fields[:5])}"

        return QualityCheckResult(
            name="completeness",
            passed=passed,
            score=score,
            details=details,
            affected_fields=problem_fields,
        )

    def _check_uniqueness(
        self,
        records: List[Dict[str, Any]],
        key_fields: List[str],
    ) -> QualityCheckResult:
        """Check for duplicate records."""
        seen_keys: Set[tuple] = set()
        duplicates = 0

        for record in records:
            key = tuple(record.get(f) for f in key_fields)
            if key in seen_keys:
                duplicates += 1
            else:
                seen_keys.add(key)

        duplicate_rate = duplicates / len(records) if records else 0
        score = (1 - duplicate_rate) * 100
        passed = duplicate_rate <= self.max_duplicate_rate

        return QualityCheckResult(
            name="uniqueness",
            passed=passed,
            score=score,
            details=f"Found {duplicates} duplicate records ({duplicate_rate:.1%})",
            affected_records=duplicates,
            affected_fields=key_fields,
        )

    def _check_anomalies(
        self,
        records: List[Dict[str, Any]],
        numeric_fields: List[str],
    ) -> QualityCheckResult:
        """Detect statistical anomalies using z-score method."""
        anomaly_count = 0
        anomaly_details = []

        for field_name in numeric_fields:
            values = [
                r.get(field_name)
                for r in records
                if r.get(field_name) is not None
                and isinstance(r.get(field_name), (int, float))
            ]

            if len(values) < 10:  # Need enough data for statistics
                continue

            try:
                mean = statistics.mean(values)
                stdev = statistics.stdev(values)

                if stdev == 0:
                    continue

                # Count anomalies (values beyond threshold standard deviations)
                field_anomalies = sum(
                    1 for v in values
                    if abs((v - mean) / stdev) > self.anomaly_threshold
                )

                if field_anomalies > 0:
                    anomaly_count += field_anomalies
                    anomaly_details.append(f"{field_name}: {field_anomalies} outliers")

            except statistics.StatisticsError:
                continue

        anomaly_rate = anomaly_count / len(records) if records else 0
        score = (1 - min(anomaly_rate, 0.2) / 0.2) * 100  # Cap at 20% anomaly rate
        passed = anomaly_rate < 0.1  # Less than 10% anomalies

        details = f"Found {anomaly_count} anomalous values"
        if anomaly_details:
            details += f": {'; '.join(anomaly_details[:3])}"

        return QualityCheckResult(
            name="anomalies",
            passed=passed,
            score=score,
            details=details,
            affected_records=anomaly_count,
            affected_fields=numeric_fields,
        )

    def _check_timeliness(
        self,
        records: List[Dict[str, Any]],
        date_field: str,
    ) -> QualityCheckResult:
        """Check data freshness."""
        dates = []

        for record in records:
            date_value = record.get(date_field)
            if date_value:
                try:
                    if isinstance(date_value, str):
                        # Try common date formats
                        for fmt in ["%Y-%m-%d", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"]:
                            try:
                                dates.append(datetime.strptime(date_value[:19], fmt))
                                break
                            except ValueError:
                                continue
                    elif isinstance(date_value, datetime):
                        dates.append(date_value)
                except (ValueError, TypeError):
                    continue

        if not dates:
            return QualityCheckResult(
                name="timeliness",
                passed=True,
                score=100,
                details=f"No parseable dates found in '{date_field}'",
            )

        latest_date = max(dates)
        now = datetime.utcnow()
        age_days = (now - latest_date).days

        # Score based on data age (full score if < 1 day, 0 if > 30 days)
        score = max(0, 100 - (age_days / 30 * 100))
        passed = age_days <= 7  # Data should be less than a week old

        return QualityCheckResult(
            name="timeliness",
            passed=passed,
            score=score,
            details=f"Latest data is {age_days} days old (from {latest_date.date()})",
            affected_fields=[date_field],
        )

    def _check_consistency(self, records: List[Dict[str, Any]]) -> QualityCheckResult:
        """Check for value consistency (format, range)."""
        issues = []

        # Check for mixed types in fields
        field_types: Dict[str, Set[str]] = {}
        for record in records:
            for field, value in record.items():
                if value is not None:
                    type_name = type(value).__name__
                    if field not in field_types:
                        field_types[field] = set()
                    field_types[field].add(type_name)

        # Fields with mixed types (excluding internal fields)
        mixed_type_fields = [
            field for field, types in field_types.items()
            if len(types) > 1 and not field.startswith("_")
        ]

        if mixed_type_fields:
            issues.append(f"Mixed types in: {', '.join(mixed_type_fields[:3])}")

        # Check for negative values in typically positive fields
        positive_fields = ["emissions", "revenue", "count", "population"]
        for record in records:
            for field, value in record.items():
                if any(pf in field.lower() for pf in positive_fields):
                    if isinstance(value, (int, float)) and value < 0:
                        issues.append(f"Negative value in positive field: {field}")
                        break

        score = max(0, 100 - len(issues) * 10)
        passed = len(issues) == 0

        details = "Data is consistent" if passed else f"Issues: {'; '.join(issues[:3])}"

        return QualityCheckResult(
            name="consistency",
            passed=passed,
            score=score,
            details=details,
            affected_fields=mixed_type_fields,
        )

    def _generate_recommendations(
        self,
        checks: Dict[str, QualityCheckResult],
    ) -> List[str]:
        """Generate actionable recommendations based on check results."""
        recommendations = []

        for check_name, result in checks.items():
            if not result.passed:
                if check_name == "completeness":
                    recommendations.append(
                        f"Review data source for missing values in: {', '.join(result.affected_fields[:3])}"
                    )
                elif check_name == "uniqueness":
                    recommendations.append(
                        "Implement deduplication logic or verify key field definitions"
                    )
                elif check_name == "anomalies":
                    recommendations.append(
                        "Review outliers for data entry errors or genuine edge cases"
                    )
                elif check_name == "timeliness":
                    recommendations.append(
                        "Consider increasing data refresh frequency"
                    )
                elif check_name == "consistency":
                    recommendations.append(
                        "Standardize data types and add validation at extraction"
                    )

        if not recommendations:
            recommendations.append("Data quality is within acceptable thresholds")

        return recommendations
