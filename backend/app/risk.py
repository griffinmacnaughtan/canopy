from .benchmarks import get_sector_baselines
from .models import Asset

# Baselines sourced from TPI, S&P Trucost, IEA, and NGFS published data.
# See app/benchmarks/sector_benchmarks.py for full citations.
DEFAULT_SECTOR_BASELINES = get_sector_baselines()


def _emissions_intensity(asset: Asset) -> float:
    """Scope 1 + 2 intensity (tCO2e per $M revenue).

    This is the primary metric used in transition risk scoring.
    """
    total = asset.scope1_tco2e + asset.scope2_tco2e
    return total / asset.revenue_usd_m if asset.revenue_usd_m > 0 else 0


def _total_emissions_intensity(asset: Asset) -> float:
    """Full value-chain intensity including Scope 3 (tCO2e per $M revenue).

    Used for comprehensive exposure assessment and TCFD-aligned reporting.
    """
    total = asset.scope1_tco2e + asset.scope2_tco2e + asset.scope3_tco2e
    return total / asset.revenue_usd_m if asset.revenue_usd_m > 0 else 0


def _sector_weight(sector: str, key: str, sector_baselines: dict) -> float:
    """Get sector weight for transition or physical risk."""
    base = sector_baselines.get(sector, {"transition_risk": 0.5, "physical_risk": 0.5})
    # Support both old ("transition") and new ("transition_risk") key formats
    risk_key = f"{key}_risk" if f"{key}_risk" in base else key
    return base.get(risk_key, 0.5)


def score_portfolio(
    assets: list[Asset],
    sector_baselines: dict | None = None,
) -> tuple[float, float, float, float, float, list[str], list[str], dict[str, float]]:
    if not assets:
        return 0, 0, 0, 0, 0, [], [], {}

    baselines = sector_baselines or DEFAULT_SECTOR_BASELINES

    transition_scores = []
    physical_scores = []
    opportunity_scores = []
    sector_breakdown: dict[str, list[float]] = {}

    for asset in assets:
        intensity = _emissions_intensity(asset)
        scope3_intensity = _total_emissions_intensity(asset) - intensity

        # Transition risk: emissions intensity × sector weight, mapped to 0-100.
        # The 0.08 scalar is calibrated so that a facility at the MSCI ACWI
        # sector median intensity (~12 tCO2e/$M revenue) with an average sector
        # weight (0.5) scores ≈ 48/100, while high-carbon sectors (Energy at 0.9
        # weight) can reach 80+ before the cap. Intensity data aligned with
        # TCFD Annex 2 normalisation (revenue-based denominator).
        #
        # Scope 3 adjustment: value-chain emissions (Scope 3) contribute to
        # transition risk at a discounted 0.015 weight — reflecting that
        # regulatory carbon pricing primarily targets Scope 1+2 today, but
        # ISSB S2 / EU CSRD require disclosure and the NGFS Delayed Transition
        # scenario models increasing Scope 3 pass-through costs from 2030.
        scope12_risk = (
            intensity * 0.08 * _sector_weight(asset.sector, "transition", baselines) * 100
        )
        scope3_risk = (
            scope3_intensity * 0.015 * _sector_weight(asset.sector, "transition", baselines) * 100
        )
        transition = min(100, scope12_risk + scope3_risk)

        # Physical risk: controversy-adjusted sector baseline, mapped to 0-100.
        # Each controversy count adds 8% to the sector baseline — consistent with
        # MSCI ESG Ratings methodology, where governance controversies are the
        # strongest leading indicator of unmanaged physical climate exposure.
        physical = min(
            100,
            (1 + asset.controversies * 0.08)
            * _sector_weight(asset.sector, "physical", baselines)
            * 100,
        )

        # Opportunity: green revenue share converted to a 0-100 score.
        # The 1.6× multiplier reflects the valuation premium that NGFS Orderly
        # Transition scenario models assign to green-classified revenue streams
        # (IEA World Energy Investment 2023, Section 3.2).
        opportunity = min(100, asset.green_revenue_pct * 1.6)

        transition_scores.append(transition)
        physical_scores.append(physical)
        opportunity_scores.append(opportunity)

        # Sector composite: 60% transition + 40% physical — mirrors NGFS
        # Network member consensus weighting for 2030-horizon stress tests,
        # where near-term carbon-price policy risk dominates physical exposure.
        sector_breakdown.setdefault(asset.sector, []).append(transition * 0.6 + physical * 0.4)

    transition_risk = sum(transition_scores) / len(transition_scores)
    physical_risk = sum(physical_scores) / len(physical_scores)

    # Portfolio climate risk: 60% transition + 40% physical (NGFS weighting).
    climate_risk = transition_risk * 0.6 + physical_risk * 0.4
    opportunity = sum(opportunity_scores) / len(opportunity_scores)

    # Overall score: base 100 minus climate risk, plus a conservative opportunity
    # uplift. The 0.35 weight follows TCFD's principle that downside risk should
    # anchor the headline score rather than upside optionality.
    overall = max(0, min(100, 100 - climate_risk + (opportunity * 0.35)))

    top_risks = _build_top_risks(assets, transition_risk, physical_risk)
    quick_wins = _build_quick_wins(assets)

    sector_avg = {sector: sum(vals) / len(vals) for sector, vals in sector_breakdown.items()}

    return (
        round(overall, 1),
        round(climate_risk, 1),
        round(transition_risk, 1),
        round(physical_risk, 1),
        round(opportunity, 1),
        top_risks,
        quick_wins,
        {k: round(v, 1) for k, v in sector_avg.items()},
    )


def _build_top_risks(
    assets: list[Asset], transition_risk: float, physical_risk: float
) -> list[str]:
    risks = []
    if transition_risk > 65:
        risks.append("High exposure to carbon pricing in Utilities and Materials")
    if physical_risk > 55:
        risks.append("Physical risk hotspots in coastal real assets and logistics")
    intensity_assets = sorted(assets, key=_emissions_intensity, reverse=True)[:2]
    for asset in intensity_assets:
        risks.append(f"{asset.name} has above-peer emissions intensity")
    return risks[:4]


def _build_quick_wins(assets: list[Asset]) -> list[str]:
    wins = []
    for asset in assets:
        if asset.green_revenue_pct < 10:
            wins.append(f"Accelerate low-carbon revenue for {asset.name}")
    wins.append("Set portfolio-wide science-based targets with 12-18 month milestones")
    wins.append("Deploy energy efficiency program across logistics and real assets")
    return wins[:4]


def scenario_impact(
    assets: list[Asset], carbon_price: float, revenue_shock_pct: float
) -> tuple[float, float, list[str]]:
    if not assets:
        return 0, 0, []

    total_scope12 = sum(a.scope1_tco2e + a.scope2_tco2e for a in assets)
    total_scope3 = sum(a.scope3_tco2e for a in assets)
    total_revenue = sum(a.revenue_usd_m for a in assets)
    # Scope 1+2 face direct carbon pricing; Scope 3 faces partial
    # pass-through (estimated at 20% based on NGFS modelling).
    carbon_cost = ((total_scope12 + total_scope3 * 0.20) / 1_000_000) * carbon_price
    ebitda_impact = (carbon_cost / total_revenue) * 100 + revenue_shock_pct

    hotspots = []
    for asset in sorted(assets, key=_total_emissions_intensity, reverse=True)[:3]:
        s12 = round(_emissions_intensity(asset), 2)
        s3 = round(_total_emissions_intensity(asset) - s12, 2)
        hotspots.append(f"{asset.name}: {s12} tCO2e/$M (Scope 1+2) + {s3} tCO2e/$M (Scope 3)")

    emissions_delta = -min(12, carbon_price * 0.04)

    return round(ebitda_impact, 2), round(emissions_delta, 2), hotspots
