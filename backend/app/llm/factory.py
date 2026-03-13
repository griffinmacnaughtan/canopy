"""Factory for creating LLM clients."""

from typing import Optional

from ..config import get_settings
from .base import LLMClient
from .openai_client import OpenAIClient
from .anthropic_client import AnthropicClient


def get_llm_client(provider: Optional[str] = None) -> LLMClient:
    """Get an LLM client based on configuration.

    Args:
        provider: Optional provider override ('anthropic' or 'openai').
                  If not specified, uses the configured default.

    Returns:
        An LLM client instance.

    Raises:
        ValueError: If the provider is not supported.
    """
    settings = get_settings()
    provider = provider or settings.llm_provider

    if provider == "anthropic":
        return AnthropicClient()
    elif provider == "openai":
        return OpenAIClient()
    else:
        raise ValueError(f"Unsupported LLM provider: {provider}")
