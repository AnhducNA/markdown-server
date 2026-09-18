"""Unified Document Model for Markdown Output Pipeline.

Follows the specification in Section 5, 13, 23.5 of the design document:
- Blocks represent atomic content units (heading, paragraph, list, table, code, image, quote).
- Each block retains traceability (page number, section_path, bbox, confidence).
"""
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, List, Optional
import uuid

from pydantic import BaseModel, Field


class BlockType(str, Enum):
    HEADING = "heading"
    PARAGRAPH = "paragraph"
    LIST = "list"
    TABLE = "table"
    IMAGE = "image"
    CODE = "code"
    QUOTE = "quote"


class Block(BaseModel):
    """Atomic block unit inside a Unified Document."""
    id: str = Field(default_factory=lambda: f"blk_{uuid.uuid4().hex[:8]}")
    type: BlockType
    level: Optional[int] = Field(default=None, description="Heading level 1-6 or list nest level")
    text: str = Field(default="", description="Textual content or representation")
    page: Optional[int] = Field(default=None, description="1-based page number")
    section_path: List[str] = Field(default_factory=list, description="Hierarchy of parent heading titles")
    attributes: Dict[str, Any] = Field(default_factory=dict, description="Metadata such as code lang, image path, table rows")
    bbox: Optional[List[float]] = Field(default=None, description="Coordinates [x1, y1, x2, y2] if available")
    confidence: Optional[float] = Field(default=None, description="OCR confidence if applicable")


class Asset(BaseModel):
    """Asset representation (e.g. extracted image or chart)."""
    asset_id: str = Field(default_factory=lambda: f"asset_{uuid.uuid4().hex[:8]}")
    name: str = Field(description="Normalized asset file name")
    relative_path: str = Field(description="Relative path used in Markdown, e.g., assets/image-001.png")
    mime_type: str = Field(default="image/png")
    page: Optional[int] = None
    data: Optional[bytes] = Field(default=None, repr=False, exclude=True)
    size_bytes: int = 0


class DocumentMetadata(BaseModel):
    """Metadata of the processed document."""
    document_id: str
    title: Optional[str] = None
    source_type: str = Field(description="pdf | docx | web | text")
    source_name: str
    source_uri: Optional[str] = None
    language: str = "vi"
    page_count: Optional[int] = None
    parser: str = "pymupdf"
    ocr_used: bool = False
    ocr_engine: Optional[str] = None
    pages_ocr: List[int] = Field(default_factory=list)
    tenant: Optional[str] = None
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class UnifiedDocument(BaseModel):
    """Standardized representation of a document regardless of input source."""
    metadata: DocumentMetadata
    blocks: List[Block] = Field(default_factory=list)
    assets: List[Asset] = Field(default_factory=list)

    def add_block(
        self,
        block_type: BlockType,
        text: str,
        level: Optional[int] = None,
        page: Optional[int] = None,
        section_path: Optional[List[str]] = None,
        attributes: Optional[Dict[str, Any]] = None,
        bbox: Optional[List[float]] = None,
        confidence: Optional[float] = None,
    ) -> Block:
        block = Block(
            type=block_type,
            text=text,
            level=level,
            page=page,
            section_path=section_path or [],
            attributes=attributes or {},
            bbox=bbox,
            confidence=confidence,
        )
        self.blocks.append(block)
        return block
