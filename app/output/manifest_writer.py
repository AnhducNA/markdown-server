"""Manifest writer module for metadata and Qdrant chunk payloads."""
from pathlib import Path
from typing import List, Optional

from app.core.config import settings
from app.core.logging import logger
from app.models.document import BlockType, UnifiedDocument
from app.models.manifest import DocumentManifest, QdrantChunkPayload
from app.output.writer import sanitize_filename


class ManifestWriter:
    """Writes document manifests containing metadata and RAG chunk payloads."""

    def __init__(
        self,
        base_manifest_dir: Optional[Path] = None,
        overwrite: Optional[bool] = None,
    ):
        self.base_manifest_dir = Path(base_manifest_dir) if base_manifest_dir else settings.manifest_output_dir
        self.overwrite = settings.output_overwrite if overwrite is None else overwrite

    def get_manifest_path(self, document_id: str, tenant: Optional[str] = None) -> Path:
        """Get destination path for a document manifest JSON."""
        safe_id = sanitize_filename(document_id)
        if tenant:
            safe_tenant = sanitize_filename(tenant)
            return self.base_manifest_dir / safe_tenant / f"{safe_id}.json"
        return self.base_manifest_dir / f"{safe_id}.json"

    def _build_chunks(self, document: UnifiedDocument) -> List[QdrantChunkPayload]:
        """Convert document blocks into Qdrant-ready chunk payloads."""
        chunks: List[QdrantChunkPayload] = []
        doc_id = document.metadata.document_id
        source_type = document.metadata.source_type
        source = document.metadata.source_name

        for idx, block in enumerate(document.blocks):
            text = block.text or ""
            if not text.strip() and block.type == BlockType.TABLE and "rows" in block.attributes:
                rows = block.attributes["rows"]
                text = "\n".join(" | ".join(str(cell) for cell in row) for row in rows)
            elif not text.strip() and block.type == BlockType.IMAGE:
                text = block.attributes.get("path", "")

            chunk = QdrantChunkPayload(
                chunk_id=f"{doc_id}_chunk_{idx:04d}",
                document_id=doc_id,
                text=text,
                source_type=source_type,
                source=source,
                page=block.page,
                section_path=block.section_path or [],
                attributes=block.attributes or {},
            )
            chunks.append(chunk)

        return chunks

    def write_manifest(
        self,
        document: UnifiedDocument,
        markdown_path: Path,
        tenant: Optional[str] = None,
    ) -> Path:
        """Create and write manifest JSON for the given document."""
        manifest_path = self.get_manifest_path(document.metadata.document_id, tenant)
        manifest_path.parent.mkdir(parents=True, exist_ok=True)

        meta = document.metadata
        chunks = self._build_chunks(document)

        manifest = DocumentManifest(
            document_id=meta.document_id,
            title=meta.title,
            source_type=meta.source_type,
            source=meta.source_name,
            source_uri=meta.source_uri,
            language=meta.language,
            page_count=meta.page_count,
            parser=meta.parser,
            ocr_used=meta.ocr_used,
            ocr_engine=meta.ocr_engine,
            pages_ocr=meta.pages_ocr,
            created_at=meta.created_at,
            markdown_path=str(markdown_path.as_posix()),
            blocks_count=len(document.blocks),
            assets_count=len(document.assets),
            blocks=[b.model_dump() for b in document.blocks],
            assets=[a.model_dump() for a in document.assets],
            chunks=chunks,
        )

        manifest_path.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        logger.info(f"Wrote manifest to {manifest_path} ({len(chunks)} chunks)")
        return manifest_path
