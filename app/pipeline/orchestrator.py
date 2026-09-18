"""Pipeline Orchestrator.

Selects and executes the appropriate pipeline based on file format or source URL.
"""
from pathlib import Path
from typing import Optional
from fastapi import HTTPException

from app.core.logging import logger
from app.models.api import ConvertResponse
from app.pipeline.docx_pipeline import DocxPipeline
from app.pipeline.pdf_pipeline import PDFPipeline
from app.pipeline.web_pipeline import WebPipeline


class PipelineOrchestrator:
    def __init__(self):
        self.pdf_pipeline = PDFPipeline()
        self.docx_pipeline = DocxPipeline()
        self.web_pipeline = WebPipeline()

    def process_file(
        self,
        file_path: Path,
        document_id: Optional[str] = None,
        force_ocr: bool = False,
        tenant: Optional[str] = None,
        include_frontmatter: Optional[bool] = None,
    ) -> ConvertResponse:
        suffix = file_path.suffix.lower()
        logger.info(f"Orchestrating file processing for {file_path.name} (type: {suffix})")

        if suffix == ".pdf":
            return self.pdf_pipeline.process(
                file_path=file_path,
                document_id=document_id,
                force_ocr=force_ocr,
                tenant=tenant,
                include_frontmatter=include_frontmatter,
            )
        elif suffix in {".docx", ".doc"}:
            return self.docx_pipeline.process(
                file_path=file_path,
                document_id=document_id,
                tenant=tenant,
                include_frontmatter=include_frontmatter,
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file type: {suffix}. Supported types: .pdf, .docx",
            )

    def process_url(
        self,
        url: str,
        document_id: Optional[str] = None,
        tenant: Optional[str] = None,
        include_frontmatter: Optional[bool] = None,
    ) -> ConvertResponse:
        logger.info(f"Orchestrating URL processing for {url}")
        return self.web_pipeline.process(
            url=url,
            document_id=document_id,
            tenant=tenant,
            include_frontmatter=include_frontmatter,
        )


orchestrator = PipelineOrchestrator()
