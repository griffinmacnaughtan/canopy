"""In-memory document store for uploaded PDFs."""

from dataclasses import dataclass
from io import BytesIO

import pdfplumber


@dataclass
class Document:
    """Stored document with extracted text."""

    filename: str
    text: str
    char_count: int


# Global in-memory store: portfolio_id -> list of documents
_document_store: dict[str, list[Document]] = {}

# Default portfolio ID for documents without a specific portfolio
DEFAULT_PORTFOLIO = "default"


def extract_text_from_pdf(file_content: bytes) -> str:
    """Extract text from PDF bytes.

    Args:
        file_content: Raw PDF file bytes.

    Returns:
        Extracted text from all pages.
    """
    text_parts = []

    with pdfplumber.open(BytesIO(file_content)) as pdf:
        for page in pdf.pages:
            page_text = page.extract_text()
            if page_text:
                text_parts.append(page_text)

    return "\n\n".join(text_parts)


def store_document(
    filename: str,
    file_content: bytes,
    portfolio_id: str | None = None,
) -> Document:
    """Store a document after extracting its text.

    Args:
        filename: Original filename.
        file_content: Raw PDF bytes.
        portfolio_id: Optional portfolio to associate with.

    Returns:
        The stored Document object.
    """
    portfolio_key = portfolio_id or DEFAULT_PORTFOLIO
    text = extract_text_from_pdf(file_content)

    doc = Document(
        filename=filename,
        text=text,
        char_count=len(text),
    )

    if portfolio_key not in _document_store:
        _document_store[portfolio_key] = []

    _document_store[portfolio_key].append(doc)
    return doc


def get_documents(portfolio_id: str | None = None) -> list[Document]:
    """Get all documents for a portfolio.

    Args:
        portfolio_id: Portfolio to get documents for.

    Returns:
        List of stored documents.
    """
    portfolio_key = portfolio_id or DEFAULT_PORTFOLIO
    return _document_store.get(portfolio_key, [])


def clear_documents(portfolio_id: str | None = None) -> int:
    """Clear all documents for a portfolio.

    Args:
        portfolio_id: Portfolio to clear documents for.

    Returns:
        Number of documents cleared.
    """
    portfolio_key = portfolio_id or DEFAULT_PORTFOLIO

    if portfolio_key in _document_store:
        count = len(_document_store[portfolio_key])
        del _document_store[portfolio_key]
        return count

    return 0


MAX_CONTEXT_CHARS = 15000  # ~3750 tokens, conservative limit


def get_combined_document_text(portfolio_id: str | None = None) -> str | None:
    """Get combined text from all documents for context injection.

    Args:
        portfolio_id: Portfolio to get documents for.

    Returns:
        Combined text from all documents, or None if no documents.
    """
    docs = get_documents(portfolio_id)

    if not docs:
        return None

    parts = []
    total_chars = 0

    for doc in docs:
        doc_text = doc.text
        remaining = MAX_CONTEXT_CHARS - total_chars

        if remaining <= 0:
            break

        if len(doc_text) > remaining:
            doc_text = doc_text[:remaining] + "\n\n[... truncated for length ...]"

        parts.append(f"### Document: {doc.filename}\n\n{doc_text}")
        total_chars += len(doc_text)

    return "\n\n---\n\n".join(parts)
