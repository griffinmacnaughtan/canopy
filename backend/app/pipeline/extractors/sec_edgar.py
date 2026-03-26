"""SEC EDGAR EFTS live filing extractor.

Fetches climate-related 10-K / 20-F filings from SEC EDGAR full-text search,
downloads the filing documents, and extracts climate risk sections.

API reference:
    - EFTS search: https://efts.sec.gov/LATEST/search-index
    - No authentication required; descriptive User-Agent header mandatory
    - Rate limit: 10 requests/second
"""

from __future__ import annotations

import asyncio
import re
from datetime import datetime
from html.parser import HTMLParser
from typing import Any

import httpx
import structlog

from ..config import PipelineConfig
from .base import BaseExtractor, ExtractionResult

logger = structlog.get_logger()

# CIK numbers for the seed-data companies (zero-padded to 10 digits).
# Expand this mapping when adding new companies to the platform.
COMPANY_CIKS: dict[str, dict[str, str]] = {
    "AAPL": {"cik": "0000320193", "name": "Apple Inc."},
    "MSFT": {"cik": "0000789019", "name": "Microsoft Corporation"},
    "GOOGL": {"cik": "0001652044", "name": "Alphabet Inc."},
    "NVDA": {"cik": "0001045810", "name": "NVIDIA Corporation"},
    "TSLA": {"cik": "0001318605", "name": "Tesla, Inc."},
    "XOM": {"cik": "0000034088", "name": "Exxon Mobil Corporation"},
    "CVX": {"cik": "0000093410", "name": "Chevron Corporation"},
    "NEE": {"cik": "0000753308", "name": "NextEra Energy, Inc."},
    "SHEL": {"cik": "0001306965", "name": "Shell plc"},
    "TTE": {"cik": "0000878560", "name": "TotalEnergies SE"},
    "CAT": {"cik": "0000018230", "name": "Caterpillar Inc."},
    "BASFY": {"cik": "0001004155", "name": "BASF SE"},
    "BHP": {"cik": "0000811809", "name": "BHP Group Limited"},
    "JPM": {"cik": "0000019617", "name": "JPMorgan Chase & Co."},
    "BLK": {"cik": "0001364742", "name": "BlackRock, Inc."},
    "UL": {"cik": "0000217410", "name": "Unilever PLC"},
    "NSRGY": {"cik": "0000070866", "name": "Nestlé S.A."},
    "JNJ": {"cik": "0000200406", "name": "Johnson & Johnson"},
    "TM": {"cik": "0001094517", "name": "Toyota Motor Corporation"},
    "005930.KS": {"cik": "0000805676", "name": "Samsung Electronics Co."},
}

# Climate-related keywords for EFTS full-text search
_CLIMATE_QUERY = (
    '"climate change" OR "greenhouse gas" OR "carbon emissions" '
    'OR "climate risk" OR "net zero"'
)

# Regex patterns for extracting Item 1A from HTML filings
_ITEM_1A_START = re.compile(
    r"item\s+1a[\.\s\—\-]*risk\s+factors",
    re.IGNORECASE,
)
_ITEM_1B_START = re.compile(
    r"item\s+1b[\.\s\—\-]*unresolved\s+staff\s+comments",
    re.IGNORECASE,
)


class _HTMLTextExtractor(HTMLParser):
    """Minimal HTML-to-text converter for SEC filing documents."""

    def __init__(self) -> None:
        super().__init__()
        self._pieces: list[str] = []
        self._skip = False

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag in ("script", "style"):
            self._skip = True

    def handle_endtag(self, tag: str) -> None:
        if tag in ("script", "style"):
            self._skip = False
        if tag in ("p", "div", "br", "tr", "li", "h1", "h2", "h3", "h4"):
            self._pieces.append("\n")

    def handle_data(self, data: str) -> None:
        if not self._skip:
            self._pieces.append(data)

    def get_text(self) -> str:
        raw = "".join(self._pieces)
        # Collapse excessive whitespace while preserving paragraph breaks
        raw = re.sub(r"[ \t]+", " ", raw)
        raw = re.sub(r"\n{3,}", "\n\n", raw)
        return raw.strip()


def _html_to_text(html: str) -> str:
    """Convert HTML to plain text."""
    parser = _HTMLTextExtractor()
    parser.feed(html)
    return parser.get_text()


def _extract_climate_section(text: str, max_chars: int = 15_000) -> str:
    """Extract Item 1A (Risk Factors) section and filter to climate content.

    Falls back to keyword-proximity extraction if section headers
    are not found (common in 20-F filings from non-US issuers).
    """
    # Try to find Item 1A boundaries
    start_match = _ITEM_1A_START.search(text)
    if start_match:
        section_start = start_match.start()
        end_match = _ITEM_1B_START.search(text, section_start + 100)
        section_end = end_match.start() if end_match else section_start + max_chars
        section = text[section_start:section_end]
    else:
        # Fallback: grab paragraphs containing climate keywords
        section = _keyword_extract(text)

    # Further filter to climate-relevant paragraphs
    paragraphs = section.split("\n\n")
    climate_keywords = {
        "climate", "carbon", "greenhouse", "emissions", "ghg",
        "net zero", "transition risk", "physical risk", "renewable",
        "decarboni", "paris agreement", "scope 1", "scope 2", "scope 3",
        "tcfd", "sustainability", "environmental",
    }
    relevant = []
    char_count = 0
    for para in paragraphs:
        lower = para.lower()
        if any(kw in lower for kw in climate_keywords):
            relevant.append(para.strip())
            char_count += len(para)
            if char_count >= max_chars:
                break

    return "\n\n".join(relevant) if relevant else section[:max_chars]


def _keyword_extract(text: str, window: int = 2000) -> str:
    """Extract text around climate keywords when section headers are absent."""
    keywords = ["climate change", "greenhouse gas", "carbon emissions", "climate risk"]
    chunks: list[str] = []
    seen_positions: set[int] = set()

    for kw in keywords:
        idx = 0
        while True:
            pos = text.lower().find(kw, idx)
            if pos == -1:
                break
            # Avoid overlapping windows
            bucket = pos // window
            if bucket not in seen_positions:
                seen_positions.add(bucket)
                start = max(0, pos - window // 2)
                end = min(len(text), pos + window // 2)
                chunks.append(text[start:end])
            idx = pos + len(kw)

    return "\n\n".join(chunks)


class SECEdgarExtractor(BaseExtractor):
    """Extract climate risk disclosures from SEC EDGAR 10-K/20-F filings.

    Uses the EDGAR Full-Text Search (EFTS) API to find filings, then
    downloads and parses the filing HTML to extract climate risk content.
    """

    def __init__(self, config: PipelineConfig):
        super().__init__(config)
        self.efts_url = config.sec_efts_base_url
        self.user_agent = config.sec_user_agent
        self.rate_limit = config.sec_rate_limit_seconds

    @property
    def source_name(self) -> str:
        return "SEC_EDGAR"

    def _headers(self) -> dict[str, str]:
        return {
            "User-Agent": self.user_agent,
            "Accept": "application/json",
        }

    async def health_check(self) -> bool:
        """Verify EFTS endpoint is reachable."""
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(
                    f"{self.efts_url}/search-index",
                    headers=self._headers(),
                    params={"q": "climate", "forms": "10-K", "from": "0", "size": "1"},
                )
                return resp.status_code == 200
        except Exception as e:
            self.logger.error("health_check_failed", error=str(e))
            return False

    async def extract(
        self,
        start_date: datetime | None = None,
        end_date: datetime | None = None,
        tickers: list[str] | None = None,
        **kwargs: Any,
    ) -> ExtractionResult:
        """Extract climate risk sections from 10-K/20-F filings.

        Args:
            start_date: Filing date range start (default: 18 months ago).
            end_date: Filing date range end (default: now).
            tickers: Stock tickers to fetch.  Defaults to all COMPANY_CIKS.

        Returns:
            ExtractionResult with one record per company filing.
        """
        if not end_date:
            end_date = datetime.utcnow()
        if not start_date:
            # Look back 18 months to catch the most recent annual filing.
            # Manual month arithmetic to avoid dateutil dependency.
            _m = end_date.month - 18
            _y = end_date.year
            while _m < 1:
                _m += 12
                _y -= 1
            start_date = datetime(_y, _m, 1)

        target_tickers = tickers or list(COMPANY_CIKS.keys())
        all_records: list[dict[str, Any]] = []
        errors: list[str] = []

        async with httpx.AsyncClient(
            timeout=self.config.request_timeout_seconds,
            headers=self._headers(),
        ) as client:
            for ticker in target_tickers:
                company = COMPANY_CIKS.get(ticker)
                if not company:
                    continue

                try:
                    record = await self._fetch_filing_for_company(
                        client,
                        ticker=ticker,
                        cik=company["cik"],
                        company_name=company["name"],
                        start_date=start_date,
                        end_date=end_date,
                    )
                    if record:
                        all_records.append(record)
                        self.logger.info(
                            "filing_extracted",
                            ticker=ticker,
                            chars=len(record.get("text", "")),
                        )
                    else:
                        self.logger.info("no_filing_found", ticker=ticker)
                except Exception as e:
                    msg = f"Failed to fetch filing for {ticker}: {e}"
                    errors.append(msg)
                    self.logger.warning("filing_extraction_failed", error=msg)

                # Respect SEC rate limit
                await asyncio.sleep(self.rate_limit)

        return ExtractionResult(
            source=self.source_name,
            records=all_records,
            watermark=end_date.isoformat(),
            metadata={
                "tickers_requested": len(target_tickers),
                "filings_found": len(all_records),
                "date_range": f"{start_date.date()} to {end_date.date()}",
            },
            errors=errors,
        )

    async def _fetch_filing_for_company(
        self,
        client: httpx.AsyncClient,
        ticker: str,
        cik: str,
        company_name: str,
        start_date: datetime,
        end_date: datetime,
    ) -> dict[str, Any] | None:
        """Search EFTS for a company's most recent 10-K/20-F, download and parse it."""

        # Step 1: Search EFTS for the most recent climate-related filing
        search_params = {
            "q": _CLIMATE_QUERY,
            "forms": "10-K,20-F",
            "dateRange": "custom",
            "startdt": start_date.strftime("%Y-%m-%d"),
            "enddt": end_date.strftime("%Y-%m-%d"),
            "from": "0",
            "size": "5",
        }

        # Search by CIK via the entity filter
        resp = await client.get(
            f"{self.efts_url}/search-index",
            params={**search_params, "q": f'"{company_name}" AND ({_CLIMATE_QUERY})'},
        )

        if resp.status_code != 200:
            self.logger.warning(
                "efts_search_error", ticker=ticker, status=resp.status_code
            )
            return None

        data = resp.json()
        hits = data.get("hits", {}).get("hits", [])
        if not hits:
            # Retry with simpler query
            resp = await client.get(
                f"{self.efts_url}/search-index",
                params={**search_params, "q": f'"{company_name}"'},
            )
            await asyncio.sleep(self.rate_limit)
            if resp.status_code == 200:
                data = resp.json()
                hits = data.get("hits", {}).get("hits", [])

        if not hits:
            return None

        # Step 2: Pick the most recent filing and get its document URL
        hit = hits[0]
        source_info = hit.get("_source", {})
        filing_url = source_info.get("file_path")
        filing_date = source_info.get("file_date", "")
        form_type = source_info.get("form_type", "10-K")

        if not filing_url:
            # Try the submissions API as fallback
            return await self._fetch_via_submissions(
                client, cik, company_name, ticker, form_type, filing_date
            )

        # Step 3: Download the filing document
        await asyncio.sleep(self.rate_limit)
        full_url = f"https://www.sec.gov/{filing_url}" if not filing_url.startswith("http") else filing_url
        doc_resp = await client.get(full_url)

        if doc_resp.status_code != 200:
            return None

        # Step 4: Parse HTML to extract climate risk content
        raw_text = _html_to_text(doc_resp.text) if "<html" in doc_resp.text.lower() else doc_resp.text
        climate_text = _extract_climate_section(raw_text)

        if len(climate_text) < 200:
            # Filing found but no meaningful climate content extracted
            return None

        return {
            "ticker": ticker,
            "company": company_name,
            "cik": cik,
            "form_type": form_type,
            "filing_date": filing_date,
            "text": climate_text,
            "char_count": len(climate_text),
            "url": full_url,
            "_source": self.source_name,
            "_extracted_at": datetime.utcnow().isoformat(),
        }

    async def _fetch_via_submissions(
        self,
        client: httpx.AsyncClient,
        cik: str,
        company_name: str,
        ticker: str,
        form_type: str,
        filing_date: str,
    ) -> dict[str, Any] | None:
        """Fallback: use the EDGAR submissions API to find the latest filing."""
        await asyncio.sleep(self.rate_limit)
        submissions_url = f"https://data.sec.gov/submissions/CIK{cik}.json"

        try:
            resp = await client.get(submissions_url)
            if resp.status_code != 200:
                return None

            data = resp.json()
            recent = data.get("filings", {}).get("recent", {})
            forms = recent.get("form", [])
            accessions = recent.get("accessionNumber", [])
            primary_docs = recent.get("primaryDocument", [])
            filing_dates = recent.get("filingDate", [])

            # Find most recent 10-K or 20-F
            for i, form in enumerate(forms):
                if form in ("10-K", "20-F", "10-K/A"):
                    accession = accessions[i].replace("-", "")
                    doc = primary_docs[i]
                    fdate = filing_dates[i]

                    await asyncio.sleep(self.rate_limit)
                    doc_url = f"https://www.sec.gov/Archives/edgar/data/{cik.lstrip('0')}/{accession}/{doc}"
                    doc_resp = await client.get(doc_url)

                    if doc_resp.status_code != 200:
                        continue

                    raw_text = (
                        _html_to_text(doc_resp.text)
                        if "<html" in doc_resp.text.lower()
                        else doc_resp.text
                    )
                    climate_text = _extract_climate_section(raw_text)

                    if len(climate_text) < 200:
                        continue

                    return {
                        "ticker": ticker,
                        "company": company_name,
                        "cik": cik,
                        "form_type": form,
                        "filing_date": fdate,
                        "text": climate_text,
                        "char_count": len(climate_text),
                        "url": doc_url,
                        "_source": self.source_name,
                        "_extracted_at": datetime.utcnow().isoformat(),
                    }

        except Exception as e:
            self.logger.warning("submissions_fallback_failed", cik=cik, error=str(e))

        return None
