"""Document inspection and retrieval endpoints."""
import json
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import FileResponse, PlainTextResponse

from app.core.config import settings
from app.models.api import DocumentDetailResponse
from app.output.manifest_writer import ManifestWriter
from app.output.writer import MarkdownWriter, sanitize_filename

router = APIRouter()
writer = MarkdownWriter()
manifest_writer = ManifestWriter()


@router.get("/documents/{document_id}", response_model=DocumentDetailResponse)
async def get_document(
    document_id: str,
    tenant: Optional[str] = Query(None, description="Optional tenant identifier"),
):
    """Get metadata summary, manifest details, and preview of a converted document."""
    safe_id = sanitize_filename(document_id)
    manifest_path = manifest_writer.get_manifest_path(safe_id, tenant)
    md_path = writer.get_output_path(safe_id, tenant)

    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail=f"Document '{safe_id}' not found.")

    try:
        manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
        preview = None
        if md_path.exists():
            md_full = md_path.read_text(encoding=settings.markdown_encoding)
            preview = md_full[:1000] + ("..." if len(md_full) > 1000 else "")

        return DocumentDetailResponse(
            document_id=safe_id,
            status="completed",
            markdown_path=str(md_path.as_posix()),
            metadata_path=str(manifest_path.as_posix()),
            metadata={
                "title": manifest_data.get("title"),
                "source_type": manifest_data.get("source_type"),
                "source": manifest_data.get("source"),
                "page_count": manifest_data.get("page_count"),
                "parser": manifest_data.get("parser"),
                "ocr_used": manifest_data.get("ocr_used"),
                "created_at": manifest_data.get("created_at"),
            },
            blocks_count=manifest_data.get("blocks_count", 0),
            assets_count=manifest_data.get("assets_count", 0),
            preview=preview,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error reading document: {str(e)}")


@router.get("/documents/{document_id}/markdown")
async def get_markdown(
    document_id: str,
    tenant: Optional[str] = Query(None, description="Optional tenant identifier"),
    download: bool = Query(False, description="Whether to download file as attachment"),
):
    """Retrieve raw Markdown content or download as .md file."""
    safe_id = sanitize_filename(document_id)
    md_path = writer.get_output_path(safe_id, tenant)

    if not md_path.exists():
        raise HTTPException(status_code=404, detail=f"Markdown for document '{safe_id}' not found.")

    if download:
        return FileResponse(
            path=str(md_path),
            filename=f"{safe_id}.md",
            media_type="text/markdown",
        )

    content = md_path.read_text(encoding=settings.markdown_encoding)
    return PlainTextResponse(content, media_type="text/markdown; charset=utf-8")


@router.get("/documents/{document_id}/manifest")
async def get_manifest(
    document_id: str,
    tenant: Optional[str] = Query(None, description="Optional tenant identifier"),
):
    """Retrieve full manifest JSON containing blocks and Qdrant chunk payloads."""
    safe_id = sanitize_filename(document_id)
    manifest_path = manifest_writer.get_manifest_path(safe_id, tenant)

    if not manifest_path.exists():
        raise HTTPException(status_code=404, detail=f"Manifest for document '{safe_id}' not found.")

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    return manifest_data
