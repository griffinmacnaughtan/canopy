"""Document chunking for vector store ingestion.

Splits documents into overlapping chunks to preserve context across
chunk boundaries — critical for retrieval quality when the query
references information that spans a paragraph break.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Chunk:
    """A text chunk with provenance metadata."""

    text: str
    source: str  # filename or document id
    index: int  # chunk ordinal within the source
    char_offset: int  # character offset in the original document


def chunk_text(
    text: str,
    source: str = "unknown",
    chunk_size: int = 512,
    chunk_overlap: int = 64,
) -> list[Chunk]:
    """Split *text* into overlapping chunks.

    Uses a sentence-aware splitting strategy: it tries to break at sentence
    boundaries (`. `, `\\n`) that fall within the target window so that
    chunks are semantically coherent.

    Args:
        text: The full document text.
        source: Identifier for the source document.
        chunk_size: Target number of characters per chunk.
        chunk_overlap: Number of characters to overlap between consecutive chunks.

    Returns:
        Ordered list of ``Chunk`` objects.
    """
    if not text or not text.strip():
        return []

    chunks: list[Chunk] = []
    start = 0
    idx = 0

    while start < len(text):
        end = min(start + chunk_size, len(text))

        # Try to break at a sentence boundary within the last 20% of the chunk
        if end < len(text):
            search_start = start + int(chunk_size * 0.8)
            best_break = -1
            for sep in (". ", ".\n", "\n\n", "\n", "; "):
                pos = text.rfind(sep, search_start, end)
                if pos != -1:
                    best_break = pos + len(sep)
                    break
            if best_break > start:
                end = best_break

        chunk_text_str = text[start:end].strip()
        if chunk_text_str:
            chunks.append(
                Chunk(
                    text=chunk_text_str,
                    source=source,
                    index=idx,
                    char_offset=start,
                )
            )
            idx += 1

        # If we consumed to the end, stop
        if end >= len(text):
            break

        # Advance with overlap
        start = end - chunk_overlap

    return chunks
