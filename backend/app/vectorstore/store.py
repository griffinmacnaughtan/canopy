"""In-memory vector store with cosine similarity search.

Designed for fast prototyping and small-to-medium corpora (< 100k chunks).
For production scale, swap with pgvector or a dedicated vector database
while keeping the same ``VectorStore`` interface.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from threading import Lock

import numpy as np

from .chunker import Chunk
from .embeddings import EmbeddingProvider, get_embedding_provider


@dataclass
class Document:
    """A stored document with its embedding vector."""

    id: str
    text: str
    source: str
    metadata: dict = field(default_factory=dict)
    embedding: np.ndarray | None = None


@dataclass
class SearchResult:
    """A search result with relevance score."""

    document: Document
    score: float  # cosine similarity, 0-1


class VectorStore:
    """Thread-safe in-memory vector store.

    Stores document chunks with their embedding vectors and supports
    cosine-similarity search for RAG retrieval.
    """

    def __init__(self, embedding_provider: EmbeddingProvider | None = None) -> None:
        self._provider = embedding_provider or get_embedding_provider()
        self._documents: dict[str, Document] = {}
        self._lock = Lock()
        # Cached numpy matrix for batch similarity — rebuilt on mutation
        self._matrix: np.ndarray | None = None
        self._matrix_ids: list[str] = []

    @property
    def size(self) -> int:
        """Number of documents in the store."""
        return len(self._documents)

    def _invalidate_cache(self) -> None:
        self._matrix = None
        self._matrix_ids = []

    def _build_matrix(self) -> None:
        """Build the embedding matrix for batch similarity search."""
        if self._matrix is not None:
            return
        if not self._documents:
            self._matrix = np.zeros((0, self._provider.dimension), dtype=np.float32)
            self._matrix_ids = []
            return

        ids = []
        vectors = []
        for doc_id, doc in self._documents.items():
            if doc.embedding is not None:
                ids.append(doc_id)
                vectors.append(doc.embedding)

        if vectors:
            self._matrix = np.stack(vectors)
            self._matrix_ids = ids
        else:
            self._matrix = np.zeros((0, self._provider.dimension), dtype=np.float32)
            self._matrix_ids = []

    async def add_chunks(
        self,
        chunks: list[Chunk],
        metadata: dict | None = None,
    ) -> list[str]:
        """Embed and store a list of text chunks.

        Args:
            chunks: Chunks from the document chunker.
            metadata: Optional metadata attached to every chunk.

        Returns:
            List of document IDs for the stored chunks.
        """
        if not chunks:
            return []

        texts = [c.text for c in chunks]
        embeddings = await self._provider.embed(texts)

        ids = []
        with self._lock:
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                doc_id = str(uuid.uuid4())
                doc = Document(
                    id=doc_id,
                    text=chunk.text,
                    source=chunk.source,
                    metadata={
                        "chunk_index": chunk.index,
                        "char_offset": chunk.char_offset,
                        **(metadata or {}),
                    },
                    embedding=embedding,
                )
                self._documents[doc_id] = doc
                ids.append(doc_id)
            self._invalidate_cache()

        return ids

    async def add_text(
        self,
        text: str,
        source: str = "inline",
        metadata: dict | None = None,
    ) -> str:
        """Embed and store a single text string (no chunking).

        Returns:
            The document ID.
        """
        embedding = await self._provider.embed_single(text)
        doc_id = str(uuid.uuid4())
        doc = Document(
            id=doc_id,
            text=text,
            source=source,
            metadata=metadata or {},
            embedding=embedding,
        )
        with self._lock:
            self._documents[doc_id] = doc
            self._invalidate_cache()
        return doc_id

    async def search(
        self,
        query: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> list[SearchResult]:
        """Semantic similarity search.

        Args:
            query: The search query text.
            top_k: Maximum number of results.
            min_score: Minimum cosine similarity threshold.

        Returns:
            Sorted list of ``SearchResult`` (highest score first).
        """
        if not self._documents:
            return []

        query_embedding = await self._provider.embed_single(query)

        with self._lock:
            self._build_matrix()
            if self._matrix is None or len(self._matrix) == 0:
                return []

            # Cosine similarity via normalised dot product
            query_norm = query_embedding / (np.linalg.norm(query_embedding) + 1e-10)
            norms = np.linalg.norm(self._matrix, axis=1, keepdims=True) + 1e-10
            matrix_norm = self._matrix / norms
            similarities = matrix_norm @ query_norm

            # Top-k selection
            k = min(top_k, len(similarities))
            top_indices = np.argpartition(similarities, -k)[-k:]
            top_indices = top_indices[np.argsort(similarities[top_indices])[::-1]]

            results = []
            for idx in top_indices:
                score = float(similarities[idx])
                if score < min_score:
                    continue
                doc_id = self._matrix_ids[idx]
                results.append(
                    SearchResult(
                        document=self._documents[doc_id],
                        score=score,
                    )
                )

        return results

    def clear(self) -> None:
        """Remove all documents from the store."""
        with self._lock:
            self._documents.clear()
            self._invalidate_cache()

    def remove(self, doc_id: str) -> bool:
        """Remove a single document by ID."""
        with self._lock:
            if doc_id in self._documents:
                del self._documents[doc_id]
                self._invalidate_cache()
                return True
        return False


# ── Singleton ────────────────────────────────────────────────────────────

_store: VectorStore | None = None


def get_vector_store() -> VectorStore:
    """Get or create the global vector store singleton."""
    global _store
    if _store is None:
        _store = VectorStore()
    return _store
