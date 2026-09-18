"""Test suite configuration."""
import pytest
from pathlib import Path
import shutil

from app.core.config import settings
from app.models.document import Block, BlockType, DocumentMetadata, UnifiedDocument


@pytest.fixture
def sample_document() -> UnifiedDocument:
    meta = DocumentMetadata(
        document_id="test_doc_001",
        title="Tài liệu kiểm thử",
        source_type="pdf",
        source_name="test.pdf",
        language="vi",
        page_count=2,
    )
    doc = UnifiedDocument(metadata=meta)
    doc.add_block(BlockType.HEADING, "Tài liệu kiểm thử", level=1, page=1, section_path=["Tài liệu kiểm thử"])
    doc.add_block(BlockType.HEADING, "Chương 1: Giới thiệu", level=2, page=1, section_path=["Tài liệu kiểm thử", "Chương 1: Giới thiệu"])
    doc.add_block(BlockType.PARAGRAPH, "Đây là đoạn văn bản tiếng Việt có dấu đầy đủ.", page=1)
    doc.add_block(
        BlockType.TABLE,
        "",
        page=1,
        attributes={"rows": [["Cột A", "Cột B"], ["Giá trị 1", "Giá trị 2\nXuống dòng"]]},
    )
    doc.add_block(
        BlockType.CODE,
        "def hello():\n    return 'world'",
        page=2,
        attributes={"language": "python"},
    )
    doc.add_block(
        BlockType.IMAGE,
        "Sơ đồ kiến trúc",
        page=2,
        attributes={"path": "assets/test_doc_001/diagram.png"},
    )
    return doc


@pytest.fixture
def temp_output_dir(tmp_path: Path):
    test_out = tmp_path / "test_output"
    test_out.mkdir(parents=True, exist_ok=True)
    orig_output = settings.output_dir
    orig_md = settings.markdown_output_dir
    orig_manifest = settings.manifest_output_dir
    orig_asset = settings.asset_output_dir

    settings.output_dir = test_out
    settings.markdown_output_dir = test_out / "markdown"
    settings.manifest_output_dir = test_out / "manifest"
    settings.asset_output_dir = test_out / "assets"
    settings.ensure_directories()

    yield test_out

    settings.output_dir = orig_output
    settings.markdown_output_dir = orig_md
    settings.manifest_output_dir = orig_manifest
    settings.asset_output_dir = orig_asset
