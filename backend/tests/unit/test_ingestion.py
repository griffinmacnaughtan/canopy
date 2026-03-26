"""Tests for SEC filing ingestion pipeline.

Validates the full path from static .txt files on disk through
chunking to vector store population — the foundation of the RAG pipeline.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.ingestion.sec_filings import (
    get_all_filing_paths,
    load_filing_from_disk,
)
from app.vectorstore import VectorStore
from app.vectorstore.chunker import chunk_text

# ── Static Filing Discovery ──────────────────────────────────────────────


class TestFilingDiscovery:
    """Ensure the data/filings directory is populated and discoverable."""

    def test_finds_at_least_six_filings(self):
        paths = get_all_filing_paths()
        assert len(paths) >= 6, f"Expected at least 6 filing files, found {len(paths)}"

    def test_all_files_are_txt(self):
        for p in get_all_filing_paths():
            assert p.suffix == ".txt", f"{p.name} is not a .txt file"

    def test_files_are_sorted(self):
        paths = get_all_filing_paths()
        names = [p.name for p in paths]
        assert names == sorted(names), "Filing paths should be sorted alphabetically"

    def test_expected_companies_present(self):
        names = {p.stem for p in get_all_filing_paths()}
        # Static baseline files must always be present; live-fetched files
        # may add more but must not remove the originals.
        expected = {
            "apple_10k_climate_risks",
            "basf_20f_climate_risks",
            "exxon_mobil_10k_climate_risks",
            "jpmorgan_10k_climate_risks",
            "nextera_energy_10k_climate_risks",
            "shell_10k_climate_risks",
        }
        assert expected.issubset(names), f"Missing static filings: {expected - names}"


# ── Filing Loader ────────────────────────────────────────────────────────


class TestFilingLoader:
    """Validate the YAML-header parser and body extraction."""

    @pytest.fixture()
    def sample_filing(self, tmp_path: Path) -> Path:
        content = (
            "Company: TestCorp Inc.\n"
            "Ticker: TEST\n"
            "Filing: 10-K Annual Report\n"
            "Section: Item 1A - Risk Factors\n"
            "Filing Date: 2024-02-15\n"
            "Source: SEC EDGAR (CIK: 0001234567)\n"
            "---\n"
            "Climate Change and Environmental Regulation\n\n"
            "TestCorp faces significant transition risks from climate-related "
            "regulation, including the EU ETS and CBAM mechanisms."
        )
        fp = tmp_path / "test_filing.txt"
        fp.write_text(content, encoding="utf-8")
        return fp

    def test_parses_metadata_fields(self, sample_filing: Path):
        body, meta = load_filing_from_disk(sample_filing)
        assert meta["Company"] == "TestCorp Inc."
        assert meta["Ticker"] == "TEST"
        assert meta["Filing"] == "10-K Annual Report"
        assert meta["Filing Date"] == "2024-02-15"

    def test_separates_body_from_header(self, sample_filing: Path):
        body, _ = load_filing_from_disk(sample_filing)
        assert "Climate Change" in body
        assert "Company:" not in body
        assert "---" not in body

    def test_body_not_empty(self, sample_filing: Path):
        body, _ = load_filing_from_disk(sample_filing)
        assert len(body) > 50

    def test_empty_file_returns_empty_body(self, tmp_path: Path):
        fp = tmp_path / "empty.txt"
        fp.write_text("Company: Empty\n---\n", encoding="utf-8")
        body, meta = load_filing_from_disk(fp)
        assert body == ""
        assert meta["Company"] == "Empty"

    def test_real_filings_parse_correctly(self):
        """All 6 real filings must parse without error and have substantial body text."""
        for path in get_all_filing_paths():
            body, meta = load_filing_from_disk(path)
            assert meta.get("Company"), f"{path.name} missing Company metadata"
            assert meta.get("Ticker"), f"{path.name} missing Ticker metadata"
            assert len(body) > 200, f"{path.name} body too short ({len(body)} chars)"

    def test_real_filings_have_climate_content(self):
        """Static filing excerpts should contain climate-related terminology.

        Live-fetched filings (from SEC EDGAR) may contain broader 10-K
        content, so we only assert ≥ 2 hits for the original static files.
        """
        static_files = {
            "apple_10k_climate_risks",
            "basf_20f_climate_risks",
            "exxon_mobil_10k_climate_risks",
            "jpmorgan_10k_climate_risks",
            "nextera_energy_10k_climate_risks",
            "shell_10k_climate_risks",
        }
        climate_terms = {"climate", "emissions", "carbon", "risk"}
        for path in get_all_filing_paths():
            body, _ = load_filing_from_disk(path)
            body_lower = body.lower()
            hits = {t for t in climate_terms if t in body_lower}
            if path.stem in static_files:
                assert len(hits) >= 2, f"{path.name} has insufficient climate terminology: found {hits}"


# ── Chunking Integration ────────────────────────────────────────────────


class TestFilingChunking:
    """Verify that filing bodies chunk correctly for the vector store."""

    def test_chunking_produces_multiple_chunks(self):
        """A real filing should produce more than one chunk at 512-char size."""
        path = get_all_filing_paths()[0]
        body, _ = load_filing_from_disk(path)
        chunks = chunk_text(body, source="test", chunk_size=512, chunk_overlap=64)
        assert len(chunks) >= 2, f"Expected multiple chunks, got {len(chunks)}"

    def test_chunks_have_correct_source(self):
        path = get_all_filing_paths()[0]
        body, meta = load_filing_from_disk(path)
        source = f"{meta['Company']} ({meta['Filing']})"
        chunks = chunk_text(body, source=source, chunk_size=512, chunk_overlap=64)
        for c in chunks:
            assert c.source == source

    def test_chunk_indices_are_sequential(self):
        path = get_all_filing_paths()[0]
        body, _ = load_filing_from_disk(path)
        chunks = chunk_text(body, source="test", chunk_size=512, chunk_overlap=64)
        indices = [c.index for c in chunks]
        assert indices == list(range(len(chunks)))


# ── Vector Store Integration ─────────────────────────────────────────────


class TestVectorStoreIngestion:
    """End-to-end: load filing, chunk, embed, store, search."""

    @pytest.fixture()
    def fresh_store(self) -> VectorStore:
        return VectorStore()

    @pytest.mark.asyncio()
    async def test_ingest_single_filing(self, fresh_store: VectorStore):
        from app.ingestion.ingest import ingest_filing

        path = get_all_filing_paths()[0]
        count = await ingest_filing(path, fresh_store)
        assert count > 0, "Should have ingested at least one chunk"
        assert fresh_store.size == count

    @pytest.mark.asyncio()
    async def test_ingest_all_filings(self, fresh_store: VectorStore):
        from app.ingestion.ingest import ingest_all_filings

        result = await ingest_all_filings(fresh_store)
        assert result["files_processed"] >= 6
        assert result["total_chunks"] > 10, "6+ filings should produce > 10 chunks"
        assert len(result["per_file"]) >= 6

    @pytest.mark.asyncio()
    async def test_search_returns_results_after_ingestion(self, fresh_store: VectorStore):
        from app.ingestion.ingest import ingest_all_filings

        await ingest_all_filings(fresh_store)

        results = await fresh_store.search("climate change emissions carbon pricing", top_k=3)
        assert len(results) > 0, "Search should return results from ingested filings"

    @pytest.mark.asyncio()
    async def test_search_results_have_metadata(self, fresh_store: VectorStore):
        from app.ingestion.ingest import ingest_filing

        path = get_all_filing_paths()[0]
        await ingest_filing(path, fresh_store)

        results = await fresh_store.search("climate risk", top_k=1)
        assert len(results) > 0
        doc = results[0].document
        assert "company" in doc.metadata
        assert "ticker" in doc.metadata
        assert "filing_type" in doc.metadata
        assert "data_source" in doc.metadata
        assert doc.metadata["data_source"] == "SEC EDGAR"

    @pytest.mark.asyncio()
    async def test_seed_vector_store_clears_and_reloads(self):
        from app.ingestion.ingest import seed_vector_store
        from app.vectorstore import get_vector_store

        # Seed once
        result1 = await seed_vector_store()
        store = get_vector_store()
        size1 = store.size

        # Seed again — should clear and produce same count
        result2 = await seed_vector_store()
        size2 = store.size

        assert size1 == size2, "Re-seeding should produce same chunk count"
        assert result1["total_chunks"] == result2["total_chunks"]

        # Clean up global state
        store.clear()


# ── SEC EDGAR Extractor Configuration ────────────────────────────────────


class TestEdgarConfig:
    """Validate SEC EDGAR extractor configuration."""

    def test_sec_extractor_has_user_agent(self):
        from app.pipeline.config import PipelineConfig
        from app.pipeline.extractors.sec_edgar import SECEdgarExtractor

        config = PipelineConfig()
        extractor = SECEdgarExtractor(config)
        headers = extractor._headers()
        assert "User-Agent" in headers
        assert len(headers["User-Agent"]) > 10

    def test_sec_extractor_has_companies(self):
        from app.pipeline.extractors.sec_edgar import COMPANY_CIKS

        assert len(COMPANY_CIKS) >= 20
