"""Ingestion pipeline: load SEC filing excerpts, chunk, embed, store.

Connects the static 10-K climate risk excerpts in ``data/filings/`` to
the vector store via the existing chunker and embedding providers.
"""

from __future__ import annotations

from pathlib import Path

import structlog

from ..vectorstore import get_vector_store
from ..vectorstore.chunker import chunk_text
from ..vectorstore.store import VectorStore
from .sec_filings import get_all_filing_paths, load_filing_from_disk

logger = structlog.get_logger()


async def ingest_filing(filepath: Path, store: VectorStore) -> int:
    """Load a single filing excerpt, chunk it, and add to the vector store.

    Args:
        filepath: Path to a ``.txt`` filing excerpt.
        store: Target vector store instance.

    Returns:
        Number of chunks added.
    """
    body, metadata = load_filing_from_disk(filepath)

    if not body:
        logger.warning("empty_filing", file=filepath.name)
        return 0

    company = metadata.get("Company", "Unknown")
    source = f"{company} ({metadata.get('Filing', '10-K')})"

    chunks = chunk_text(body, source=source, chunk_size=1024, chunk_overlap=128)

    chunk_metadata = {
        "company": company,
        "ticker": metadata.get("Ticker", ""),
        "filing_type": metadata.get("Filing", "10-K"),
        "section": metadata.get("Section", "Item 1A - Risk Factors"),
        "filing_date": metadata.get("Filing Date", ""),
        "source_file": filepath.name,
        "data_source": "SEC EDGAR",
    }

    ids = await store.add_chunks(chunks, metadata=chunk_metadata)

    logger.info(
        "filing_ingested",
        company=company,
        chunks=len(ids),
        chars=len(body),
    )
    return len(ids)


async def ingest_all_filings(
    store: VectorStore | None = None,
) -> dict:
    """Ingest all static filing excerpts into the vector store.

    Args:
        store: Vector store instance.  Defaults to the global singleton.

    Returns:
        Summary dict with total chunks, files processed, and per-file counts.
    """
    if store is None:
        store = get_vector_store()

    paths = get_all_filing_paths()
    if not paths:
        logger.warning("no_filings_found")
        return {"total_chunks": 0, "files_processed": 0, "per_file": {}}

    per_file: dict[str, int] = {}
    total = 0

    for path in paths:
        count = await ingest_filing(path, store)
        per_file[path.name] = count
        total += count

    logger.info(
        "all_filings_ingested",
        files=len(paths),
        total_chunks=total,
    )

    return {
        "total_chunks": total,
        "files_processed": len(paths),
        "per_file": per_file,
    }


async def seed_vector_store() -> dict:
    """Clear and re-seed the global vector store with filing excerpts.

    On startup this first attempts to fetch **live** filings from SEC
    EDGAR (EFTS full-text search → filing download → HTML parsing).
    Successfully fetched filings are cached as .txt files alongside the
    static excerpts so that subsequent restarts are instant.

    If the live fetch fails or returns nothing the existing static files
    are used as a fallback.

    Returns:
        Summary dict from :func:`ingest_all_filings`.
    """
    # Attempt live EDGAR fetch — results are cached to disk
    try:
        from .sec_filings import fetch_live_filings

        live_results = await fetch_live_filings()
        logger.info("live_sec_filings_fetched", count=len(live_results))
    except Exception as exc:
        logger.warning("live_sec_filings_skipped", error=str(exc))

    store = get_vector_store()
    store.clear()
    return await ingest_all_filings(store)
