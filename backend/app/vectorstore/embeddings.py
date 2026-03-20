"""Embedding providers for vector store.

Supports OpenAI text-embedding-3-small (production) and a lightweight
hash-based fallback for testing and offline development.
"""

from __future__ import annotations

import hashlib
from abc import ABC, abstractmethod
from functools import lru_cache

import numpy as np


class EmbeddingProvider(ABC):
    """Abstract embedding provider."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Dimensionality of the embedding vectors."""

    @abstractmethod
    async def embed(self, texts: list[str]) -> np.ndarray:
        """Embed a batch of texts.

        Args:
            texts: List of strings to embed.

        Returns:
            2-D numpy array of shape ``(len(texts), self.dimension)``.
        """

    async def embed_single(self, text: str) -> np.ndarray:
        """Convenience wrapper for a single text."""
        result = await self.embed([text])
        return result[0]


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI text-embedding-3-small provider.

    Uses the OpenAI API to generate 1536-dimensional embeddings
    optimised for semantic similarity and retrieval tasks.
    """

    MODEL = "text-embedding-3-small"
    DIMENSION = 1536

    def __init__(self, api_key: str | None = None) -> None:
        import openai

        self._client = openai.AsyncOpenAI(api_key=api_key)

    @property
    def dimension(self) -> int:
        return self.DIMENSION

    async def embed(self, texts: list[str]) -> np.ndarray:
        response = await self._client.embeddings.create(
            input=texts,
            model=self.MODEL,
        )
        vectors = [item.embedding for item in response.data]
        return np.array(vectors, dtype=np.float32)


class HashEmbeddingProvider(EmbeddingProvider):
    """Deterministic hash-based embeddings for testing.

    Produces consistent 128-dimensional vectors by hashing text content.
    NOT suitable for production — semantic similarity is approximate at
    best — but useful for unit tests and offline development.
    """

    DIMENSION = 128

    @property
    def dimension(self) -> int:
        return self.DIMENSION

    async def embed(self, texts: list[str]) -> np.ndarray:
        vectors = []
        for text in texts:
            # Use multiple hashes to fill 128 dimensions with values in [-1, 1]
            parts = []
            for i in range(4):
                seed = f"{i}:{text}".encode()
                digest = hashlib.sha256(seed).digest()
                # 32 bytes → 32 uint8 values, scaled to [-1, 1]
                vals = np.frombuffer(digest, dtype=np.uint8).astype(np.float32)
                parts.append((vals / 127.5) - 1.0)
            vec = np.concatenate(parts)[: self.DIMENSION]
            # L2-normalise so cosine similarity works correctly
            norm = np.linalg.norm(vec)
            if norm > 0:
                vec = vec / norm
            vectors.append(vec)
        return np.array(vectors, dtype=np.float32)


@lru_cache
def get_embedding_provider(provider: str = "hash") -> EmbeddingProvider:
    """Factory for embedding providers.

    Args:
        provider: ``"openai"`` for production or ``"hash"`` for testing.

    Returns:
        An ``EmbeddingProvider`` instance.
    """
    if provider == "openai":
        from ..config import get_settings

        settings = get_settings()
        return OpenAIEmbeddingProvider(api_key=settings.openai_api_key)
    return HashEmbeddingProvider()
