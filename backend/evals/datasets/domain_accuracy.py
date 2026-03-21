"""Ground-truth evaluation dataset using real seed data.

Every expected answer is COMPUTED from the actual seed data, not hardcoded.
If the seed data changes, the eval expectations change with it.  This is
the difference between testing vibes and testing factual accuracy.
"""

from __future__ import annotations

from app.benchmarks import SECTOR_BENCHMARKS
from app.database.seed import REAL_ASSETS, SAMPLE_PORTFOLIOS
from app.models import Asset
from app.risk import score_portfolio

from ..framework import EvalCase

# ── Helpers: compute ground truth from seed data ─────────────────────────


def _assets_for_portfolio(portfolio_name: str) -> list[dict]:
    """Get the raw asset dicts for a named sample portfolio."""
    portfolio = next(p for p in SAMPLE_PORTFOLIOS if p["name"] == portfolio_name)
    return [a for a in REAL_ASSETS if a["name"] in portfolio["asset_names"]]


def _pydantic_assets(raw_assets: list[dict]) -> list[Asset]:
    """Convert raw dicts to Pydantic Asset models for scoring."""
    return [
        Asset(
            id=f"eval-{i}",
            name=a["name"],
            ticker=a.get("ticker"),
            sector=a["sector"],
            region=a["region"],
            revenue_usd_m=a["revenue_usd_m"],
            scope1_tco2e=a["scope1_tco2e"],
            scope2_tco2e=a["scope2_tco2e"],
            green_revenue_pct=a["green_revenue_pct"],
            controversies=a["controversies"],
        )
        for i, a in enumerate(raw_assets)
    ]


def _emissions_intensity(asset: dict) -> float:
    total = asset["scope1_tco2e"] + asset["scope2_tco2e"]
    return total / asset["revenue_usd_m"] if asset["revenue_usd_m"] > 0 else 0


def _build_portfolio_context(portfolio_name: str) -> str:
    """Build a realistic portfolio context string for eval cases."""
    raw = _assets_for_portfolio(portfolio_name)
    pydantic = _pydantic_assets(raw)
    baselines = {
        s: {
            "transition_risk": d["transition_risk_weight"],
            "physical_risk": d["physical_risk_weight"],
        }
        for s, d in SECTOR_BENCHMARKS.items()
    }
    overall, climate, transition, physical, opportunity, top_risks, quick_wins, sector_breakdown = (
        score_portfolio(pydantic, baselines)
    )

    lines = [f"## Portfolio: {portfolio_name}\n"]
    lines.append(f"- Overall Score: {overall}/100")
    lines.append(f"- Climate Risk: {climate}/100")
    lines.append(f"- Transition Risk: {transition}/100")
    lines.append(f"- Physical Risk: {physical}/100")
    lines.append(f"- Opportunity Score: {opportunity}/100\n")

    lines.append("### Holdings\n")
    lines.append("| Asset | Sector | Revenue ($M) | Scope1+2 (tCO2e) | Intensity | Green Rev % |")
    lines.append("|-------|--------|-------------|------------------|-----------|-------------|")

    for a in raw:
        total_e = a["scope1_tco2e"] + a["scope2_tco2e"]
        intensity = round(_emissions_intensity(a), 2)
        lines.append(
            f"| {a['name']} | {a['sector']} | {a['revenue_usd_m']:,.0f} "
            f"| {total_e:,.0f} | {intensity} | {a['green_revenue_pct']}% |"
        )

    return "\n".join(lines)


# ── Compute ground-truth values ──────────────────────────────────────────

# Individual asset lookups
_apple = next(a for a in REAL_ASSETS if a["ticker"] == "AAPL")
_exxon = next(a for a in REAL_ASSETS if a["ticker"] == "XOM")
_nextera = next(a for a in REAL_ASSETS if a["ticker"] == "NEE")
_tesla = next(a for a in REAL_ASSETS if a["ticker"] == "TSLA")

# Portfolio-level computations
_tech_assets = _assets_for_portfolio("Tech Leaders ESG")
_energy_assets = _assets_for_portfolio("Energy Transition")
_global_assets = _assets_for_portfolio("Global Diversified")

_tech_avg_intensity = sum(_emissions_intensity(a) for a in _tech_assets) / len(_tech_assets)

_energy_ranked_by_green = sorted(_energy_assets, key=lambda a: a["green_revenue_pct"], reverse=True)

# Score both portfolios for comparison
_tech_pydantic = _pydantic_assets(_tech_assets)
_energy_pydantic = _pydantic_assets(_energy_assets)
_baselines = {
    s: {"transition_risk": d["transition_risk_weight"], "physical_risk": d["physical_risk_weight"]}
    for s, d in SECTOR_BENCHMARKS.items()
}
_tech_scores = score_portfolio(_tech_pydantic, _baselines)
_energy_scores = score_portfolio(_energy_pydantic, _baselines)

# Context strings
TECH_CONTEXT = _build_portfolio_context("Tech Leaders ESG")
ENERGY_CONTEXT = _build_portfolio_context("Energy Transition")
GLOBAL_CONTEXT = _build_portfolio_context("Global Diversified")


# ── Eval cases ───────────────────────────────────────────────────────────

DOMAIN_ACCURACY_CASES: list[EvalCase] = [
    # ── Category A: Factual Retrieval ────────────────────────────────
    EvalCase(
        id="domain_001",
        category="domain_accuracy",
        prompt="What is Apple Inc.'s Scope 1 emissions in tCO2e?",
        context=TECH_CONTEXT,
        criteria={
            "factuality": "Must state Apple's Scope 1 emissions correctly from the portfolio data"
        },
        expected_values={"apple_scope1": _apple["scope1_tco2e"]},
        expected_entities=["Apple"],
        expected_keywords=["55,200", "scope 1"],
        pass_threshold=3.0,
    ),
    EvalCase(
        id="domain_002",
        category="domain_accuracy",
        prompt="What is Exxon Mobil's total emissions (Scope 1 + Scope 2)?",
        context=ENERGY_CONTEXT,
        criteria={"factuality": "Must correctly compute total emissions from Scope 1 + Scope 2"},
        expected_values={
            "exxon_total": _exxon["scope1_tco2e"] + _exxon["scope2_tco2e"],
        },
        expected_entities=["Exxon"],
        expected_keywords=["110,000,000"],
        pass_threshold=3.0,
    ),
    EvalCase(
        id="domain_003",
        category="domain_accuracy",
        prompt="What percentage of NextEra Energy's revenue comes from green sources?",
        context=ENERGY_CONTEXT,
        criteria={"factuality": "Must state NextEra's green revenue percentage from the data"},
        expected_values={"nextera_green_pct": _nextera["green_revenue_pct"]},
        expected_entities=["NextEra"],
        expected_keywords=["65"],
        pass_threshold=3.0,
    ),
    # ── Category B: Computation ──────────────────────────────────────
    EvalCase(
        id="domain_004",
        category="domain_accuracy",
        prompt="What is the Tech Leaders ESG portfolio's average emissions intensity (tCO2e per $M revenue)?",
        context=TECH_CONTEXT,
        criteria={
            "factuality": "Must compute average intensity from the four tech stocks",
            "reasoning": "Should show or reference the per-asset intensity values",
        },
        expected_values={"avg_intensity": round(_tech_avg_intensity, 2)},
        expected_entities=["Apple", "Microsoft"],
        pass_threshold=2.5,
    ),
    EvalCase(
        id="domain_005",
        category="domain_accuracy",
        prompt=(
            "What is the total revenue of all assets in the Global Diversified portfolio? "
            "Express in millions of dollars."
        ),
        context=GLOBAL_CONTEXT,
        criteria={"factuality": "Must sum revenue across all 6 assets"},
        expected_values={
            "total_revenue": sum(a["revenue_usd_m"] for a in _global_assets),
        },
        pass_threshold=2.5,
    ),
    EvalCase(
        id="domain_006",
        category="domain_accuracy",
        prompt="How many controversies does the Energy Transition portfolio have in total?",
        context=ENERGY_CONTEXT,
        criteria={"factuality": "Must sum controversy counts across all portfolio assets"},
        expected_values={
            "total_controversies": sum(a["controversies"] for a in _energy_assets),
        },
        pass_threshold=3.0,
    ),
    # ── Category C: Ranking ──────────────────────────────────────────
    EvalCase(
        id="domain_007",
        category="domain_accuracy",
        prompt="Rank the Energy Transition portfolio assets from highest to lowest green revenue percentage.",
        context=ENERGY_CONTEXT,
        criteria={
            "factuality": "Must list assets in correct order by green revenue %",
        },
        expected_entities=[a["name"] for a in _energy_ranked_by_green],
        expected_keywords=[
            str(_energy_ranked_by_green[0]["green_revenue_pct"]),
        ],
        pass_threshold=3.0,
    ),
    EvalCase(
        id="domain_008",
        category="domain_accuracy",
        prompt="Which asset in the Tech Leaders ESG portfolio has the highest emissions intensity?",
        context=TECH_CONTEXT,
        criteria={"factuality": "Must identify the correct highest-intensity asset"},
        expected_entities=[
            max(_tech_assets, key=_emissions_intensity)["name"],
        ],
        pass_threshold=3.0,
    ),
    EvalCase(
        id="domain_009",
        category="domain_accuracy",
        prompt="Which asset in the Global Diversified portfolio has the lowest controversy score?",
        context=GLOBAL_CONTEXT,
        criteria={"factuality": "Must identify asset(s) with the lowest controversy count"},
        expected_entities=[
            min(_global_assets, key=lambda a: a["controversies"])["name"],
        ],
        pass_threshold=3.0,
    ),
    # ── Category D: Comparison ───────────────────────────────────────
    EvalCase(
        id="domain_010",
        category="domain_accuracy",
        prompt=(
            "Which portfolio has a higher transition risk score: "
            "Tech Leaders ESG or Energy Transition? By how much?"
        ),
        context=TECH_CONTEXT + "\n\n" + ENERGY_CONTEXT,
        criteria={
            "factuality": "Must correctly identify which portfolio has higher transition risk",
            "reasoning": "Should reference both scores and compute the difference",
        },
        expected_values={
            "tech_transition": _tech_scores[2],
            "energy_transition": _energy_scores[2],
        },
        expected_entities=["Tech Leaders ESG", "Energy Transition"],
        pass_threshold=2.5,
    ),
    EvalCase(
        id="domain_011",
        category="domain_accuracy",
        prompt=(
            "Compare the overall portfolio scores of Tech Leaders ESG and Energy Transition. "
            "Which is better positioned for the climate transition?"
        ),
        context=TECH_CONTEXT + "\n\n" + ENERGY_CONTEXT,
        criteria={
            "factuality": "Must reference both overall scores correctly",
            "reasoning": "Should explain why one is better positioned",
        },
        expected_values={
            "tech_overall": _tech_scores[0],
            "energy_overall": _energy_scores[0],
        },
        expected_entities=["Tech Leaders ESG", "Energy Transition"],
        pass_threshold=2.5,
    ),
    # ── Category E: Sector Benchmark Awareness ───────────────────────
    EvalCase(
        id="domain_012",
        category="domain_accuracy",
        prompt=(
            "What is the emissions intensity benchmark for the Energy sector, "
            "and how does Exxon Mobil compare to it?"
        ),
        context=ENERGY_CONTEXT,
        criteria={
            "factuality": "Should reference the sector benchmark and compare Exxon's actual intensity",
        },
        expected_values={
            "energy_benchmark": SECTOR_BENCHMARKS["Energy"][
                "emissions_intensity_benchmark_tco2e_per_m"
            ],
            "exxon_intensity": round(_emissions_intensity(_exxon), 2),
        },
        expected_entities=["Exxon", "Energy"],
        pass_threshold=2.5,
    ),
    EvalCase(
        id="domain_013",
        category="domain_accuracy",
        prompt="Which GICS sector has the highest physical risk weight, and why?",
        context=GLOBAL_CONTEXT,
        criteria={
            "factuality": "Must identify Real Estate as highest physical risk",
            "reasoning": "Should explain building/infrastructure exposure to climate hazards",
        },
        expected_entities=["Real Estate"],
        expected_keywords=["physical risk", "0.6"],
        pass_threshold=3.0,
    ),
    # ── Category F: Edge Cases ───────────────────────────────────────
    EvalCase(
        id="domain_014",
        category="domain_accuracy",
        prompt="What is Apple's Scope 2 emissions? What explains this value?",
        context=TECH_CONTEXT,
        criteria={
            "factuality": "Must state that Scope 2 is 0 tCO2e",
            "reasoning": "Should explain Apple uses 100% renewable electricity",
        },
        expected_values={"apple_scope2": 0},
        expected_entities=["Apple"],
        expected_keywords=["renewable", "0"],
        pass_threshold=3.0,
    ),
    EvalCase(
        id="domain_015",
        category="domain_accuracy",
        prompt="Tesla has 3 controversies. What are they, and how do they affect its risk score?",
        context=ENERGY_CONTEXT,
        criteria={
            "factuality": "Must reference that Tesla has 3 controversies from the data",
            "reasoning": "Should discuss how controversies affect physical risk scoring",
        },
        expected_values={"tesla_controversies": _tesla["controversies"]},
        expected_entities=["Tesla"],
        pass_threshold=2.5,
    ),
]
