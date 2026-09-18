"""Markdown Renderer implementation.

Conforms to Section 6, 7, 8, 9, 24.2 of the design document:
- Deterministic rendering of UnifiedDocument blocks
- Frontmatter YAML generation (configurable)
- Heading hierarchy (H1-H6)
- Standard GFM table formatting with cell newline normalization (<br> or space)
- Fenced code blocks with language support
- Image and link rendering with safe relative paths
- Page markers support (<!-- Page X -->)
- Integration with MarkdownNormalizer
"""
from typing import Any, Dict, List, Optional
import yaml

from app.core.config import settings
from app.models.document import Block, BlockType, UnifiedDocument
from app.processors.normalizer import MarkdownNormalizer


class MarkdownRenderer:
    def __init__(
        self,
        include_frontmatter: Optional[bool] = None,
        include_page_markers: Optional[bool] = None,
        max_blank_lines: int = 1,
    ):
        self.include_frontmatter = (
            include_frontmatter
            if include_frontmatter is not None
            else settings.markdown_include_frontmatter
        )
        self.include_page_markers = (
            include_page_markers
            if include_page_markers is not None
            else settings.markdown_include_page_markers
        )
        self.normalizer = MarkdownNormalizer(max_blank_lines=max_blank_lines)

    def render_frontmatter(self, document: UnifiedDocument) -> str:
        """Render YAML front matter per section 7 & 24.2."""
        meta = document.metadata
        frontmatter_dict: Dict[str, Any] = {
            "document_id": meta.document_id,
            "source_type": meta.source_type,
            "source_name": meta.source_name,
            "parser": meta.parser,
            "ocr_used": meta.ocr_used,
            "ocr_engine": meta.ocr_engine,
            "language": meta.language,
            "page_count": meta.page_count,
            "created_at": meta.created_at,
        }
        if meta.title:
            frontmatter_dict["title"] = meta.title
        if meta.source_uri:
            frontmatter_dict["source_uri"] = meta.source_uri
        if meta.tenant:
            frontmatter_dict["tenant"] = meta.tenant

        # Filter out None values
        clean_dict = {k: v for k, v in frontmatter_dict.items() if v is not None}
        yaml_str = yaml.dump(clean_dict, sort_keys=False, allow_unicode=True).strip()
        return f"---\n{yaml_str}\n---\n\n"

    def render_heading(self, block: Block) -> str:
        level = block.level or 1
        level = max(1, min(6, level))
        hashes = "#" * level
        return f"{hashes} {block.text.strip()}"

    def render_paragraph(self, block: Block) -> str:
        return block.text.strip()

    def render_code(self, block: Block) -> str:
        lang = block.attributes.get("language", "").strip()
        content = block.text.rstrip()
        return f"```{lang}\n{content}\n```"

    def render_quote(self, block: Block) -> str:
        lines = block.text.strip().split("\n")
        return "\n".join(f"> {line}" for line in lines)

    def render_image(self, block: Block) -> str:
        path = block.attributes.get("path", "")
        alt = block.text.strip() or "image"
        return f"![{alt}]({path})"

    def render_list(self, block: Block) -> str:
        ordered = block.attributes.get("ordered", False)
        items = block.attributes.get("items", [])
        if items:
            lines = []
            for i, item in enumerate(items, 1):
                clean_item = str(item).strip()
                prefix = f"{i}. " if ordered else "- "
                lines.append(f"{prefix}{clean_item}")
            return "\n".join(lines)
        
        # Fallback to block text
        lines = block.text.strip().split("\n")
        rendered = []
        for i, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
            if line.startswith("- ") or line.startswith("* ") or (len(line) > 2 and line[0].isdigit() and line[1] in ". "):
                rendered.append(line)
            else:
                prefix = f"{i}. " if ordered else "- "
                rendered.append(f"{prefix}{line}")
        return "\n".join(rendered)

    def render_table(self, block: Block) -> str:
        """Render table block to standard GFM table format."""
        # Check if table data is in attributes['rows'] or attributes['matrix']
        rows = block.attributes.get("rows") or block.attributes.get("matrix")
        if not rows:
            # Check if block.text already has a markdown table or text
            if "|" in block.text:
                return block.text.strip()
            return block.text.strip()

        # Sanitize cells (newlines inside cells -> <br>)
        cleaned_rows: List[List[str]] = []
        for row in rows:
            cleaned_row = []
            for cell in row:
                cell_str = str(cell if cell is not None else "").strip()
                cell_str = cell_str.replace("\r\n", "<br>").replace("\n", "<br>").replace("|", "\\|")
                cleaned_row.append(cell_str)
            cleaned_rows.append(cleaned_row)

        if not cleaned_rows:
            return ""

        col_count = max(len(r) for r in cleaned_rows)
        # Pad shorter rows
        for row in cleaned_rows:
            while len(row) < col_count:
                row.append("")

        header = cleaned_rows[0]
        separator = ["---"] * col_count
        body = cleaned_rows[1:] if len(cleaned_rows) > 1 else []

        lines = [
            "| " + " | ".join(header) + " |",
            "| " + " | ".join(separator) + " |",
        ]
        for r in body:
            lines.append("| " + " | ".join(r) + " |")

        return "\n".join(lines)

    def render_block(self, block: Block) -> str:
        match block.type:
            case BlockType.HEADING:
                return self.render_heading(block)
            case BlockType.PARAGRAPH:
                return self.render_paragraph(block)
            case BlockType.CODE:
                return self.render_code(block)
            case BlockType.QUOTE:
                return self.render_quote(block)
            case BlockType.IMAGE:
                return self.render_image(block)
            case BlockType.LIST:
                return self.render_list(block)
            case BlockType.TABLE:
                return self.render_table(block)
            case _:
                return block.text.strip()

    def render(self, document: UnifiedDocument) -> str:
        """Render the complete document into normalized Markdown."""
        parts: List[str] = []

        if self.include_frontmatter:
            parts.append(self.render_frontmatter(document).strip())

        last_page: Optional[int] = None

        for block in document.blocks:
            # Check for page transitions if page markers are enabled
            if self.include_page_markers and block.page is not None:
                if last_page is None or block.page != last_page:
                    parts.append(f"<!-- Page {block.page} -->")
                    last_page = block.page

            rendered_block = self.render_block(block)
            if rendered_block.strip():
                parts.append(rendered_block)

        raw_markdown = "\n\n".join(parts)
        return self.normalizer.normalize(raw_markdown)
