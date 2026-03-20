"""Agentic AI framework for autonomous multi-step analysis.

Implements a ReAct (Reasoning + Acting) agent loop where the LLM can
plan, select tools, execute them, observe results, and iterate until
it has enough information to deliver a synthesised answer.
"""

from .base import AgentExecutor, AgentResult, ToolCall, ToolDefinition
from .climate_agent import create_climate_agent
from .tools import CLIMATE_TOOLS

__all__ = [
    "AgentExecutor",
    "AgentResult",
    "CLIMATE_TOOLS",
    "ToolCall",
    "ToolDefinition",
    "create_climate_agent",
]
