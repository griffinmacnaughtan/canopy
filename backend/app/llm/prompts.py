"""Prompt engineering for Canopy."""

from typing import Any

SYSTEM_PROMPT = """You are an ESG and climate risk analyst copilot for institutional investors and finance teams. Your role is to provide actionable insights on portfolio climate risk, regulatory readiness, and transition opportunities.

## Key Principles

1. **Be specific** - Always reference actual asset names, sectors, and metrics from the portfolio context provided.

2. **Be actionable** - Provide clear, concrete recommendations that can be implemented. Avoid vague suggestions.

3. **Be quantitative** - Use numbers from the portfolio context. Reference emissions intensity (tCO2e/$M revenue), green revenue percentages, and risk scores.

4. **Be regulatory-aware** - Reference relevant frameworks: TCFD, CSRD, SBTi, EU Taxonomy, SEC climate rules, ISSB standards.

5. **Be balanced** - Acknowledge both risks and opportunities. Climate transition involves both defensive risk mitigation and offensive green growth.

## Response Format

Structure your responses with clear sections using markdown headers (##) and bullet points:

## Key Finding
Lead with the most important insight in 1-2 sentences.

## Analysis
Provide supporting data and context with bullet points.

## Recommendations
Actionable next steps with priority levels.

## Considerations
Caveats, data gaps, or areas needing further analysis.

**Formatting Rules:**
- Use ## for section headers, not bold text for headers
- Always put a blank line before headers and lists
- Use bullet points (-) for lists, not numbered lists unless order matters
- Keep bold (**text**) for emphasis within paragraphs, not for section titles

## Domain Knowledge

**Risk Types:**
- Transition Risk: Carbon pricing exposure, stranded asset risk, policy/regulatory changes, technology disruption
- Physical Risk: Acute (extreme weather events) and chronic (sea level rise, temperature changes)
- Opportunity: Green revenue growth, energy efficiency, low-carbon products/services

**Key Metrics:**
- Emissions Intensity: (Scope 1 + Scope 2) / Revenue - measures carbon efficiency
- Green Revenue %: Revenue from climate solutions and sustainable products
- Controversy Score: 0-5 scale indicating ESG-related incidents

**Sector Context:**
- Utilities & Materials: Highest transition risk due to emissions intensity
- Real Estate: Mixed physical/transition risk depending on location and building efficiency
- Technology: Lower direct emissions but supply chain and energy use considerations

**SEC Filing Context:**
When SEC filing excerpts are provided, cite specific company disclosures to ground your analysis. Use phrases like "According to [Company]'s 10-K filing..." rather than generating unsupported claims. This demonstrates regulatory-grade sourcing.

**Honesty & Confidence:**
If the available data is insufficient to answer a question confidently, say so explicitly. Identify what data is missing and what the user could provide to get a better answer. Never fabricate statistics, company disclosures, or regulatory details. Partial answers grounded in real data are far more valuable than comprehensive answers built on speculation.

Keep responses focused and executive-ready. Finance teams need insights they can act on, not academic dissertations."""


def build_portfolio_context(
    assets: list[dict[str, Any]],
    scores: dict[str, Any],
    scenarios: dict[str, Any],
) -> str:
    """Build portfolio context string for RAG injection.

    Args:
        assets: List of asset dictionaries with emissions and financial data.
        scores: Portfolio scores including risk breakdowns.
        scenarios: Available scenario definitions.

    Returns:
        Formatted context string for the LLM.
    """
    lines = ["## Portfolio Context\n"]

    # Portfolio scores
    lines.append("### Risk Scores")
    lines.append(f"- Overall Portfolio Score: {scores.get('overall_score', 'N/A')}/100")
    lines.append(f"- Climate Risk: {scores.get('climate_risk', 'N/A')}/100")
    lines.append(f"- Transition Risk: {scores.get('transition_risk', 'N/A')}/100")
    lines.append(f"- Physical Risk: {scores.get('physical_risk', 'N/A')}/100")
    lines.append(f"- Opportunity Score: {scores.get('opportunity_score', 'N/A')}/100")
    lines.append("")

    # Top risks
    if scores.get("top_risks"):
        lines.append("### Top Risks")
        for risk in scores["top_risks"]:
            lines.append(f"- {risk}")
        lines.append("")

    # Quick wins
    if scores.get("quick_wins"):
        lines.append("### Quick Wins")
        for win in scores["quick_wins"]:
            lines.append(f"- {win}")
        lines.append("")

    # Sector breakdown
    if scores.get("sector_breakdown"):
        lines.append("### Sector Risk Breakdown")
        for sector, score in scores["sector_breakdown"].items():
            lines.append(f"- {sector}: {score}/100")
        lines.append("")

    # Asset details
    lines.append("### Portfolio Holdings\n")
    lines.append(
        "| Asset | Sector | Region | Revenue ($M) | Scope1+2 (tCO2e) | Intensity | Green Rev % | Controversies |"
    )
    lines.append(
        "|-------|--------|--------|--------------|------------------|-----------|-------------|---------------|"
    )

    total_revenue = 0
    total_emissions = 0

    for asset in assets:
        name = asset.get("name", "Unknown")
        sector = asset.get("sector", "N/A")
        region = asset.get("region", "N/A")
        revenue = asset.get("revenue_usd_m", 0)
        scope1 = asset.get("scope1_tco2e", 0)
        scope2 = asset.get("scope2_tco2e", 0)
        total_scope = scope1 + scope2
        intensity = round(total_scope / revenue, 2) if revenue > 0 else 0
        green_pct = asset.get("green_revenue_pct", 0)
        controversies = asset.get("controversies", 0)

        total_revenue += revenue
        total_emissions += total_scope

        lines.append(
            f"| {name} | {sector} | {region} | {revenue:,.0f} | {total_scope:,.0f} | {intensity:,.2f} | {green_pct}% | {controversies} |"
        )

    lines.append("")

    # Portfolio totals
    avg_intensity = round(total_emissions / total_revenue, 2) if total_revenue > 0 else 0
    lines.append(
        f"**Portfolio Totals:** ${total_revenue:,.0f}M revenue, {total_emissions:,.0f} tCO2e emissions, {avg_intensity} tCO2e/$M intensity"
    )
    lines.append("")

    # Scenarios
    if scenarios:
        lines.append("### Available Scenarios")
        for name, params in scenarios.items():
            carbon = params.get("carbon_price", "N/A")
            shock = params.get("revenue_shock", "N/A")
            lines.append(f"- **{name}**: ${carbon}/tCO2e carbon price, {shock}% revenue shock")
        lines.append("")

    return "\n".join(lines)


def build_user_message(
    question: str,
    context: str,
    document_context: str | None = None,
) -> str:
    """Build the user message with context and question.

    Args:
        question: The user's question.
        context: The portfolio context string.
        document_context: Optional extracted text from uploaded documents.

    Returns:
        Formatted user message.
    """
    parts = [f"Here is the current portfolio data:\n\n{context}"]

    if document_context:
        parts.append(
            f"\n\n## Uploaded Documents\n\nThe user has uploaded the following documents for analysis:\n\n{document_context}"
        )

    parts.append(f"\n\n## User Question\n\n{question}")
    parts.append(
        "\n\nPlease provide a focused, actionable response based on the portfolio data and any uploaded documents above."
    )

    return "".join(parts)


def get_source_attribution(
    has_documents: bool,
    document_count: int = 0,
    has_pipeline_data: bool = False,
    filing_sources: list[dict] | None = None,
) -> list[str]:
    """Generate source attribution for the response.

    When filing sources are provided, each cited filing gets its own
    entry with company, section, and date — giving users chunk-level
    traceability instead of a generic "SEC filings" label.
    """
    sources = [
        "Portfolio asset inventory",
        "Sector benchmarks (TPI, S&P Trucost, IEA — see benchmarks module)",
        "Scenario library (NGFS Phase IV)",
    ]

    if filing_sources:
        seen: set[str] = set()
        for fs in filing_sources:
            company = fs.get("company", "Unknown")
            filing = fs.get("filing_type", "10-K")
            section = fs.get("section", "")
            date = fs.get("filing_date", "")
            key = f"{company}|{filing}"
            if key in seen:
                continue
            seen.add(key)
            label = f"{company} {filing}"
            if section:
                label += f" — {section}"
            if date:
                label += f" ({date})"
            sources.append(label)

    if has_pipeline_data:
        sources.append("EPA GHGRP emissions data")

    if has_documents:
        sources.append(f"Uploaded documents ({document_count} files)")

    return sources
