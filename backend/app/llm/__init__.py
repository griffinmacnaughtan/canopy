"""LLM integration module for ESG Copilot."""

from .base import LLMClient, LLMResponse
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient
from .prompts import SYSTEM_PROMPT, build_portfolio_context
from .factory import get_llm_client

__all__ = [
    "LLMClient",
    "LLMResponse",
    "OpenAIClient",
    "AnthropicClient",
    "SYSTEM_PROMPT",
    "build_portfolio_context",
    "get_llm_client",
]
