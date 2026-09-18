"""Unit tests for Output and Manifest Writers."""
import json
from pathlib import Path
from app.models.document import BlockType, DocumentMetadata, UnifiedDocument
from app.output.manifest_writer import ManifestWriter
from app.output.writer import MarkdownWriter, sanitize_filename


def test_sanitize_filename():
    assert sanitize_filename("../../etc/passwd") == "passwd"
    # on Windows, os.path.basename("doc:123/file*.md") yields "file*.md" -> sanitized to "file_.md"
    assert sanitize_filename("doc:123/file*.md") == "file_.md"
    assert sanitize_filename("") == "unnamed_document"


def test_markdown_and_manifest_writing(temp_output_dir: Path, sample_document: UnifiedDocument):
    writer = MarkdownWriter(base_output_dir=temp_output_dir / "markdown", overwrite=True)
    manifest_writer = ManifestWriter(base_manifest_dir=temp_output_dir / "manifest", overwrite=True)

    md_content = "# Sample Title\n\nContent here."
    md_path = writer.write(sample_document.metadata.document_id, md_content)
    assert md_path.exists()
    assert md_path.read_text(encoding="utf-8") == md_content

    manifest_path = manifest_writer.write_manifest(sample_document, md_path)
    assert manifest_path.exists()

    manifest_data = json.loads(manifest_path.read_text(encoding="utf-8"))
    assert manifest_data["document_id"] == "test_doc_001"
    assert len(manifest_data["chunks"]) > 0
    # Check Qdrant chunk payload format per section 13
    chunk0 = manifest_data["chunks"][0]
    assert "chunk_id" in chunk0
    assert "document_id" in chunk0
    assert "text" in chunk0
    assert "source_type" in chunk0
