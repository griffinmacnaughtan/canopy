"""Document upload and management endpoints."""

import structlog
from fastapi import APIRouter, File, UploadFile

from ..documents import clear_documents, get_documents, store_document
from ..exceptions import DocumentError, FileTooLargeError, UnsupportedFileTypeError
from ..models import DocumentInfo, DocumentListResponse, UploadResponse

router = APIRouter()
logger = structlog.get_logger()

# Configuration
MAX_FILE_SIZE_MB = 10
SUPPORTED_EXTENSIONS = [".pdf"]


@router.post("/upload", response_model=UploadResponse)
async def upload_document(file: UploadFile = File(...)):
    """Upload a PDF document for context in copilot queries."""
    # Validate file type
    if not file.filename:
        raise UnsupportedFileTypeError("unknown", SUPPORTED_EXTENSIONS)

    if not any(file.filename.lower().endswith(ext) for ext in SUPPORTED_EXTENSIONS):
        raise UnsupportedFileTypeError(file.filename, SUPPORTED_EXTENSIONS)

    # Read content
    content = await file.read()

    # Validate file size
    if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
        raise FileTooLargeError(MAX_FILE_SIZE_MB)

    # Process and store
    try:
        doc = store_document(file.filename, content)

        logger.info(
            "document_uploaded",
            filename=file.filename,
            char_count=doc.char_count,
        )

        return UploadResponse(
            success=True,
            document=DocumentInfo(filename=doc.filename, char_count=doc.char_count),
            message=f"Successfully extracted {doc.char_count:,} characters from {doc.filename}",
        )

    except Exception as e:
        logger.error("document_processing_failed", filename=file.filename, error=str(e))
        raise DocumentError(f"Failed to process PDF: {str(e)}") from e


@router.get("/documents", response_model=DocumentListResponse)
async def list_documents():
    """List all uploaded documents."""
    docs = get_documents()
    return DocumentListResponse(
        documents=[DocumentInfo(filename=d.filename, char_count=d.char_count) for d in docs],
        total_chars=sum(d.char_count for d in docs),
    )


@router.delete("/documents")
async def delete_documents():
    """Clear all uploaded documents."""
    count = clear_documents()

    logger.info("documents_cleared", count=count)

    return {"success": True, "cleared": count}
