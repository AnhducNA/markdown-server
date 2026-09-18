"""PaddleOCR Adapter for optical character recognition on scanned PDF pages.

Conforms to Section 23.4 & 23.5 of the design document:
- Rasterizes PDF pages to high-resolution images via PyMuPDF / PIL
- Interacts with PaddleOCR engine when available
- Sorts OCR detected text boxes according to natural reading order (top-to-bottom, left-to-right)
- Produces Unified Document Model Blocks with bbox coordinates and confidence scores
- Graceful fallback and error boundary per page
"""
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Any, List, Optional
import fitz  # PyMuPDF
from PIL import Image

from app.core.config import settings
from app.core.logging import logger
from app.models.document import Block, BlockType


@dataclass
class OCRLineResult:
    text: str
    bbox: List[float]  # [x1, y1, x2, y2]
    confidence: float


class PaddleOCRAdapter:
    def __init__(self, lang: Optional[str] = None):
        self.lang = lang or settings.ocr_lang
        self._engine: Any = None
        self._is_available: Optional[bool] = None

    def is_available(self) -> bool:
        """Check if PaddleOCR and its backend are importable."""
        if self._is_available is not None:
            return self._is_available
        try:
            from paddleocr import PaddleOCR  # type: ignore
            # Try lazy init or check import
            self._is_available = True
        except ImportError:
            logger.warning("PaddleOCR is not installed in the environment. Operating in mock/fallback mode.")
            self._is_available = False
        except Exception as e:
            logger.warning(f"PaddleOCR check failed: {e}")
            self._is_available = False
        return self._is_available

    def _get_engine(self):
        if self._engine is None and self.is_available():
            try:
                from paddleocr import PaddleOCR  # type: ignore
                logger.info(f"Initializing PaddleOCR engine with lang='{self.lang}'...")
                self._engine = PaddleOCR(use_angle_cls=True, lang=self.lang, show_log=False)
            except Exception as e:
                logger.error(f"Failed to initialize PaddleOCR engine: {e}")
                self._is_available = False
        return self._engine

    def rasterize_pdf_page(self, pdf_page: fitz.Page, dpi: Optional[int] = None) -> Path:
        """Rasterize a PDF page to a temporary PNG file."""
        target_dpi = dpi or settings.pdf_render_dpi
        rendered_dir = settings.tmp_dir / "rendered_pages"
        rendered_dir.mkdir(parents=True, exist_ok=True)

        img_path = rendered_dir / f"page_{pdf_page.number + 1}_{target_dpi}dpi.png"
        pix = pdf_page.get_pixmap(dpi=target_dpi)
        pix.save(str(img_path))
        return img_path

    def sort_reading_order(self, lines: List[OCRLineResult]) -> List[OCRLineResult]:
        """
        Sort bounding boxes in natural human reading order:
        Group boxes having overlapping or close vertical ranges into lines,
        then sort left-to-right within each line.
        """
        if not lines:
            return []

        # Sort by top-y first
        sorted_by_y = sorted(lines, key=lambda item: (item.bbox[1], item.bbox[0]))

        # Group lines with vertical tolerance
        grouped_lines: List[List[OCRLineResult]] = []
        for item in sorted_by_y:
            placed = False
            for group in grouped_lines:
                # Average height of group
                avg_y = sum(g.bbox[1] for g in group) / len(group)
                avg_height = sum(g.bbox[3] - g.bbox[1] for g in group) / len(group)
                tolerance = max(8.0, avg_height * 0.5)

                if abs(item.bbox[1] - avg_y) <= tolerance:
                    group.append(item)
                    placed = True
                    break
            if not placed:
                grouped_lines.append([item])

        # Sort each group horizontally left-to-right
        final_ordered: List[OCRLineResult] = []
        for group in grouped_lines:
            group.sort(key=lambda item: item.bbox[0])
            final_ordered.extend(group)

        return final_ordered

    def recognize_image(self, image_path: Path) -> List[OCRLineResult]:
        """Perform OCR recognition on an image file."""
        engine = self._get_engine()
        results: List[OCRLineResult] = []

        if engine is not None:
            try:
                ocr_output = engine.ocr(str(image_path), cls=True)
                if ocr_output and ocr_output[0]:
                    for entry in ocr_output[0]:
                        # entry format: [points, (text, confidence)]
                        points = entry[0]
                        text, conf = entry[1]
                        x_coords = [p[0] for p in points]
                        y_coords = [p[1] for p in points]
                        bbox = [min(x_coords), min(y_coords), max(x_coords), max(y_coords)]
                        results.append(OCRLineResult(text=str(text).strip(), bbox=bbox, confidence=float(conf)))
            except Exception as e:
                logger.error(f"Error during PaddleOCR recognition on {image_path}: {e}")
        else:
            logger.info(f"PaddleOCR not available for {image_path}. Returning fallback notice.")
            results.append(
                OCRLineResult(
                    text="[OCR fallback: PaddleOCR not installed or unavailable in current environment]",
                    bbox=[0.0, 0.0, 100.0, 20.0],
                    confidence=0.0,
                )
            )

        return self.sort_reading_order(results)

    def process_page_to_blocks(
        self,
        pdf_page: fitz.Page,
        document_id: str,
        section_path: Optional[List[str]] = None,
    ) -> List[Block]:
        """Rasterize a PDF page, perform OCR, and convert results into Unified Document Blocks."""
        page_num = pdf_page.number + 1
        img_path = self.rasterize_pdf_page(pdf_page)
        lines = self.recognize_image(img_path)

        blocks: List[Block] = []
        for line in lines:
            if not line.text:
                continue
            # Simple heuristic for heading in OCR: short lines in all caps or starting with numbers
            is_heading = len(line.text) < 60 and (line.text.isupper() or line.text.startswith(("Chương", "Phần", "Mục", "Điều")))
            block_type = BlockType.HEADING if is_heading else BlockType.PARAGRAPH
            level = 2 if is_heading else None

            block = Block(
                type=block_type,
                level=level,
                text=line.text,
                page=page_num,
                section_path=section_path or [],
                attributes={
                    "ocr": True,
                    "ocr_engine": "paddleocr",
                    "rasterized_image": str(img_path.name),
                },
                bbox=line.bbox,
                confidence=line.confidence,
            )
            blocks.append(block)

        return blocks
