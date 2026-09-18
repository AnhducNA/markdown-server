"""Health check endpoint."""
from fastapi import APIRouter
from app.core.config import settings
from app.models.api import HealthResponse
from app.ocr.paddleocr_adapter import PaddleOCRAdapter
from app.parsers.docling_adapter import DoclingParserAdapter

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check returning available adapters and runtime status."""
    docling_available = DoclingParserAdapter().is_available()
    paddleocr_available = PaddleOCRAdapter().is_available()

    available_parsers = ["pymupdf", "python-docx", "trafilatura"]
    if docling_available:
        available_parsers.append("docling")

    return HealthResponse(
        status="ok",
        version="0.1.0",
        available_parsers=available_parsers,
        ocr_engine=settings.ocr_engine,
        ocr_available=paddleocr_available,
        output_dir=str(settings.output_dir),
    )
