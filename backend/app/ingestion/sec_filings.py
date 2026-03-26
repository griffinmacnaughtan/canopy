"""SEC EDGAR filing loader.

Loads 10-K climate risk excerpts from two sources:

1. **Live EDGAR EFTS** — the :class:`SECEdgarExtractor` searches the SEC
   full-text search API, downloads filings, and extracts climate risk
   sections via HTML parsing.  Results are cached as ``.txt`` files in
   ``backend/data/filings/`` so subsequent restarts are instant.

2. **Static fallback** — if the live fetch is unavailable (no network,
   rate-limited, etc.) the loader falls back to pre-downloaded excerpts
   already on disk.

SEC EDGAR EFTS API reference:
    - Base URL: ``https://efts.sec.gov/LATEST/search-index``
    - No authentication required; only a descriptive ``User-Agent`` header
    - Rate limit: 10 requests / second
"""

from __future__ import annotations

import re
from pathlib import Path

import structlog

logger = structlog.get_logger()

# Static filings live alongside the SQLite database
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "filings"


def get_all_filing_paths() -> list[Path]:
    """Return paths to all filing excerpts (both static and live-fetched).

    Returns:
        Sorted list of ``.txt`` file paths in ``data/filings/``.
    """
    if not _DATA_DIR.exists():
        logger.warning("filing_directory_missing", path=str(_DATA_DIR))
        return []
    return sorted(_DATA_DIR.glob("*.txt"))


def load_filing_from_disk(filepath: Path) -> tuple[str, dict[str, str]]:
    """Read a filing excerpt and parse its metadata header.

    Each filing file starts with a YAML-style metadata block separated
    from the body by a ``---`` line::

        Company: Exxon Mobil Corporation
        Ticker: XOM
        Filing: 10-K Annual Report
        ---
        (body text)

    Args:
        filepath: Path to a ``.txt`` filing excerpt.

    Returns:
        ``(body_text, metadata_dict)``
    """
    raw = filepath.read_text(encoding="utf-8")

    metadata: dict[str, str] = {}
    body_lines: list[str] = []
    in_header = True

    for line in raw.splitlines():
        if in_header:
            stripped = line.strip()
            if stripped == "---":
                in_header = False
                continue
            if ":" in stripped:
                key, _, value = stripped.partition(":")
                metadata[key.strip()] = value.strip()
        else:
            body_lines.append(line)

    body = "\n".join(body_lines).strip()
    logger.debug(
        "filing_loaded",
        file=filepath.name,
        company=metadata.get("Company", "Unknown"),
        chars=len(body),
    )
    return body, metadata


def _ticker_to_filename(ticker: str) -> str:
    """Convert a ticker symbol to a safe filename slug."""
    return re.sub(r"[^a-z0-9]", "_", ticker.lower())


async def fetch_live_filings() -> list[dict]:
    """Fetch live filings from SEC EDGAR for all tracked companies.

    Downloads 10-K/20-F climate risk sections and caches them as .txt
    files in the data/filings directory so the vector store can ingest
    them alongside any pre-existing static files.

    Returns:
        List of dicts with filing metadata for each successful fetch.
    """
    from ..pipeline.config import PipelineConfig
    from ..pipeline.extractors.sec_edgar import SECEdgarExtractor

    config = PipelineConfig.from_env()
    extractor = SECEdgarExtractor(config)

    if not await extractor.health_check():
        logger.warning("sec_edgar_unavailable", msg="Falling back to static filings")
        return []

    result = await extractor.extract()
    saved: list[dict] = []

    _DATA_DIR.mkdir(parents=True, exist_ok=True)

    for record in result.records:
        ticker = record["ticker"]
        company = record["company"]
        text = record["text"]
        form_type = record.get("form_type", "10-K")
        filing_date = record.get("filing_date", "")
        cik = record.get("cik", "")

        # Build the same metadata header format as static files
        header = (
            f"Company: {company}\n"
            f"Ticker: {ticker}\n"
            f"Filing: {form_type} Annual Report\n"
            f"Section: Item 1A - Risk Factors (Climate-Related Excerpts)\n"
            f"Filing Date: {filing_date}\n"
            f"Source: SEC EDGAR (CIK: {cik})\n"
            f"---\n"
        )

        slug = _ticker_to_filename(ticker)
        filepath = _DATA_DIR / f"{slug}_10k_climate_risks.txt"
        filepath.write_text(header + text, encoding="utf-8")

        saved.append(
            {
                "ticker": ticker,
                "company": company,
                "filepath": str(filepath),
                "chars": len(text),
            }
        )

        logger.info(
            "live_filing_saved",
            ticker=ticker,
            company=company,
            chars=len(text),
            path=filepath.name,
        )

    logger.info(
        "live_filings_complete",
        fetched=len(result.records),
        saved=len(saved),
        errors=len(result.errors),
    )

    return saved
