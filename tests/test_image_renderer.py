"""Unit tests for image block rendering."""
from app.models.document import BlockType, DocumentMetadata, UnifiedDocument
from app.renderers.markdown_renderer import MarkdownRenderer


def test_image_block_rendering():
    renderer = MarkdownRenderer(include_frontmatter=False, include_page_markers=False)
    meta = DocumentMetadata(document_id="d_img", source_type="pdf", source_name="img.pdf")
    doc = UnifiedDocument(metadata=meta)

    doc.add_block(
        BlockType.IMAGE,
        "Mô tả hình ảnh",
        attributes={"path": "assets/d_img/chart.png"},
    )

    md = renderer.render(doc)
    assert "![Mô tả hình ảnh](assets/d_img/chart.png)" in md
