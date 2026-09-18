"""Unit tests for frontmatter rendering."""
import yaml
from app.models.document import DocumentMetadata, UnifiedDocument
from app.renderers.markdown_renderer import MarkdownRenderer


def test_frontmatter_presence():
    renderer = MarkdownRenderer(include_frontmatter=True, include_page_markers=False)
    meta = DocumentMetadata(
        document_id="doc_xyz",
        title="Tài liệu Test Frontmatter",
        source_type="pdf",
        source_name="xyz.pdf",
        language="vi",
        page_count=10,
    )
    doc = UnifiedDocument(metadata=meta)
    md = renderer.render(doc)

    assert md.startswith("---")
    parts = md.split("---")
    assert len(parts) >= 3
    fm_content = parts[1]
    parsed_yaml = yaml.safe_load(fm_content)

    assert parsed_yaml["document_id"] == "doc_xyz"
    assert parsed_yaml["title"] == "Tài liệu Test Frontmatter"
    assert parsed_yaml["source_type"] == "pdf"
    assert parsed_yaml["language"] == "vi"
    assert parsed_yaml["page_count"] == 10
