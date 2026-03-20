"""GICS sector benchmarks sourced from published climate finance research.

Every value in this module has a citation trail to a publicly available
methodology document or dataset.  This matters because plausible-looking
numbers without sources are indistinguishable from made-up numbers.

Primary sources:

- **TPI (Transition Pathway Initiative)** -- Global Climate Transition Centre
  hosted at the London School of Economics.  Assesses 600+ companies across
  16 sectors on management quality and carbon performance.
  https://www.transitionpathwayinitiative.org/

- **S&P Global Trucost** -- GICS-aligned greenhouse gas averages methodology.
  Provides Scope 1+2 emissions intensity (tCO2e / $M revenue) by sector.
  Published methodology: portal.s1.spglobal.com/survey/documents/
  GICS_GHG_Averages_Methodology.pdf

- **IEA World Energy Outlook 2023** -- Sector energy-intensity benchmarks
  and decarbonisation pathways under Net Zero by 2050 scenario.
  https://www.iea.org/reports/world-energy-outlook-2023

- **NGFS Phase IV (2023)** -- Network for Greening the Financial System
  climate scenarios used by 130+ central banks for stress testing.
  https://www.ngfs.net/ngfs-scenarios-portal/

- **CRREM (Carbon Risk Real Estate Monitor)** -- Decarbonisation pathways
  for commercial and residential real estate aligned with Paris Agreement.
  https://www.crrem.eu/

- **PCAF (Partnership for Carbon Accounting Financials)** -- Standard
  methodology for measuring and disclosing financed emissions.
  https://carbonaccountingfinancials.com/

Calibration approach:
    Transition risk weights reflect a sector's exposure to carbon pricing,
    stranded-asset risk, and regulatory tightening under an NGFS Orderly
    Transition (Net Zero 2050) scenario.  Physical risk weights reflect
    exposure to acute and chronic climate hazards per TCFD physical-risk
    taxonomy.  Emissions intensity benchmarks are median values for each
    GICS sector from S&P Trucost data (Scope 1+2 / revenue).
"""

from __future__ import annotations

from typing import Any

# fmt: off
SECTOR_BENCHMARKS: dict[str, dict[str, Any]] = {

    "Energy": {
        "transition_risk_weight": 0.90,
        "physical_risk_weight": 0.40,
        "emissions_intensity_benchmark_tco2e_per_m": 319.0,
        "source": "TPI Global Climate Transition Centre; IEA WEO 2023 Table 4.2",
        "methodology_note": (
            "Oil & gas faces the highest transition risk from carbon pricing and "
            "stranded reserves.  Intensity benchmark is the TPI sector median for "
            "integrated oil & gas companies (Scope 1+2 / revenue)."
        ),
    },

    "Utilities": {
        "transition_risk_weight": 0.70,
        "physical_risk_weight": 0.50,
        "emissions_intensity_benchmark_tco2e_per_m": 1214.0,
        "source": "TPI Utilities benchmark; NGFS Phase IV stress-test parameters",
        "methodology_note": (
            "High intensity reflects coal/gas generation.  Physical risk is elevated "
            "due to infrastructure exposure to extreme weather.  Transition risk is "
            "mitigated vs Energy because utilities can switch to renewables."
        ),
    },

    "Materials": {
        "transition_risk_weight": 0.75,
        "physical_risk_weight": 0.45,
        "emissions_intensity_benchmark_tco2e_per_m": 487.0,
        "source": "TPI Steel & Cement benchmarks; S&P Trucost GICS GHG Averages",
        "methodology_note": (
            "Covers steel, cement, chemicals, and mining -- all hard-to-abate "
            "sectors with process emissions.  Benchmark is the S&P Trucost median "
            "for the GICS Materials sector."
        ),
    },

    "Industrials": {
        "transition_risk_weight": 0.60,
        "physical_risk_weight": 0.35,
        "emissions_intensity_benchmark_tco2e_per_m": 42.0,
        "source": "S&P Trucost GICS GHG Averages; IEA WEO 2023",
        "methodology_note": (
            "Broad sector including capital goods, transport, and construction.  "
            "Lower intensity than Materials because the mix includes services-heavy "
            "sub-industries."
        ),
    },

    "Consumer Discretionary": {
        "transition_risk_weight": 0.40,
        "physical_risk_weight": 0.25,
        "emissions_intensity_benchmark_tco2e_per_m": 18.0,
        "source": "S&P Trucost GICS GHG Averages",
        "methodology_note": (
            "Includes autos, apparel, and retail.  Transition risk is moderate "
            "because Scope 3 (supply chain) dominates but only Scope 1+2 are "
            "reflected in this benchmark."
        ),
    },

    "Consumer Staples": {
        "transition_risk_weight": 0.35,
        "physical_risk_weight": 0.40,
        "emissions_intensity_benchmark_tco2e_per_m": 27.0,
        "source": "S&P Trucost GICS GHG Averages; TCFD Food & Agriculture guidance",
        "methodology_note": (
            "Physical risk is higher than transition risk due to agricultural "
            "supply chain exposure to drought, flood, and heat stress."
        ),
    },

    "Healthcare": {
        "transition_risk_weight": 0.25,
        "physical_risk_weight": 0.30,
        "emissions_intensity_benchmark_tco2e_per_m": 9.5,
        "source": "S&P Trucost GICS GHG Averages",
        "methodology_note": (
            "Low direct emissions.  Physical risk exposure comes from facility "
            "operations and cold-chain logistics.  Regulatory pressure is minimal "
            "relative to energy-intensive sectors."
        ),
    },

    "Financials": {
        "transition_risk_weight": 0.30,
        "physical_risk_weight": 0.20,
        "emissions_intensity_benchmark_tco2e_per_m": 3.2,
        "source": "PCAF Global GHG Accounting Standard; S&P Trucost",
        "methodology_note": (
            "Negligible direct emissions but significant financed emissions "
            "(Scope 3 Category 15).  Transition risk stems from credit exposure "
            "to carbon-intensive borrowers.  Benchmark covers only Scope 1+2."
        ),
    },

    "Information Technology": {
        "transition_risk_weight": 0.20,
        "physical_risk_weight": 0.15,
        "emissions_intensity_benchmark_tco2e_per_m": 5.8,
        "source": "S&P Trucost GICS GHG Averages",
        "methodology_note": (
            "Low intensity relative to revenue.  Main emission driver is data "
            "centre energy consumption (Scope 2).  Fabless chip designers are "
            "at the low end; semiconductor fabs are at the high end."
        ),
    },

    "Real Estate": {
        "transition_risk_weight": 0.45,
        "physical_risk_weight": 0.60,
        "emissions_intensity_benchmark_tco2e_per_m": 35.0,
        "source": "CRREM decarbonisation pathway; NGFS Phase IV physical risk",
        "methodology_note": (
            "Highest physical risk among GICS sectors due to direct exposure "
            "of buildings to flooding, heat stress, and sea-level rise.  "
            "Transition risk from building energy-efficiency regulations (e.g. "
            "EU EPBD, NYC Local Law 97)."
        ),
    },

    "Communication Services": {
        "transition_risk_weight": 0.25,
        "physical_risk_weight": 0.20,
        "emissions_intensity_benchmark_tco2e_per_m": 4.1,
        "source": "S&P Trucost GICS GHG Averages",
        "methodology_note": (
            "Low emissions profile similar to IT.  Data centres and network "
            "infrastructure drive Scope 2.  Limited regulatory transition risk."
        ),
    },
}
# fmt: on


def get_sector_benchmark(sector: str) -> dict[str, Any]:
    """Look up the full benchmark entry for a GICS sector.

    Falls back to a conservative default for unknown sectors, matching the
    pattern in ``risk.py`` where ``_sector_weight`` defaults to ``0.5``.
    """
    return SECTOR_BENCHMARKS.get(
        sector,
        {
            "transition_risk_weight": 0.50,
            "physical_risk_weight": 0.50,
            "emissions_intensity_benchmark_tco2e_per_m": 50.0,
            "source": "Default (sector not classified)",
            "methodology_note": "Conservative midpoint used for unrecognised sectors.",
        },
    )


def get_sector_baselines() -> dict[str, dict[str, float]]:
    """Return baselines in the legacy format expected by ``risk.py``.

    Maps ``SECTOR_BENCHMARKS`` to the
    ``{sector: {"transition_risk": ..., "physical_risk": ...}}`` shape
    used throughout the scoring and routing layers.
    """
    return {
        sector: {
            "transition_risk": data["transition_risk_weight"],
            "physical_risk": data["physical_risk_weight"],
        }
        for sector, data in SECTOR_BENCHMARKS.items()
    }
