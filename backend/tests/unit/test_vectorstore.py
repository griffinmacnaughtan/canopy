"""Tests for the vector store, chunker, and embedding providers."""

import numpy as np
import pytest

from app.vectorstore.chunker import Chunk, chunk_text
from app.vectorstore.embeddings import HashEmbeddingProvider
from app.vectorstore.store import VectorStore

# ── Chunker tests ────────────────────────────────────────────────────────


class TestChunker:
    def test_empty_text_returns_no_chunks(self):
        assert chunk_text("") == []
        assert chunk_text("   ") == []

    def test_short_text_single_chunk(self):
        chunks = chunk_text("Hello world.", source="test.txt", chunk_size=512)
        assert len(chunks) == 1
        assert chunks[0].text == "Hello world."
        assert chunks[0].source == "test.txt"
        assert chunks[0].index == 0

    def test_long_text_multiple_chunks(self):
        text = "A" * 1500
        chunks = chunk_text(text, chunk_size=512, chunk_overlap=64)
        assert len(chunks) > 1
        # All chunks should be non-empty
        assert all(c.text for c in chunks)
        # Indices should be sequential
        assert [c.index for c in chunks] == list(range(len(chunks)))

    def test_sentence_boundary_splitting(self):
        # Build text with clear sentence boundaries
        sentences = [f"Sentence number {i} is here." for i in range(20)]
        text = " ".join(sentences)
        chunks = chunk_text(text, chunk_size=100, chunk_overlap=20)
        # Chunks should not cut words in half at sentence boundaries
        for chunk in chunks:
            assert not chunk.text.startswith(" ")

    def test_chunk_overlap(self):
        text = "ABCDEFGHIJ" * 100  # 1000 chars
        chunks = chunk_text(text, chunk_size=200, chunk_overlap=50)
        # With overlap, consecutive chunks should share some content
        assert len(chunks) >= 4

    def test_source_preserved(self):
        chunks = chunk_text("Test content.", source="report.pdf")
        assert chunks[0].source == "report.pdf"

    def test_char_offset_tracking(self):
        chunks = chunk_text("Hello world. " * 100, chunk_size=50, chunk_overlap=10)
        # First chunk should start at offset 0
        assert chunks[0].char_offset == 0
        # Subsequent chunks should have increasing offsets
        for i in range(1, len(chunks)):
            assert chunks[i].char_offset > chunks[i - 1].char_offset


# ── Embedding provider tests ────────────────────────────────────────────


class TestHashEmbeddingProvider:
    @pytest.fixture
    def provider(self):
        return HashEmbeddingProvider()

    @pytest.mark.asyncio
    async def test_dimension(self, provider):
        assert provider.dimension == 128

    @pytest.mark.asyncio
    async def test_single_embedding(self, provider):
        result = await provider.embed_single("hello world")
        assert result.shape == (128,)
        assert result.dtype == np.float32

    @pytest.mark.asyncio
    async def test_batch_embedding(self, provider):
        result = await provider.embed(["hello", "world", "test"])
        assert result.shape == (3, 128)

    @pytest.mark.asyncio
    async def test_deterministic(self, provider):
        a = await provider.embed_single("same text")
        b = await provider.embed_single("same text")
        np.testing.assert_array_equal(a, b)

    @pytest.mark.asyncio
    async def test_different_texts_different_embeddings(self, provider):
        a = await provider.embed_single("climate risk")
        b = await provider.embed_single("quantum physics")
        assert not np.array_equal(a, b)

    @pytest.mark.asyncio
    async def test_normalized(self, provider):
        result = await provider.embed_single("test normalization")
        norm = np.linalg.norm(result)
        assert abs(norm - 1.0) < 0.01


# ── Vector store tests ───────────────────────────────────────────────────


class TestVectorStore:
    @pytest.fixture
    def store(self):
        provider = HashEmbeddingProvider()
        return VectorStore(embedding_provider=provider)

    @pytest.mark.asyncio
    async def test_empty_store(self, store):
        assert store.size == 0
        results = await store.search("anything")
        assert results == []

    @pytest.mark.asyncio
    async def test_add_text(self, store):
        doc_id = await store.add_text("climate risk analysis", source="test")
        assert store.size == 1
        assert isinstance(doc_id, str)

    @pytest.mark.asyncio
    async def test_add_chunks(self, store):
        chunks = [
            Chunk(text="carbon emissions data", source="report.pdf", index=0, char_offset=0),
            Chunk(text="transition risk factors", source="report.pdf", index=1, char_offset=50),
        ]
        ids = await store.add_chunks(chunks)
        assert len(ids) == 2
        assert store.size == 2

    @pytest.mark.asyncio
    async def test_search_returns_results(self, store):
        await store.add_text("climate change and carbon emissions", source="a")
        await store.add_text("portfolio risk assessment", source="b")
        await store.add_text("machine learning algorithms", source="c")

        # Search for exact stored text — hash embeddings are deterministic
        # so the same text will have cosine similarity of 1.0
        results = await store.search("climate change and carbon emissions", top_k=3)
        assert len(results) >= 1
        # The exact match should have high similarity
        assert results[0].score > 0.9
        # Results should be sorted by score descending
        for i in range(len(results) - 1):
            assert results[i].score >= results[i + 1].score

    @pytest.mark.asyncio
    async def test_search_top_k(self, store):
        for i in range(10):
            await store.add_text(f"document number {i}", source=f"doc_{i}")

        results = await store.search("document", top_k=3)
        assert len(results) <= 3

    @pytest.mark.asyncio
    async def test_search_min_score(self, store):
        await store.add_text("relevant content", source="a")
        results = await store.search("relevant content", min_score=0.99)
        # Very high threshold should filter most results
        assert all(r.score >= 0.99 for r in results)

    @pytest.mark.asyncio
    async def test_clear(self, store):
        await store.add_text("some text", source="a")
        assert store.size == 1
        store.clear()
        assert store.size == 0

    @pytest.mark.asyncio
    async def test_remove(self, store):
        doc_id = await store.add_text("to be removed", source="a")
        assert store.size == 1
        assert store.remove(doc_id) is True
        assert store.size == 0

    @pytest.mark.asyncio
    async def test_remove_nonexistent(self, store):
        assert store.remove("nonexistent-id") is False

    @pytest.mark.asyncio
    async def test_metadata_preserved(self, store):
        chunks = [
            Chunk(text="test chunk", source="report.pdf", index=0, char_offset=0),
        ]
        await store.add_chunks(chunks, metadata={"portfolio_id": "p1"})
        results = await store.search("test chunk")
        assert results[0].document.metadata.get("portfolio_id") == "p1"
        assert results[0].document.metadata.get("chunk_index") == 0

    @pytest.mark.asyncio
    async def test_add_empty_chunks(self, store):
        ids = await store.add_chunks([])
        assert ids == []
        assert store.size == 0

    @pytest.mark.asyncio
    async def test_search_metadata_filter(self, store):
        # Use identical text so hash embeddings produce the same vector —
        # guaranteeing both pass min_score regardless of query wording.
        text = "carbon disclosure report"
        await store.add_text(text, source="a", metadata={"company": "Apple Inc."})
        await store.add_text(text, source="b", metadata={"company": "Shell plc"})

        # Without filter — both candidates (identical embeddings → same score)
        all_results = await store.search(text, top_k=5)
        assert len(all_results) == 2

        # With filter — only Apple
        filtered = await store.search(text, top_k=5, metadata_filter={"company": "Apple Inc."})
        assert len(filtered) == 1
        assert filtered[0].document.metadata["company"] == "Apple Inc."

    @pytest.mark.asyncio
    async def test_search_metadata_filter_no_match(self, store):
        await store.add_text("some text", source="a", metadata={"company": "X"})
        results = await store.search("some text", metadata_filter={"company": "NonExistent"})
        # All candidates masked to -1.0 and filtered by min_score default (0.0)
        assert results == []
