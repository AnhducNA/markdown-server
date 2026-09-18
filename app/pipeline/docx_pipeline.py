"""DOCX Processing Pipeline."""
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.core.logging import logger
from app.models.api import ConvertResponse
from app.output.asset_writer import AssetWriter
from app.output.manifest_writer import ManifestWriter
from app.output.writer import MarkdownWriter
from app.parsers.docx_adapter import DocxParserAdapter
from app.pipeline.base import BasePipeline
from app.processors.validator import MarkdownValidator
from app.renderers.markdown_renderer import MarkdownRenderer


class DocxPipeline(BasePipeline):
    def __init__(
        self,
        parser: Optional[DocxParserAdapter] = None,
        renderer: Optional[MarkdownRenderer] = None,
        writer: Optional[MarkdownWriter] = None,
        asset_writer: Optional[AssetWriter] = None,
        manifest_writer: Optional[ManifestWriter] = None,
        validator: Optional[MarkdownValidator] = None,
    ):
        self.parser = parser or DocxParserAdapter()
        self.renderer = renderer or MarkdownRenderer()
        self.writer = writer or MarkdownWriter()
        self.asset_writer = asset_writer or AssetWriter()
        self.manifest_writer = manifest_writer or ManifestWriter()
        self.validator = validator or MarkdownValidator(strict=settings.markdown_strict_validation)

    def process(
        self,
        file_path: Path,
        document_id: Optional[str] = None,
        tenant: Optional[str] = None,
        include_frontmatter: Optional[bool] = None,
    ) -> ConvertResponse:
        logger.info(f"Starting DOCX pipeline for file: {file_path}")

        # 1. Parse DOCX into Unified Document Model
        unified_doc = self.parser.parse(
            source=file_path,
            document_id=document_id,
            tenant=tenant,
        )

        # 2. Render Markdown
        renderer = self.renderer
        if include_frontmatter is not None:
            renderer = MarkdownRenderer(include_frontmatter=include_frontmatter)
        markdown_text = renderer.render(unified_doc)

        # 3. Validate Markdown
        validation = self.validator.validate(markdown_text)
        if not validation.is_valid and settings.markdown_strict_validation:
            raise ValueError(f"Strict markdown validation failed: {'; '.join(validation.errors)}")

        # 4. Save Assets
        self.asset_writer.write_assets(
            document_id=unified_doc.metadata.document_id,
            assets=unified_doc.assets,
            tenant=tenant,
        )

        # 5. Write Markdown Output
        md_path = self.writer.write(
            document_id=unified_doc.metadata.document_id,
            markdown_content=markdown_text,
            tenant=tenant,
        )

        # 6. Write Manifest
        manifest_path = self.manifest_writer.write_manifest(
            document=unified_doc,
            markdown_path=md_path,
            tenant=tenant,
        )

        meta = unified_doc.metadata
        return ConvertResponse(
            document_id=meta.document_id,
            status="completed",
            markdown_path=str(md_path.as_posix()),
            metadata_path=str(manifest_path.as_posix()),
            assets_count=len(unified_doc.assets),
            page_count=None,
            ocr_used=False,
            pages_ocr=[],
            created_at=meta.created_at,
        )
