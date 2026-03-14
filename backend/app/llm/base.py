"""Abstract base class for LLM clients."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from dataclasses import dataclass


@dataclass
class LLMResponse:
    """Response from an LLM completion."""

    content: str
    model: str
    usage: dict | None = None


class LLMClient(ABC):
    """Abstract base class for LLM integrations."""

    @abstractmethod
    async def complete(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a completion from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            system_prompt: Optional system prompt to prepend.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0-1).

        Returns:
            LLMResponse with the generated content.
        """
        pass

    @abstractmethod
    async def stream(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream a completion from the LLM.

        Args:
            messages: List of message dicts with 'role' and 'content' keys.
            system_prompt: Optional system prompt to prepend.
            max_tokens: Maximum tokens in the response.
            temperature: Sampling temperature (0-1).

        Yields:
            Text chunks as they are generated.
        """
        pass

    @abstractmethod
    def count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string.

        Args:
            text: The text to count tokens for.

        Returns:
            Number of tokens.
        """
        pass
