"""Unit tests for risk scoring algorithms."""

import pytest
from app.risk import (
    score_portfolio,
    scenario_impact,
    copilot_answer,
    _emissions_intensity,
    _sector_weight,
    DEFAULT_SECTOR_BASELINES,
)
from app.models import Asset


class TestEmissionsIntensity:
    """Tests for emissions intensity calculation."""

    def test_basic_intensity(self):
        """Test basic emissions intensity calculation."""
        asset = Asset(
            id="test",
            name="Test Asset",
            sector="Utilities",
            region="North America",
            revenue_usd_m=1000,
            scope1_tco2e=500000,
            scope2_tco2e=100000,
            green_revenue_pct=10,
            controversies=0,
        )
        intensity = _emissions_intensity(asset)
        assert intensity == 600  # (500000 + 100000) / 1000

    def test_zero_scope2(self):
        """Test intensity with zero scope 2 emissions."""
        asset = Asset(
            id="test",
            name="Test Asset",
            sector="Information Technology",
            region="Europe",
            revenue_usd_m=2000,
            scope1_tco2e=200000,
            scope2_tco2e=0,
            green_revenue_pct=20,
            controversies=0,
        )
        intensity = _emissions_intensity(asset)
        assert intensity == 100  # 200000 / 2000

    def test_low_emissions(self):
        """Test intensity with minimal emissions."""
        asset = Asset(
            id="test",
            name="Test Asset",
            sector="Information Technology",
            region="North America",
            revenue_usd_m=100000,
            scope1_tco2e=1000,
            scope2_tco2e=500,
            green_revenue_pct=50,
            controversies=0,
        )
        intensity = _emissions_intensity(asset)
        assert intensity == 0.015  # (1000 + 500) / 100000


class TestSectorWeight:
    """Tests for sector weight lookups."""

    def test_utilities_transition(self):
        """Test utilities sector transition weight."""
        weight = _sector_weight("Utilities", "transition", DEFAULT_SECTOR_BASELINES)
        assert weight == 0.7

    def test_technology_physical(self):
        """Test technology sector physical weight."""
        weight = _sector_weight("Information Technology", "physical", DEFAULT_SECTOR_BASELINES)
        assert weight == 0.15

    def test_unknown_sector(self):
        """Test unknown sector returns default."""
        weight = _sector_weight("Unknown Sector", "transition", DEFAULT_SECTOR_BASELINES)
        assert weight == 0.5


class TestScorePortfolio:
    """Tests for portfolio scoring."""

    def test_empty_portfolio(self):
        """Test scoring an empty portfolio."""
        result = score_portfolio([])
        assert result[0] == 0  # overall
        assert result[1] == 0  # climate
        assert result[2] == 0  # transition
        assert result[3] == 0  # physical
        assert result[4] == 0  # opportunity
        assert result[5] == []  # top_risks
        assert result[6] == []  # quick_wins
        assert result[7] == {}  # sector_breakdown

    def test_single_asset_portfolio(self):
        """Test scoring a single-asset portfolio."""
        asset = Asset(
            id="test",
            name="Test Utility",
            sector="Utilities",
            region="North America",
            revenue_usd_m=1000,
            scope1_tco2e=1000000,
            scope2_tco2e=200000,
            green_revenue_pct=15,
            controversies=1,
        )
        result = score_portfolio([asset])

        overall, climate, transition, physical, opportunity, top_risks, quick_wins, sector = result

        # Verify all values are reasonable
        assert 0 <= overall <= 150
        assert 0 <= climate <= 100
        assert 0 <= transition <= 100
        assert 0 <= physical <= 100
        assert 0 <= opportunity <= 100
        assert isinstance(top_risks, list)
        assert isinstance(quick_wins, list)
        assert "Utilities" in sector

    def test_diversified_portfolio(self, sample_assets):
        """Test scoring a diversified portfolio."""
        result = score_portfolio(sample_assets)
        overall, climate, transition, physical, opportunity, top_risks, quick_wins, sector = result

        # Diversified portfolio should have multiple sectors
        assert len(sector) >= 2

        # Should identify risks and wins
        assert len(top_risks) > 0
        assert len(quick_wins) > 0


class TestScenarioImpact:
    """Tests for scenario stress testing."""

    def test_empty_portfolio_scenario(self):
        """Test scenario on empty portfolio."""
        ebitda, emissions, hotspots = scenario_impact([], 100, -2.0)
        assert ebitda == 0
        assert emissions == 0
        assert hotspots == []

    def test_net_zero_scenario(self, sample_assets):
        """Test Orderly Net Zero scenario."""
        ebitda, emissions, hotspots = scenario_impact(sample_assets, 120, -1.8)

        # EBITDA should be negative (cost)
        assert ebitda < 0

        # Emissions delta should be negative (reduction)
        assert emissions < 0

        # Should identify top 3 hotspots
        assert len(hotspots) == 3

    def test_high_carbon_price(self, sample_assets):
        """Test impact of high carbon price."""
        low_price_ebitda, _, _ = scenario_impact(sample_assets, 50, 0)
        high_price_ebitda, _, _ = scenario_impact(sample_assets, 200, 0)

        # Higher carbon price should have worse (larger magnitude) EBITDA impact
        # The value represents cost as positive, so higher is worse
        assert abs(high_price_ebitda) > abs(low_price_ebitda)


class TestCopilotAnswer:
    """Tests for keyword-based copilot responses."""

    def test_risk_question(self, sample_assets):
        """Test question about top risks."""
        answer = copilot_answer("What are the top risks in my portfolio?", sample_assets)
        assert "risk" in answer.lower() or "carbon" in answer.lower()

    def test_opportunity_question(self, sample_assets):
        """Test question about opportunities."""
        answer = copilot_answer("What opportunities do I have?", sample_assets)
        assert "upside" in answer.lower() or "green" in answer.lower()

    def test_targets_question(self, sample_assets):
        """Test question about SBT targets."""
        answer = copilot_answer("How should I set SBT targets?", sample_assets)
        assert "sbti" in answer.lower() or "target" in answer.lower()

    def test_fallback_answer(self, sample_assets):
        """Test fallback for unrecognized questions."""
        answer = copilot_answer("What is the meaning of life?", sample_assets)
        assert len(answer) > 0  # Should return something
