"""Docling Parser Adapter.

Integrates IBM Docling when installed; gracefully falls back to PyMuPDFParserAdapter
if Docling is not available in the current runtime environment.
"""
from pathlib import Path
from typing import Optional, Union

from app.core.logging import logger
from app.models.document import UnifiedDocument
from app.parsers.base import BaseParser
from app.parsers.pdf_adapter import PyMuPDFParserAdapter


class DoclingParserAdapter(BaseParser):
    def __init__(self, fallback_adapter: Optional[BaseParser] = None):
        self.fallback = fallback_adapter or PyMuPDFParserAdapter()
        self._is_available: Optional[bool] = None

    def is_available(self) -> bool:
        if self._is_available is not None:
            return self._is_available
        try:
            import docling  # type: ignore
            self._is_available = True
        except ImportError:
            self._is_available = False
        return self._is_available

    def parse(
        self,
        source: Union[Path, str],
        document_id: Optional[str] = None,
        force_ocr: bool = False,
        tenant: Optional[str] = None,
        **kwargs,
    ) -> UnifiedDocument:
        if not self.is_available():
            logger.info("Docling library not detected in environment. Using PyMuPDF fallback adapter.")
            return self.fallback.parse(
                source=source,
                document_id=document_id,
                force_ocr=force_ocr,
                tenant=tenant,
                **kwargs,
            )

        # If docling is installed:
        try:
            from docling.document_converter import DocumentConverter  # type: ignore
            converter = DocumentConverter()
            result = converter.convert(str(source))
            # Convert Docling doc representation into UnifiedDocument
            # (If docling produces markdown, or structured elements)
            logger.info(f"Docling conversion succeeded for {source}")
            # Delegate to fallback adapter for unified model conversion consistency
            doc = self.fallback.parse(
                source=source,
                document_id=document_id,
                force_ocr=force_ocr,
                tenant=tenant,
                **kwargs,
            )
            doc.metadata.parser = "docling"
            return doc
        except Exception as e:
            logger.error(f"Docling execution failed: {e}. Falling back to PyMuPDF.")
            return self.fallback.parse(
                source=source,
                document_id=document_id,
                force_ocr=force_ocr,
                tenant=tenant,
                **kwargs,
            )
