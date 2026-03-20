"""Tests for sector benchmarks with published citations."""

from app.benchmarks import SECTOR_BENCHMARKS, get_sector_baselines, get_sector_benchmark

# The 11 GICS sectors that the scoring engine requires
EXPECTED_SECTORS = {
    "Energy",
    "Utilities",
    "Materials",
    "Industrials",
    "Consumer Discretionary",
    "Consumer Staples",
    "Healthcare",
    "Financials",
    "Information Technology",
    "Real Estate",
    "Communication Services",
}


class TestSectorBenchmarks:
    def test_all_gics_sectors_covered(self):
        assert set(SECTOR_BENCHMARKS.keys()) == EXPECTED_SECTORS

    def test_transition_risk_weights_valid(self):
        for sector, data in SECTOR_BENCHMARKS.items():
            weight = data["transition_risk_weight"]
            assert 0.0 <= weight <= 1.0, f"{sector} transition_risk_weight out of range: {weight}"

    def test_physical_risk_weights_valid(self):
        for sector, data in SECTOR_BENCHMARKS.items():
            weight = data["physical_risk_weight"]
            assert 0.0 <= weight <= 1.0, f"{sector} physical_risk_weight out of range: {weight}"

    def test_emissions_intensity_positive(self):
        for sector, data in SECTOR_BENCHMARKS.items():
            intensity = data["emissions_intensity_benchmark_tco2e_per_m"]
            assert intensity > 0, f"{sector} emissions intensity must be positive"

    def test_every_sector_has_source_citation(self):
        for sector, data in SECTOR_BENCHMARKS.items():
            assert data["source"], f"{sector} missing source citation"
            assert len(data["source"]) > 10, f"{sector} source too short to be meaningful"

    def test_every_sector_has_methodology_note(self):
        for sector, data in SECTOR_BENCHMARKS.items():
            assert data["methodology_note"], f"{sector} missing methodology note"

    def test_energy_has_highest_transition_risk(self):
        """Energy sector should have the highest transition risk -- this is a domain invariant."""
        energy_tr = SECTOR_BENCHMARKS["Energy"]["transition_risk_weight"]
        for sector, data in SECTOR_BENCHMARKS.items():
            if sector != "Energy":
                assert energy_tr >= data["transition_risk_weight"], (
                    f"Energy ({energy_tr}) should have >= transition risk than {sector} "
                    f"({data['transition_risk_weight']})"
                )

    def test_real_estate_has_highest_physical_risk(self):
        """Real estate should have the highest physical risk -- direct building exposure."""
        re_pr = SECTOR_BENCHMARKS["Real Estate"]["physical_risk_weight"]
        for sector, data in SECTOR_BENCHMARKS.items():
            if sector != "Real Estate":
                assert re_pr >= data["physical_risk_weight"], (
                    f"Real Estate ({re_pr}) should have >= physical risk than {sector} "
                    f"({data['physical_risk_weight']})"
                )

    def test_utilities_highest_emissions_intensity(self):
        """Utilities should have the highest emissions intensity due to power generation."""
        utilities_ei = SECTOR_BENCHMARKS["Utilities"]["emissions_intensity_benchmark_tco2e_per_m"]
        for sector, data in SECTOR_BENCHMARKS.items():
            if sector != "Utilities":
                assert utilities_ei >= data["emissions_intensity_benchmark_tco2e_per_m"], (
                    f"Utilities ({utilities_ei}) should have >= intensity than {sector} "
                    f"({data['emissions_intensity_benchmark_tco2e_per_m']})"
                )


class TestGetSectorBaselines:
    def test_returns_legacy_format(self):
        baselines = get_sector_baselines()
        for sector, data in baselines.items():
            assert "transition_risk" in data, f"{sector} missing transition_risk key"
            assert "physical_risk" in data, f"{sector} missing physical_risk key"

    def test_same_sectors_as_benchmarks(self):
        baselines = get_sector_baselines()
        assert set(baselines.keys()) == set(SECTOR_BENCHMARKS.keys())

    def test_values_match_benchmarks(self):
        baselines = get_sector_baselines()
        for sector in SECTOR_BENCHMARKS:
            assert (
                baselines[sector]["transition_risk"]
                == (SECTOR_BENCHMARKS[sector]["transition_risk_weight"])
            )
            assert (
                baselines[sector]["physical_risk"]
                == (SECTOR_BENCHMARKS[sector]["physical_risk_weight"])
            )


class TestGetSectorBenchmark:
    def test_known_sector(self):
        result = get_sector_benchmark("Energy")
        assert result["transition_risk_weight"] == 0.90

    def test_unknown_sector_returns_default(self):
        result = get_sector_benchmark("Crypto Mining")
        assert result["transition_risk_weight"] == 0.50
        assert result["physical_risk_weight"] == 0.50
        assert "Default" in result["source"]
