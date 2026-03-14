"""Unit tests for risk scoring algorithms."""

import pytest

from app.models import Asset
from app.risk import (
    DEFAULT_SECTOR_BASELINES,
    _emissions_intensity,
    _sector_weight,
    scenario_impact,
    score_portfolio,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_asset(**kwargs) -> Asset:
    """Create an Asset with sensible defaults; override with kwargs."""
    defaults: dict = {
        "id": "test",
        "name": "Test Co",
        "sector": "Information Technology",
        "region": "North America",
        "revenue_usd_m": 1000.0,
        "scope1_tco2e": 10_000,
        "scope2_tco2e": 5_000,
        "green_revenue_pct": 20.0,
        "controversies": 0,
    }
    defaults.update(kwargs)
    return Asset(**defaults)


# ---------------------------------------------------------------------------
# Emissions Intensity
# ---------------------------------------------------------------------------


class TestEmissionsIntensity:
    """Tests for emissions intensity calculation."""

    def test_basic_intensity(self):
        asset = make_asset(
            sector="Utilities",
            revenue_usd_m=1_000,
            scope1_tco2e=500_000,
            scope2_tco2e=100_000,
        )
        assert _emissions_intensity(asset) == pytest.approx(600.0)

    def test_zero_scope2(self):
        asset = make_asset(revenue_usd_m=2_000, scope1_tco2e=200_000, scope2_tco2e=0)
        assert _emissions_intensity(asset) == pytest.approx(100.0)

    def test_low_emissions(self):
        asset = make_asset(revenue_usd_m=100_000, scope1_tco2e=1_000, scope2_tco2e=500)
        assert _emissions_intensity(asset) == pytest.approx(0.015)

    def test_combined_scope_emissions(self):
        asset = make_asset(revenue_usd_m=1_000, scope1_tco2e=300_000, scope2_tco2e=200_000)
        assert _emissions_intensity(asset) == pytest.approx(500.0)


# ---------------------------------------------------------------------------
# Sector Weight
# ---------------------------------------------------------------------------


class TestSectorWeight:
    """Tests for sector weight lookups."""

    def test_utilities_transition(self):
        weight = _sector_weight("Utilities", "transition", DEFAULT_SECTOR_BASELINES)
        assert weight == pytest.approx(0.7)

    def test_technology_physical(self):
        weight = _sector_weight("Information Technology", "physical", DEFAULT_SECTOR_BASELINES)
        assert weight == pytest.approx(0.15)

    def test_energy_highest_transition(self):
        weight = _sector_weight("Energy", "transition", DEFAULT_SECTOR_BASELINES)
        assert weight == pytest.approx(0.9)

    def test_unknown_sector_defaults_to_half(self):
        weight = _sector_weight("Unicorn Sector", "transition", DEFAULT_SECTOR_BASELINES)
        assert weight == pytest.approx(0.5)

    def test_all_sectors_have_valid_weights(self):
        for sector in DEFAULT_SECTOR_BASELINES:
            t = _sector_weight(sector, "transition", DEFAULT_SECTOR_BASELINES)
            p = _sector_weight(sector, "physical", DEFAULT_SECTOR_BASELINES)
            assert 0.0 <= t <= 1.0, f"{sector}: transition weight {t} out of [0,1]"
            assert 0.0 <= p <= 1.0, f"{sector}: physical weight {p} out of [0,1]"


# ---------------------------------------------------------------------------
# Portfolio Scoring
# ---------------------------------------------------------------------------


class TestScorePortfolio:
    """Tests for portfolio scoring."""

    def test_empty_portfolio(self):
        overall, climate, transition, physical, opp, risks, wins, sectors = score_portfolio([])
        assert overall == 0
        assert climate == 0
        assert transition == 0
        assert physical == 0
        assert opp == 0
        assert risks == []
        assert wins == []
        assert sectors == {}

    def test_single_asset_value_ranges(self):
        asset = make_asset(
            sector="Utilities",
            revenue_usd_m=1_000,
            scope1_tco2e=1_000_000,
            scope2_tco2e=200_000,
            green_revenue_pct=15,
            controversies=1,
        )
        overall, climate, transition, physical, opp, risks, wins, sectors = score_portfolio([asset])

        assert 0 <= climate <= 100
        assert 0 <= transition <= 100
        assert 0 <= physical <= 100
        assert 0 <= opp <= 100
        assert overall >= 0
        assert isinstance(risks, list)
        assert isinstance(wins, list)
        assert "Utilities" in sectors

    def test_diversified_portfolio(self, sample_assets):
        _, _, _, _, _, risks, wins, sectors = score_portfolio(sample_assets)

        assert len(sectors) >= 2, "Diversified portfolio should span ≥2 sectors"
        assert len(risks) > 0
        assert len(wins) > 0

    def test_green_revenue_improves_opportunity(self):
        """Higher green revenue share must yield a higher opportunity score."""
        brown = make_asset(green_revenue_pct=0)
        green = make_asset(green_revenue_pct=100)

        _, _, _, _, opp_brown, _, _, _ = score_portfolio([brown])
        _, _, _, _, opp_green, _, _, _ = score_portfolio([green])

        assert opp_green > opp_brown

    def test_high_emissions_intensity_raises_transition_risk(self):
        low = make_asset(sector="Energy", scope1_tco2e=1_000, scope2_tco2e=0)
        high = make_asset(sector="Energy", scope1_tco2e=100_000_000, scope2_tco2e=0)

        _, _, t_low, _, _, _, _, _ = score_portfolio([low])
        _, _, t_high, _, _, _, _, _ = score_portfolio([high])

        assert t_high > t_low

    def test_controversies_raise_physical_risk(self):
        clean = make_asset(controversies=0)
        controversial = make_asset(controversies=5)

        _, _, _, p_clean, _, _, _, _ = score_portfolio([clean])
        _, _, _, p_controversial, _, _, _, _ = score_portfolio([controversial])

        assert p_controversial > p_clean

    def test_overall_score_never_negative(self, sample_assets):
        overall, *_ = score_portfolio(sample_assets)
        assert overall >= 0

    def test_sector_breakdown_keys_match_assets(self):
        assets = [
            make_asset(id="1", name="Tech", sector="Information Technology"),
            make_asset(id="2", name="Energy", sector="Energy"),
        ]
        _, _, _, _, _, _, _, sectors = score_portfolio(assets)
        assert "Information Technology" in sectors
        assert "Energy" in sectors

    def test_scores_are_rounded_to_one_decimal(self, sample_assets):
        overall, climate, transition, physical, opp, _, _, _ = score_portfolio(sample_assets)
        for val in (overall, climate, transition, physical, opp):
            assert val == round(val, 1)


# ---------------------------------------------------------------------------
# Scenario Impact
# ---------------------------------------------------------------------------


class TestScenarioImpact:
    """Tests for scenario stress testing."""

    def test_empty_portfolio(self):
        ebitda, emissions, hotspots = scenario_impact([], 100, -2.0)
        assert ebitda == 0
        assert emissions == 0
        assert hotspots == []

    def test_net_zero_scenario(self, sample_assets):
        ebitda, emissions, hotspots = scenario_impact(sample_assets, 120, -1.8)

        assert ebitda < 0, "Combined carbon cost + revenue shock should be negative"
        assert emissions < 0, "Emissions delta should be negative (reduction)"
        assert len(hotspots) == 3

    def test_higher_carbon_price_worsens_ebitda(self, sample_assets):
        low_ebitda, _, _ = scenario_impact(sample_assets, 50, 0)
        high_ebitda, _, _ = scenario_impact(sample_assets, 200, 0)

        assert abs(high_ebitda) > abs(low_ebitda)

    def test_hotspot_count_capped_at_three(self, sample_assets):
        _, _, hotspots = scenario_impact(sample_assets, 100, -2.0)
        assert len(hotspots) <= 3

    def test_emissions_delta_capped_at_minus_12(self):
        """Emissions delta floor is −12% even at extreme carbon prices."""
        assets = [make_asset(scope1_tco2e=1_000_000, scope2_tco2e=500_000)]
        _, emissions_delta, _ = scenario_impact(assets, 10_000, -5.0)
        assert emissions_delta >= -12

    def test_zero_carbon_price_pure_revenue_shock(self, sample_assets):
        """With zero carbon price the EBITDA impact equals the revenue shock."""
        revenue_shock = -3.0
        ebitda, _, _ = scenario_impact(sample_assets, 0, revenue_shock)
        assert ebitda == pytest.approx(revenue_shock, abs=0.01)
