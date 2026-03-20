"""Tests for ground-truth evaluation dataset and FactualAccuracyScorer.

Validates that:
1. Eval cases are correctly computed from seed data (not hardcoded)
2. The FactualAccuracyScorer correctly identifies numeric matches/misses
3. Entity recall scoring works as expected
4. The combined scoring weights are applied correctly
"""

from __future__ import annotations

import pytest

from app.benchmarks import SECTOR_BENCHMARKS
from app.database.seed import REAL_ASSETS, SAMPLE_PORTFOLIOS
from evals.datasets.domain_accuracy import (
    DOMAIN_ACCURACY_CASES,
    ENERGY_CONTEXT,
    GLOBAL_CONTEXT,
    TECH_CONTEXT,
    _assets_for_portfolio,
    _emissions_intensity,
    _pydantic_assets,
)
from evals.framework import EvalCase
from evals.scorers import FactualAccuracyScorer

# ── Dataset Integrity ────────────────────────────────────────────────────


class TestDatasetIntegrity:
    """Verify dataset structure and completeness."""

    def test_has_15_cases(self):
        assert len(DOMAIN_ACCURACY_CASES) == 15

    def test_all_ids_unique(self):
        ids = [c.id for c in DOMAIN_ACCURACY_CASES]
        assert len(ids) == len(set(ids)), f"Duplicate IDs: {ids}"

    def test_all_cases_are_domain_accuracy_category(self):
        for case in DOMAIN_ACCURACY_CASES:
            assert case.category == "domain_accuracy"

    def test_all_cases_have_ground_truth(self):
        """Every domain accuracy case should have expected_values or expected_entities."""
        for case in DOMAIN_ACCURACY_CASES:
            has_values = bool(case.expected_values)
            has_entities = bool(case.expected_entities)
            assert has_values or has_entities, (
                f"Case {case.id} has neither expected_values nor expected_entities"
            )

    def test_all_cases_have_criteria(self):
        for case in DOMAIN_ACCURACY_CASES:
            assert case.criteria, f"Case {case.id} has empty criteria"

    def test_all_cases_are_evalcase_instances(self):
        for case in DOMAIN_ACCURACY_CASES:
            assert isinstance(case, EvalCase)

    def test_pass_thresholds_reasonable(self):
        for case in DOMAIN_ACCURACY_CASES:
            assert 2.0 <= case.pass_threshold <= 4.0, (
                f"Case {case.id} threshold {case.pass_threshold} seems extreme"
            )


# ── Ground Truth Computation ─────────────────────────────────────────────


class TestGroundTruthComputation:
    """Verify that expected values match what we'd compute from seed data."""

    def test_apple_scope1_matches_seed(self):
        apple = next(a for a in REAL_ASSETS if a["ticker"] == "AAPL")
        case = next(c for c in DOMAIN_ACCURACY_CASES if c.id == "domain_001")
        assert case.expected_values["apple_scope1"] == apple["scope1_tco2e"]

    def test_exxon_total_emissions_computed(self):
        exxon = next(a for a in REAL_ASSETS if a["ticker"] == "XOM")
        case = next(c for c in DOMAIN_ACCURACY_CASES if c.id == "domain_002")
        expected_total = exxon["scope1_tco2e"] + exxon["scope2_tco2e"]
        assert case.expected_values["exxon_total"] == expected_total

    def test_nextera_green_pct_matches_seed(self):
        nextera = next(a for a in REAL_ASSETS if a["ticker"] == "NEE")
        case = next(c for c in DOMAIN_ACCURACY_CASES if c.id == "domain_003")
        assert case.expected_values["nextera_green_pct"] == nextera["green_revenue_pct"]

    def test_tech_avg_intensity_computed_correctly(self):
        tech_assets = _assets_for_portfolio("Tech Leaders")
        manual_avg = sum(_emissions_intensity(a) for a in tech_assets) / len(tech_assets)
        case = next(c for c in DOMAIN_ACCURACY_CASES if c.id == "domain_004")
        assert abs(case.expected_values["avg_intensity"] - round(manual_avg, 2)) < 0.01

    def test_energy_benchmark_from_sector_benchmarks(self):
        case = next(c for c in DOMAIN_ACCURACY_CASES if c.id == "domain_012")
        expected_bm = SECTOR_BENCHMARKS["Energy"]["emissions_intensity_benchmark_tco2e_per_m"]
        assert case.expected_values["energy_benchmark"] == expected_bm

    def test_apple_scope2_is_zero(self):
        """Apple's reported Scope 2 is 0 (100% renewable electricity)."""
        case = next(c for c in DOMAIN_ACCURACY_CASES if c.id == "domain_014")
        assert case.expected_values["apple_scope2"] == 0


# ── Portfolio Context Builders ───────────────────────────────────────────


class TestPortfolioContexts:
    """Verify context strings are well-formed and contain expected data."""

    def test_tech_context_has_portfolio_header(self):
        assert "## Portfolio: Tech Leaders" in TECH_CONTEXT

    def test_energy_context_has_scores(self):
        assert "Overall Score:" in ENERGY_CONTEXT
        assert "Climate Risk:" in ENERGY_CONTEXT
        assert "Transition Risk:" in ENERGY_CONTEXT

    def test_global_context_has_holdings_table(self):
        assert "| Asset |" in GLOBAL_CONTEXT
        assert "Sector" in GLOBAL_CONTEXT

    def test_contexts_reference_real_companies(self):
        assert "Apple" in TECH_CONTEXT
        assert "Shell" in ENERGY_CONTEXT

    def test_portfolio_helper_finds_correct_assets(self):
        tech_assets = _assets_for_portfolio("Tech Leaders")
        tech_names = {a["name"] for a in tech_assets}
        portfolio = next(p for p in SAMPLE_PORTFOLIOS if p["name"] == "Tech Leaders")
        assert tech_names == set(portfolio["asset_names"])

    def test_pydantic_asset_conversion(self):
        raw = _assets_for_portfolio("Tech Leaders")
        pydantic = _pydantic_assets(raw)
        assert len(pydantic) == len(raw)
        for asset in pydantic:
            assert asset.name
            assert asset.sector


# ── FactualAccuracyScorer ────────────────────────────────────────────────


class TestFactualAccuracyScorer:
    """Unit tests for the ground-truth scoring engine."""

    @pytest.fixture()
    def scorer(self) -> FactualAccuracyScorer:
        return FactualAccuracyScorer(tolerance=0.10)

    @pytest.mark.asyncio()
    async def test_perfect_numeric_match(self, scorer: FactualAccuracyScorer):
        scores, reasoning = await scorer.score_with_ground_truth(
            prompt="What is the value?",
            response="The value is 55,200 tCO2e.",
            criteria={"factuality": "Must match"},
            max_score=5,
            expected_values={"value": 55200},
        )
        assert scores["factuality"] == 5.0
        assert "1/1 values found" in reasoning

    @pytest.mark.asyncio()
    async def test_within_tolerance(self, scorer: FactualAccuracyScorer):
        """A response with 54,000 should match expected 55,200 within 10%."""
        scores, _ = await scorer.score_with_ground_truth(
            prompt="test",
            response="Approximately 54,000 tCO2e",
            criteria={"factuality": "Must match"},
            max_score=5,
            expected_values={"value": 55200},
        )
        assert scores["factuality"] == 5.0

    @pytest.mark.asyncio()
    async def test_outside_tolerance(self, scorer: FactualAccuracyScorer):
        """A response with 40,000 should NOT match expected 55,200."""
        scores, reasoning = await scorer.score_with_ground_truth(
            prompt="test",
            response="About 40,000 tCO2e",
            criteria={"factuality": "Must match"},
            max_score=5,
            expected_values={"value": 55200},
        )
        assert scores["factuality"] < 5.0
        assert "Missing" in reasoning

    @pytest.mark.asyncio()
    async def test_entity_recall_all_found(self, scorer: FactualAccuracyScorer):
        scores, reasoning = await scorer.score_with_ground_truth(
            prompt="test",
            response="Apple and Microsoft are both tech companies.",
            criteria={"factuality": "Entities"},
            max_score=5,
            expected_entities=["Apple", "Microsoft"],
        )
        assert scores["factuality"] == 5.0
        assert "2/2" in reasoning

    @pytest.mark.asyncio()
    async def test_entity_recall_partial(self, scorer: FactualAccuracyScorer):
        scores, reasoning = await scorer.score_with_ground_truth(
            prompt="test",
            response="Apple is a tech company.",
            criteria={"factuality": "Entities"},
            max_score=5,
            expected_entities=["Apple", "Microsoft"],
        )
        assert scores["factuality"] < 5.0
        assert "1/2" in reasoning
        assert "Microsoft" in reasoning

    @pytest.mark.asyncio()
    async def test_combined_scoring_weights(self, scorer: FactualAccuracyScorer):
        """60% numeric + 40% entity recall."""
        # Perfect numeric, zero entity recall
        scores, _ = await scorer.score_with_ground_truth(
            prompt="test",
            response="The value is 100.",
            criteria={"factuality": "Combined"},
            max_score=5,
            expected_values={"val": 100},
            expected_entities=["NonexistentCompany"],
        )
        # 5.0 * 0.6 + 0.0 * 0.4 = 3.0
        assert scores["factuality"] == 3.0

    @pytest.mark.asyncio()
    async def test_zero_expected_value(self, scorer: FactualAccuracyScorer):
        """Edge case: expected value is 0 (e.g., Apple Scope 2)."""
        scores, _ = await scorer.score_with_ground_truth(
            prompt="test",
            response="Apple's Scope 2 emissions are 0 tCO2e due to 100% renewable energy.",
            criteria={"factuality": "Zero check"},
            max_score=5,
            expected_values={"scope2": 0},
        )
        assert scores["factuality"] == 5.0

    @pytest.mark.asyncio()
    async def test_fallback_to_rubric_without_ground_truth(self, scorer: FactualAccuracyScorer):
        """score() without ground truth should fall back to RubricScorer."""
        scores, _ = await scorer.score(
            prompt="What are climate risks?",
            response="Climate risks include transition risks from carbon pricing "
            "and physical risks from extreme weather events. Companies should "
            "consider scope 1 and scope 2 emissions in their assessments.",
            criteria={"relevance": "Relevant response"},
        )
        assert "relevance" in scores
        assert 0 <= scores["relevance"] <= 5

    @pytest.mark.asyncio()
    async def test_number_extraction_handles_commas(self, scorer: FactualAccuracyScorer):
        numbers = scorer._extract_numbers("Revenue: $1,234,567 and emissions of 55,200")
        assert 1234567 in numbers
        assert 55200 in numbers

    @pytest.mark.asyncio()
    async def test_number_extraction_handles_decimals(self, scorer: FactualAccuracyScorer):
        numbers = scorer._extract_numbers("Intensity is 12.34 tCO2e per $M")
        assert any(abs(n - 12.34) < 0.001 for n in numbers)

    @pytest.mark.asyncio()
    async def test_multi_criteria_gets_same_combined_score(self, scorer: FactualAccuracyScorer):
        """All criteria dimensions should get the same combined score."""
        scores, _ = await scorer.score_with_ground_truth(
            prompt="test",
            response="Apple has 55,200 tCO2e Scope 1.",
            criteria={
                "factuality": "Correct numbers",
                "reasoning": "Good explanation",
            },
            max_score=5,
            expected_values={"val": 55200},
            expected_entities=["Apple"],
        )
        assert scores["factuality"] == scores["reasoning"]


# ── Integration: Cases Load in Dataset Registry ──────────────────────────


class TestDatasetRegistration:
    """Verify domain_accuracy is properly registered in the dataset index."""

    def test_registered_in_datasets(self):
        from evals.datasets import DATASETS

        assert "domain_accuracy" in DATASETS
        assert len(DATASETS["domain_accuracy"]) == 15

    def test_included_in_all_dataset(self):
        from evals.datasets import DATASETS

        all_ids = {c.id for c in DATASETS["all"]}
        domain_ids = {c.id for c in DATASETS["domain_accuracy"]}
        assert domain_ids.issubset(all_ids)
