"""Ingestion and file handling module."""
from pathlib import Path
from typing import Optional
import uuid
from fastapi import HTTPException, UploadFile

from app.core.config import settings
from app.core.logging import logger
from app.output.writer import sanitize_filename

ALLOWED_EXTENSIONS = {".pdf", ".docx", ".doc"}


class FileHandler:
    def __init__(self, upload_dir: Optional[Path] = None):
        self.upload_dir = upload_dir or (settings.tmp_dir / "uploads")
        self.upload_dir.mkdir(parents=True, exist_ok=True)

    def validate_extension(self, filename: str) -> str:
        """Validate and return file extension."""
        ext = Path(filename).suffix.lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"Unsupported file format '{ext}'. Supported formats: {list(ALLOWED_EXTENSIONS)}",
            )
        return ext

    async def save_upload(
        self,
        file: UploadFile,
        document_id: Optional[str] = None,
    ) -> tuple[str, Path]:
        """Save uploaded file to temporary directory and return (document_id, file_path)."""
        filename = file.filename or "uploaded_file"
        self.validate_extension(filename)

        doc_id = document_id or f"doc_{uuid.uuid4().hex[:8]}"
        safe_doc_id = sanitize_filename(doc_id)
        safe_name = sanitize_filename(filename)

        doc_upload_dir = self.upload_dir / safe_doc_id
        doc_upload_dir.mkdir(parents=True, exist_ok=True)
        dest_path = doc_upload_dir / safe_name

        try:
            content = await file.read()
            dest_path.write_bytes(content)
            logger.info(f"Saved uploaded file to {dest_path} ({len(content)} bytes)")
        except Exception as e:
            logger.error(f"Failed to write uploaded file: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to save uploaded file: {str(e)}")

        return safe_doc_id, dest_path
