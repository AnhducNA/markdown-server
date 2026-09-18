"""Unit tests for heading rendering."""
from app.models.document import Block, BlockType, DocumentMetadata, UnifiedDocument
from app.renderers.markdown_renderer import MarkdownRenderer


def test_heading_levels():
    renderer = MarkdownRenderer(include_frontmatter=False, include_page_markers=False)
    meta = DocumentMetadata(document_id="d1", source_type="pdf", source_name="doc.pdf")
    doc = UnifiedDocument(metadata=meta)

    for level in range(1, 7):
        doc.add_block(BlockType.HEADING, f"Heading Level {level}", level=level)

    md = renderer.render(doc)
    assert "# Heading Level 1" in md
    assert "## Heading Level 2" in md
    assert "### Heading Level 3" in md
    assert "#### Heading Level 4" in md
    assert "##### Heading Level 5" in md
    assert "###### Heading Level 6" in md


def test_heading_clamping():
    renderer = MarkdownRenderer(include_frontmatter=False, include_page_markers=False)
    meta = DocumentMetadata(document_id="d2", source_type="pdf", source_name="doc.pdf")
    doc = UnifiedDocument(metadata=meta)
    doc.add_block(BlockType.HEADING, "Too deep", level=10)

    md = renderer.render(doc)
    assert "###### Too deep" in md
