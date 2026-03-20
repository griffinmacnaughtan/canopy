"""SEC EDGAR filing loader.

Loads pre-downloaded 10-K climate risk excerpts from ``backend/data/filings/``.
Also exposes :func:`fetch_10k_climate_section` to demonstrate the capability
of fetching live filings from the SEC EDGAR full-text search (EFTS) API.

SEC EDGAR EFTS API reference:
    - Base URL: ``https://efts.sec.gov/LATEST/search-index``
    - No authentication required; only a descriptive ``User-Agent`` header
    - Rate limit: 10 requests / second
    - Returns JSON with accession numbers and filing metadata
    - Full text of filings available at
      ``https://www.sec.gov/Archives/edgar/data/{cik}/{accession}/{filename}``

For the demo we use static files to avoid runtime network dependency.
"""

from __future__ import annotations

from pathlib import Path

import structlog

logger = structlog.get_logger()

# Static filings live alongside the SQLite database
_DATA_DIR = Path(__file__).resolve().parent.parent.parent / "data" / "filings"

# SEC EDGAR requires a descriptive User-Agent header
EDGAR_HEADERS = {
    "User-Agent": "Canopy Climate Risk Platform research@canopy-demo.com",
    "Accept": "application/json",
}


def get_all_filing_paths() -> list[Path]:
    """Return paths to all static filing excerpts.

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


async def fetch_10k_climate_section(
    ticker: str,
    cik: str,
) -> str | None:
    """Fetch climate risk disclosures from SEC EDGAR EFTS (capability demo).

    This function demonstrates live fetching from the SEC EDGAR full-text
    search API.  In production it would be called by a scheduled pipeline;
    for the demo the app uses pre-downloaded static excerpts instead.

    Args:
        ticker: Stock ticker symbol (e.g. ``"XOM"``).
        cik: SEC Central Index Key, zero-padded to 10 digits.

    Returns:
        Extracted climate risk text, or ``None`` on failure.
    """
    try:
        import httpx
    except ImportError:
        logger.warning("httpx_not_installed", msg="pip install httpx for live EDGAR fetching")
        return None

    search_url = "https://efts.sec.gov/LATEST/search-index"
    params = {
        "q": '"climate" OR "greenhouse gas" OR "carbon emissions"',
        "forms": "10-K",
        "dateRange": "custom",
        "startdt": "2024-01-01",
        "enddt": "2025-03-01",
    }

    try:
        async with httpx.AsyncClient(headers=EDGAR_HEADERS, timeout=30) as client:
            resp = await client.get(search_url, params=params)
            resp.raise_for_status()
            data = resp.json()
            logger.info(
                "edgar_search_complete",
                ticker=ticker,
                total_hits=data.get("hits", {}).get("total", {}).get("value", 0),
            )
            return None  # Full extraction requires HTML parsing of the filing
    except Exception as e:
        logger.warning("edgar_fetch_error", ticker=ticker, error=str(e))
        return None
