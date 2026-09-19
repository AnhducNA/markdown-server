"""PyMuPDF PDF Parser Adapter with OCR detection integration.

Extracts text, headings, tables, and images from PDF documents.
Evaluates each page with OCRDetector and seamlessly delegates scanned/low-text pages
to PaddleOCRAdapter.
"""
from pathlib import Path
from typing import Any, Dict, List, Optional, Union
import uuid
import fitz  # PyMuPDF

from app.core.config import settings
from app.core.logging import logger
from app.models.document import Asset, Block, BlockType, DocumentMetadata, UnifiedDocument
from app.ocr.detector import OCRDetector
from app.ocr.paddleocr_adapter import PaddleOCRAdapter
from app.parsers.base import BaseParser


class PyMuPDFParserAdapter(BaseParser):
    def __init__(
        self,
        ocr_detector: Optional[OCRDetector] = None,
        ocr_adapter: Optional[PaddleOCRAdapter] = None,
    ):
        self.detector = ocr_detector or OCRDetector()
        self.ocr_adapter = ocr_adapter or PaddleOCRAdapter()

    def _determine_heading_level(self, span_size: float, is_bold: bool, base_size: float = 10.0) -> Optional[int]:
        """Infer heading level based on font size and weight."""
        if span_size >= base_size * 1.8:
            return 1
        elif span_size >= base_size * 1.5:
            return 2
        elif span_size >= base_size * 1.25 or (span_size >= base_size * 1.15 and is_bold):
            return 3
        elif span_size >= base_size * 1.05 and is_bold:
            return 4
        return None

    def parse(
        self,
        source: Union[Path, str],
        document_id: Optional[str] = None,
        force_ocr: bool = False,
        tenant: Optional[str] = None,
        **kwargs,
    ) -> UnifiedDocument:
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"PDF source file not found: {source_path}")

        doc_id = document_id or f"doc_{uuid.uuid4().hex[:8]}"
        doc = fitz.open(str(source_path))
        page_count = len(doc)

        logger.info(f"Parsing PDF '{source_path.name}' with {page_count} pages (doc_id={doc_id})")

        metadata = DocumentMetadata(
            document_id=doc_id,
            title=doc.metadata.get("title") or None,
            source_type="pdf",
            source_name=source_path.name,
            source_uri=str(source_path.as_posix()),
            page_count=page_count,
            parser="pymupdf",
            tenant=tenant,
        )

        unified_doc = UnifiedDocument(metadata=metadata)

        current_section_path: List[str] = []
        pages_ocr: List[int] = []
        image_counter = 1

        for page_idx in range(page_count):
            page_num = page_idx + 1
            page = doc[page_idx]
            raw_text = page.get_text()
            page_rect = page.rect
            img_list = page.get_images()

            # Evaluate page for OCR
            decision = self.detector.evaluate_page(
                text=raw_text,
                page_width=page_rect.width,
                page_height=page_rect.height,
                image_count=len(img_list),
                force_ocr=force_ocr,
            )

            if decision.needs_ocr and self.ocr_adapter.is_available():
                logger.info(f"Page {page_num} routed to OCR (reason: {decision.reason})")
                ocr_blocks = self.ocr_adapter.process_page_to_blocks(
                    pdf_page=page,
                    document_id=doc_id,
                    section_path=list(current_section_path),
                )
                if ocr_blocks:
                    for blk in ocr_blocks:
                        unified_doc.blocks.append(blk)
                        if blk.type == BlockType.HEADING:
                            level = blk.level or 1
                            current_section_path = current_section_path[: max(0, level - 1)] + [blk.text.strip()]
                    pages_ocr.append(page_num)
                    continue
                logger.warning(f"OCR produced no text for page {page_num}; using native PDF extraction.")
            elif decision.needs_ocr:
                logger.warning(f"OCR requested for page {page_num}, but PaddleOCR is unavailable; using native PDF extraction.")

            # Process native text page
            # 1. Try finding tables first to prevent table text duplication
            table_rects = []
            try:
                tables = page.find_tables()
                for table in tables:
                    table_matrix = table.extract()
                    if table_matrix and len(table_matrix) > 0:
                        table_rects.append(fitz.Rect(table.bbox))
                        unified_doc.add_block(
                            block_type=BlockType.TABLE,
                            text="",
                            page=page_num,
                            section_path=list(current_section_path),
                            attributes={"rows": table_matrix},
                            bbox=list(table.bbox),
                        )
            except Exception as e:
                logger.debug(f"Table detection skipped on page {page_num}: {e}")

            # 2. Extract text blocks and determine headings
            text_dict = page.get_text("dict")
            for block in text_dict.get("blocks", []):
                block_rect = fitz.Rect(block.get("bbox", [0, 0, 0, 0]))

                # Skip if text is within an already extracted table
                if any(block_rect.intersects(t_rect) for t_rect in table_rects):
                    continue

                if block.get("type") == 0:  # text block
                    block_text_parts = []
                    max_span_size = 0.0
                    is_bold = False

                    for line in block.get("lines", []):
                        for span in line.get("spans", []):
                            span_text = span.get("text", "")
                            if span_text:
                                block_text_parts.append(span_text)
                                size = span.get("size", 0.0)
                                if size > max_span_size:
                                    max_span_size = size
                                font_flags = span.get("flags", 0)
                                font_name = span.get("font", "").lower()
                                if (font_flags & 2 != 0) or ("bold" in font_name):
                                    is_bold = True

                    full_text = " ".join("".join(block_text_parts).split()).strip()
                    if not full_text:
                        continue

                    level = self._determine_heading_level(max_span_size, is_bold)
                    if level is not None and len(full_text) < 120 and "\n" not in full_text:
                        # Recognized as heading
                        current_section_path = current_section_path[: max(0, level - 1)] + [full_text]
                        unified_doc.add_block(
                            block_type=BlockType.HEADING,
                            text=full_text,
                            level=level,
                            page=page_num,
                            section_path=list(current_section_path),
                            bbox=list(block_rect),
                        )
                        if unified_doc.metadata.title is None and level == 1:
                            unified_doc.metadata.title = full_text
                    else:
                        unified_doc.add_block(
                            block_type=BlockType.PARAGRAPH,
                            text=full_text,
                            page=page_num,
                            section_path=list(current_section_path),
                            bbox=list(block_rect),
                        )

                elif block.get("type") == 1:  # image block
                    # Extract image data
                    try:
                        bbox = list(block.get("bbox", [0, 0, 0, 0]))
                        img_name = f"image_{page_num:03d}_{image_counter:03d}.png"
                        image_counter += 1

                        # Clip pixmap of the image bbox from page
                        pix = page.get_pixmap(clip=fitz.Rect(bbox), dpi=150)
                        img_bytes = pix.tobytes("png")

                        rel_path = f"assets/{doc_id}/{img_name}"
                        asset = Asset(
                            name=img_name,
                            relative_path=rel_path,
                            mime_type="image/png",
                            page=page_num,
                            data=img_bytes,
                            size_bytes=len(img_bytes),
                        )
                        unified_doc.assets.append(asset)
                        unified_doc.add_block(
                            block_type=BlockType.IMAGE,
                            text=f"Image on page {page_num}",
                            page=page_num,
                            section_path=list(current_section_path),
                            attributes={"path": rel_path},
                            bbox=bbox,
                        )
                    except Exception as img_err:
                        logger.warning(f"Could not extract image on page {page_num}: {img_err}")

        doc.close()

        # Update metadata if OCR was used
        if pages_ocr:
            unified_doc.metadata.ocr_used = True
            unified_doc.metadata.ocr_engine = settings.ocr_engine
            unified_doc.metadata.pages_ocr = sorted(pages_ocr)
            unified_doc.metadata.parser = "pymupdf+paddleocr"

        return unified_doc
