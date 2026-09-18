"""DOCX Parser Adapter using python-docx.

Extracts structured headings, paragraphs, lists, tables, and images from Word documents.
"""
from pathlib import Path
from typing import List, Optional, Union
import uuid
import docx

from app.core.logging import logger
from app.models.document import Asset, Block, BlockType, DocumentMetadata, UnifiedDocument
from app.parsers.base import BaseParser


class DocxParserAdapter(BaseParser):
    def parse(
        self,
        source: Union[Path, str],
        document_id: Optional[str] = None,
        tenant: Optional[str] = None,
        **kwargs,
    ) -> UnifiedDocument:
        source_path = Path(source)
        if not source_path.exists():
            raise FileNotFoundError(f"DOCX source file not found: {source_path}")

        doc_id = document_id or f"doc_{uuid.uuid4().hex[:8]}"
        doc = docx.Document(str(source_path))

        metadata = DocumentMetadata(
            document_id=doc_id,
            title=source_path.stem.replace("_", " "),
            source_type="docx",
            source_name=source_path.name,
            source_uri=str(source_path.as_posix()),
            page_count=None,
            parser="python-docx",
            tenant=tenant,
        )

        unified_doc = UnifiedDocument(metadata=metadata)
        current_section_path: List[str] = []
        image_counter = 1

        # Iterate document elements in sequence (paragraphs and tables)
        for element in doc.element.body:
            tag = element.tag.split("}")[-1] if "}" in element.tag else element.tag

            if tag == "p":
                # Paragraph element
                p = docx.text.paragraph.Paragraph(element, doc)
                text = p.text.strip()
                if not text:
                    continue

                style_name = p.style.name.lower() if p.style and p.style.name else ""

                if "heading" in style_name:
                    # Extract heading level
                    level = 1
                    for digit in style_name:
                        if digit.isdigit():
                            level = int(digit)
                            break
                    current_section_path = current_section_path[: max(0, level - 1)] + [text]
                    unified_doc.add_block(
                        block_type=BlockType.HEADING,
                        text=text,
                        level=level,
                        section_path=list(current_section_path),
                    )
                    if unified_doc.metadata.title is None and level == 1:
                        unified_doc.metadata.title = text

                elif "list bullet" in style_name or style_name.startswith("bullet"):
                    unified_doc.add_block(
                        block_type=BlockType.LIST,
                        text=text,
                        section_path=list(current_section_path),
                        attributes={"ordered": False, "items": [text]},
                    )
                elif "list number" in style_name:
                    unified_doc.add_block(
                        block_type=BlockType.LIST,
                        text=text,
                        section_path=list(current_section_path),
                        attributes={"ordered": True, "items": [text]},
                    )
                elif "code" in style_name or "console" in style_name:
                    unified_doc.add_block(
                        block_type=BlockType.CODE,
                        text=text,
                        section_path=list(current_section_path),
                    )
                elif "quote" in style_name:
                    unified_doc.add_block(
                        block_type=BlockType.QUOTE,
                        text=text,
                        section_path=list(current_section_path),
                    )
                else:
                    unified_doc.add_block(
                        block_type=BlockType.PARAGRAPH,
                        text=text,
                        section_path=list(current_section_path),
                    )

            elif tag == "tbl":
                # Table element
                t = docx.table.Table(element, doc)
                matrix = []
                for row in t.rows:
                    row_data = [cell.text.strip() for cell in row.cells]
                    matrix.append(row_data)

                if matrix:
                    unified_doc.add_block(
                        block_type=BlockType.TABLE,
                        text="",
                        section_path=list(current_section_path),
                        attributes={"rows": matrix},
                    )

        # Extract images from relationships
        try:
            for rel in doc.part.rels.values():
                if "image" in rel.target_ref:
                    image_part = rel.target_part
                    img_bytes = image_part.blob
                    ext = image_part.content_type.split("/")[-1] if "/" in image_part.content_type else "png"
                    if ext == "jpeg":
                        ext = "jpg"

                    img_name = f"docx_image_{image_counter:03d}.{ext}"
                    image_counter += 1
                    rel_path = f"assets/{doc_id}/{img_name}"

                    asset = Asset(
                        name=img_name,
                        relative_path=rel_path,
                        mime_type=image_part.content_type,
                        data=img_bytes,
                        size_bytes=len(img_bytes),
                    )
                    unified_doc.assets.append(asset)
                    unified_doc.add_block(
                        block_type=BlockType.IMAGE,
                        text=f"Embedded image {img_name}",
                        section_path=list(current_section_path),
                        attributes={"path": rel_path},
                    )
        except Exception as e:
            logger.warning(f"Error extracting images from DOCX: {e}")

        return unified_doc
