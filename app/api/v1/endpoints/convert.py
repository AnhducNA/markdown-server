"""Conversion endpoints for file upload and URLs."""
from typing import Optional
from fastapi import APIRouter, File, Form, HTTPException, UploadFile

from app.core.logging import logger
from app.ingestion.file_handler import FileHandler
from app.models.api import ConvertResponse, ConvertUrlRequest
from app.pipeline.orchestrator import orchestrator

router = APIRouter()
file_handler = FileHandler()


@router.post("/convert", response_model=ConvertResponse)
async def convert_file(
    file: UploadFile = File(..., description="PDF or DOCX document to convert"),
    document_id: Optional[str] = Form(None, description="Optional custom document ID"),
    force_ocr: bool = Form(False, description="Force OCR on all pages even if text exists"),
    tenant: Optional[str] = Form(None, description="Tenant identifier for multi-tenant storage"),
    include_frontmatter: Optional[bool] = Form(None, description="Include YAML frontmatter in markdown"),
):
    """
    Convert an uploaded document (PDF or DOCX) into normalized Markdown and manifest JSON.
    """
    try:
        doc_id, saved_path = await file_handler.save_upload(file, document_id=document_id)
        result = orchestrator.process_file(
            file_path=saved_path,
            document_id=doc_id,
            force_ocr=force_ocr,
            tenant=tenant,
            include_frontmatter=include_frontmatter,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing upload: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")


@router.post("/convert-url", response_model=ConvertResponse)
async def convert_url(request: ConvertUrlRequest):
    """
    Extract content from a web URL and convert to normalized Markdown and manifest JSON.
    """
    try:
        result = orchestrator.process_url(
            url=str(request.url),
            document_id=request.document_id,
            tenant=request.tenant,
            include_frontmatter=request.include_frontmatter,
        )
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error processing URL: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Conversion error: {str(e)}")
