"""Markdown output writer and path management."""
import os
from pathlib import Path
import re
from typing import Optional

from app.core.config import settings
from app.core.logging import logger


def sanitize_filename(name: Optional[str]) -> str:
    """Sanitize a filename or ID to be filesystem-safe."""
    if not name:
        return "unnamed_document"

    clean = str(name).replace("\\", "/").rstrip("/")
    basename = os.path.basename(clean)
    if not basename:
        return "unnamed_document"

    sanitized = re.sub(r'[\\/:*?"<>|\x00-\x1f]', '_', basename)
    sanitized = sanitized.strip()
    return sanitized or "unnamed_document"


class MarkdownWriter:
    """Writes rendered markdown to the configured output directory."""

    def __init__(
        self,
        base_output_dir: Optional[Path] = None,
        overwrite: Optional[bool] = None,
    ):
        self.base_output_dir = Path(base_output_dir) if base_output_dir else settings.markdown_output_dir
        self.overwrite = settings.output_overwrite if overwrite is None else overwrite

    def get_output_path(self, document_id: str, tenant: Optional[str] = None) -> Path:
        """Get destination path for a markdown document."""
        safe_id = sanitize_filename(document_id)
        if tenant:
            safe_tenant = sanitize_filename(tenant)
            return self.base_output_dir / safe_tenant / f"{safe_id}.md"
        return self.base_output_dir / f"{safe_id}.md"

    def write(
        self,
        document_id: str,
        markdown_content: str,
        tenant: Optional[str] = None,
    ) -> Path:
        """Write markdown content to destination file and return path."""
        target_path = self.get_output_path(document_id, tenant)
        target_path.parent.mkdir(parents=True, exist_ok=True)

        if target_path.exists() and not self.overwrite:
            logger.warning(f"File {target_path} already exists. Overwriting per request.")

        target_path.write_text(markdown_content, encoding=settings.markdown_encoding)
        logger.info(f"Wrote markdown to {target_path}")
        return target_path
