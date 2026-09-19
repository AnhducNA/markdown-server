"""OCR Detector module.

Implements decision heuristics per Section 23.3 of the design document:
- Evaluates individual page text length vs OCR_MIN_TEXT_CHARS
- Evaluates text density vs OCR_MIN_TEXT_DENSITY
- Checks for image-dominant pages without adequate text
- Honors force_ocr override
- Records explicit processing_reason for RAG traceability
"""
from dataclasses import dataclass
from typing import Optional

from app.core.config import settings
from app.core.logging import logger


@dataclass
class OCRDecision:
    needs_ocr: bool
    reason: str  # "force_ocr" | "scan" | "low_density" | "native_text"


class OCRDetector:
    def __init__(
        self,
        min_text_chars: Optional[int] = None,
        min_text_density: Optional[float] = None,
        enabled: Optional[bool] = None,
    ):
        self.min_text_chars = (
            min_text_chars if min_text_chars is not None else settings.ocr_min_text_chars
        )
        self.min_text_density = (
            min_text_density if min_text_density is not None else settings.ocr_min_text_density
        )
        self.enabled = enabled if enabled is not None else settings.ocr_enabled

    def evaluate_page(
        self,
        text: str,
        page_width: float,
        page_height: float,
        image_count: int = 0,
        force_ocr: bool = False,
    ) -> OCRDecision:
        """Evaluate if an individual PDF page warrants OCR."""
        if not self.enabled:
            return OCRDecision(needs_ocr=False, reason="ocr_disabled")

        if force_ocr or settings.ocr_force:
            logger.info("OCR triggered by force_ocr flag")
            return OCRDecision(needs_ocr=True, reason="force_ocr")

        stripped_text = text.strip()
        text_length = len(stripped_text)

        # If page area is valid, compute character density
        area = max(1.0, page_width * page_height)
        density = text_length / area

        # Only route pages that contain embedded images to OCR automatically.
        # This preserves the native parser for text PDFs (including sparse pages,
        # such as cover pages or pages containing only a short heading).
        if image_count == 0:
            return OCRDecision(needs_ocr=False, reason="native_text")

        # 1. Very low text count on an image-containing page: likely a scan.
        if text_length < self.min_text_chars:
            logger.info(
                f"Page needs OCR: low text length ({text_length} < {self.min_text_chars}) with {image_count} images"
            )
            return OCRDecision(needs_ocr=True, reason="scan")

        # 2. Very low text density on an image-containing page.
        if density < self.min_text_density:
            logger.info(
                f"Page needs OCR: low text density ({density:.6f} < {self.min_text_density})"
            )
            return OCRDecision(needs_ocr=True, reason="low_density")

        return OCRDecision(needs_ocr=False, reason="native_text")
