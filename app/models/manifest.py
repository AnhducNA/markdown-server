"""Manifest and Qdrant chunk payload schema for RAG traceability."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class QdrantChunkPayload(BaseModel):
    """Payload format designed for direct Qdrant ingestion without re-reading source file."""
    chunk_id: str
    document_id: str
    text: str
    source_type: str
    source: str
    page: Optional[int] = None
    section_path: List[str] = Field(default_factory=list)
    attributes: Dict[str, Any] = Field(default_factory=dict)


class DocumentManifest(BaseModel):
    """Complete manifest written to output/manifest/<document_id>.json."""
    document_id: str
    title: Optional[str] = None
    source_type: str
    source: str
    source_uri: Optional[str] = None
    language: str = "vi"
    page_count: Optional[int] = None
    parser: str
    ocr_used: bool = False
    ocr_engine: Optional[str] = None
    pages_ocr: List[int] = Field(default_factory=list)
    created_at: str
    markdown_path: str
    blocks_count: int
    assets_count: int
    blocks: List[Dict[str, Any]] = Field(default_factory=list)
    assets: List[Dict[str, Any]] = Field(default_factory=list)
    chunks: List[QdrantChunkPayload] = Field(default_factory=list)
