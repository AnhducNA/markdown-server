"""Unit tests for table rendering."""
from app.models.document import BlockType, DocumentMetadata, UnifiedDocument
from app.renderers.markdown_renderer import MarkdownRenderer


def test_table_gfm_rendering():
    renderer = MarkdownRenderer(include_frontmatter=False, include_page_markers=False)
    meta = DocumentMetadata(document_id="d_tbl", source_type="docx", source_name="table.docx")
    doc = UnifiedDocument(metadata=meta)

    table_data = [
        ["Header 1", "Header 2", "Header 3"],
        ["Cell 1", "Cell 2\nmultiline", "Cell 3|pipe"],
        ["Cell 4", "Cell 5", "Cell 6"],
    ]
    doc.add_block(BlockType.TABLE, "", attributes={"rows": table_data})

    md = renderer.render(doc)
    assert "| Header 1 | Header 2 | Header 3 |" in md
    assert "| --- | --- | --- |" in md
    assert "Cell 2<br>multiline" in md
    assert "Cell 3\\|pipe" in md
