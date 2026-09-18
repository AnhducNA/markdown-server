"""API Request and Response schemas."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, HttpUrl


class ConvertResponse(BaseModel):
    """Response returned upon successful document conversion."""
    document_id: str = Field(description="Unique document ID (UUID/ULID)")
    status: str = Field(default="completed", description="Processing status")
    markdown_path: str = Field(description="Relative path to converted markdown file")
    metadata_path: str = Field(description="Relative path to metadata manifest json")
    assets_count: int = Field(default=0, description="Total extracted assets")
    page_count: Optional[int] = Field(default=None, description="Total pages processed")
    ocr_used: bool = Field(default=False, description="Whether OCR was performed")
    pages_ocr: List[int] = Field(default_factory=list, description="Pages that underwent OCR")
    created_at: str = Field(description="ISO timestamp of completion")


class ConvertUrlRequest(BaseModel):
    """Payload for POST /api/v1/convert-url."""
    url: HttpUrl = Field(description="Web page URL to scrape and convert")
    document_id: Optional[str] = Field(default=None, description="Custom document_id if desired")
    tenant: Optional[str] = Field(default=None, description="Tenant ID for multi-tenant storage")
    force_ocr: bool = Field(default=False, description="Whether to force OCR on rendered page images")
    include_frontmatter: Optional[bool] = Field(default=None, description="Override frontmatter setting")


class DocumentDetailResponse(BaseModel):
    """Response for GET /api/v1/documents/{document_id}."""
    document_id: str
    status: str
    markdown_path: str
    metadata_path: str
    metadata: Dict[str, Any]
    blocks_count: int
    assets_count: int
    preview: Optional[str] = None


class HealthResponse(BaseModel):
    """Response for GET /api/v1/health."""
    status: str = "ok"
    version: str = "0.1.0"
    available_parsers: List[str]
    ocr_engine: str
    ocr_available: bool
    output_dir: str
