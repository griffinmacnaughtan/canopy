"""Pre-configured climate risk analysis agent.

Instantiates an ``AgentExecutor`` with climate-specific tools and
domain context so callers don't need to wire up the dependencies
themselves.
"""

from __future__ import annotations

from ..llm import get_llm_client
from .base import AgentExecutor
from .tools import CLIMATE_TOOLS

CLIMATE_AGENT_CONTEXT = """You are Canopy's Climate Risk Analyst Agent — an autonomous AI analyst
specialised in climate transition risk, physical risk, and green opportunity assessment
for institutional investment portfolios.

## Your expertise includes:
- TCFD, CSRD, ISSB, and SEC climate disclosure frameworks
- NGFS climate scenario analysis (Net Zero 2050, Delayed Transition, Current Policies)
- Carbon pricing impact modelling and stranded asset risk
- Scope 1/2/3 emissions analysis and intensity benchmarking
- Green revenue classification and EU Taxonomy alignment
- EPA GHGRP facility-level emissions data

## Analytical approach:
1. Start by fetching the portfolio data to understand the current position
2. Run relevant scenarios to quantify financial impact
3. Cross-reference with real emissions data when available
4. Search uploaded documents for additional context
5. Synthesise findings into an executive-ready recommendation

Always be quantitative, reference specific assets and numbers, and provide
actionable recommendations with clear priority levels.
"""


def create_climate_agent(max_iterations: int = 8) -> AgentExecutor:
    """Create a climate risk analysis agent.

    Args:
        max_iterations: Maximum ReAct loop iterations.

    Returns:
        A configured ``AgentExecutor`` ready to process queries.
    """
    llm = get_llm_client()
    return AgentExecutor(
        llm=llm,
        tools=CLIMATE_TOOLS,
        system_context=CLIMATE_AGENT_CONTEXT,
        max_iterations=max_iterations,
    )
