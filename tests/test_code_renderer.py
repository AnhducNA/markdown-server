"""Unit tests for code block rendering."""
from app.models.document import BlockType, DocumentMetadata, UnifiedDocument
from app.renderers.markdown_renderer import MarkdownRenderer


def test_code_block_rendering():
    renderer = MarkdownRenderer(include_frontmatter=False, include_page_markers=False)
    meta = DocumentMetadata(document_id="d_code", source_type="pdf", source_name="code.pdf")
    doc = UnifiedDocument(metadata=meta)

    code_content = "def test():\n    return 42"
    doc.add_block(BlockType.CODE, code_content, attributes={"language": "python"})

    md = renderer.render(doc)
    assert "```python\ndef test():\n    return 42\n```" in md
