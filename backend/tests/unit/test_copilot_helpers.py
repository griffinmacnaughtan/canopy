"""Tests for copilot RAG helper functions (source attribution)."""

from __future__ import annotations

from app.llm.prompts import get_source_attribution


class TestSourceAttribution:
    def test_base_sources_always_present(self):
        citations = get_source_attribution(has_documents=False)
        assert len(citations) == 3
        assert any("Portfolio" in c for c in citations)

    def test_filing_sources_produce_specific_citations(self):
        filing_sources = [
            {
                "company": "Apple Inc.",
                "filing_type": "10-K Annual Report",
                "section": "Item 1A - Risk Factors",
                "filing_date": "2024-11-01",
                "relevance": 0.85,
                "excerpt": "...",
            },
            {
                "company": "Shell plc",
                "filing_type": "10-K Annual Report",
                "section": "Item 1A - Risk Factors",
                "filing_date": "2024-02-20",
                "relevance": 0.72,
                "excerpt": "...",
            },
        ]
        citations = get_source_attribution(has_documents=False, filing_sources=filing_sources)
        assert any("Apple" in c for c in citations)
        assert any("Shell" in c for c in citations)
        # Should NOT have a generic label
        assert not any(
            c == "SEC 10-K filings (Item 1A climate risk disclosures)" for c in citations
        )

    def test_duplicate_filing_companies_deduplicated(self):
        filing_sources = [
            {
                "company": "Apple Inc.",
                "filing_type": "10-K",
                "section": "",
                "filing_date": "",
                "relevance": 0.9,
                "excerpt": "...",
            },
            {
                "company": "Apple Inc.",
                "filing_type": "10-K",
                "section": "",
                "filing_date": "",
                "relevance": 0.8,
                "excerpt": "...",
            },
        ]
        citations = get_source_attribution(has_documents=False, filing_sources=filing_sources)
        apple_citations = [c for c in citations if "Apple" in c]
        assert len(apple_citations) == 1

    def test_pipeline_and_documents_included(self):
        citations = get_source_attribution(
            has_documents=True,
            document_count=3,
            has_pipeline_data=True,
        )
        assert any("EPA" in c for c in citations)
        assert any("3 files" in c for c in citations)

    def test_section_and_date_in_citation(self):
        filing_sources = [
            {
                "company": "ExxonMobil",
                "filing_type": "10-K",
                "section": "Item 1A - Risk Factors",
                "filing_date": "2024-02-28",
                "relevance": 0.9,
                "excerpt": "...",
            },
        ]
        citations = get_source_attribution(has_documents=False, filing_sources=filing_sources)
        exxon_cite = [c for c in citations if "Exxon" in c][0]
        assert "Item 1A" in exxon_cite
        assert "2024-02-28" in exxon_cite

    def test_no_filings_no_filing_citations(self):
        citations = get_source_attribution(has_documents=False, filing_sources=None)
        assert not any("10-K" in c for c in citations)
        assert len(citations) == 3
