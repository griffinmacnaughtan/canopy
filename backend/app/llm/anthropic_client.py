"""Anthropic LLM client implementation."""

from collections.abc import AsyncIterator

from anthropic import AsyncAnthropic

from ..config import get_settings
from .base import LLMClient, LLMResponse


class AnthropicClient(LLMClient):
    """Anthropic Claude API client with streaming support."""

    def __init__(self, api_key: str | None = None, model: str | None = None):
        settings = get_settings()
        self.api_key = api_key or settings.anthropic_api_key
        self.model = model or settings.anthropic_model
        self.client = AsyncAnthropic(api_key=self.api_key)

    async def complete(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> LLMResponse:
        """Generate a completion using Anthropic Claude."""
        formatted_messages = self._format_messages(messages)

        response = await self.client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=formatted_messages,
        )

        content = ""
        for block in response.content:
            if block.type == "text":
                content += block.text

        return LLMResponse(
            content=content,
            model=response.model,
            usage={
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
            },
        )

    async def stream(
        self,
        messages: list[dict],
        system_prompt: str | None = None,
        max_tokens: int = 2048,
        temperature: float = 0.7,
    ) -> AsyncIterator[str]:
        """Stream a completion using Anthropic Claude."""
        formatted_messages = self._format_messages(messages)

        async with self.client.messages.stream(
            model=self.model,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_prompt or "",
            messages=formatted_messages,
        ) as stream:
            async for text in stream.text_stream:
                yield text

    def count_tokens(self, text: str) -> int:
        """Estimate token count for Anthropic models.

        Anthropic doesn't provide a public tokenizer, so we estimate
        based on the ~4 characters per token rule of thumb.
        """
        return len(text) // 4 + 1

    def _format_messages(self, messages: list[dict]) -> list[dict]:
        """Format messages for Anthropic API."""
        formatted = []

        for msg in messages:
            role = msg.get("role", "user")
            # Anthropic only accepts 'user' and 'assistant' roles
            if role == "system":
                continue  # System messages are handled separately
            if role not in ("user", "assistant"):
                role = "user"

            formatted.append(
                {
                    "role": role,
                    "content": msg.get("content", ""),
                }
            )

        return formatted
