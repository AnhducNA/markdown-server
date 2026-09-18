"""Web Parser Adapter using Trafilatura and BeautifulSoup fallback.

Extracts the primary body content from web URLs, stripping away boilerplate,
navigation menus, headers, footers, and advertisements.
"""
from typing import Any, List, Optional, Union
import urllib.parse
import uuid
from bs4 import BeautifulSoup
import httpx
import trafilatura

from app.core.logging import logger
from app.models.document import BlockType, DocumentMetadata, UnifiedDocument
from app.parsers.base import BaseParser


class WebParserAdapter(BaseParser):
    def __init__(self, timeout: float = 20.0):
        self.timeout = timeout

    def fetch_url(self, url: str) -> str:
        """Fetch raw HTML using httpx with desktop User-Agent."""
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            resp = client.get(url, headers=headers)
            resp.raise_for_status()
            return resp.text

    def parse(
        self,
        source: Union[str, Any],
        document_id: Optional[str] = None,
        tenant: Optional[str] = None,
        **kwargs,
    ) -> UnifiedDocument:
        url = str(source).strip()
        doc_id = document_id or f"doc_{uuid.uuid4().hex[:8]}"

        parsed_url = urllib.parse.urlparse(url)
        domain = parsed_url.netloc

        logger.info(f"Extracting web content from: {url}")
        html = self.fetch_url(url)

        # 1. Try Trafilatura structured extraction
        extracted_xml = trafilatura.extract(
            html,
            output_format="xml",
            include_links=True,
            include_images=True,
            include_tables=True,
            url=url,
        )

        metadata_extract = trafilatura.extract_metadata(html)
        title = (
            metadata_extract.title
            if metadata_extract and metadata_extract.title
            else parsed_url.path.strip("/").split("/")[-1] or domain
        )

        metadata = DocumentMetadata(
            document_id=doc_id,
            title=title,
            source_type="web",
            source_name=domain,
            source_uri=url,
            language=metadata_extract.language if metadata_extract and metadata_extract.language else "vi",
            parser="trafilatura",
            tenant=tenant,
        )
        unified_doc = UnifiedDocument(metadata=metadata)

        current_section_path: List[str] = []
        if title:
            unified_doc.add_block(
                block_type=BlockType.HEADING,
                text=title,
                level=1,
                section_path=[title],
            )
            current_section_path = [title]

        if extracted_xml:
            # Parse XML output from Trafilatura
            soup = BeautifulSoup(extracted_xml, "xml")
            for elem in soup.find_all(["head", "p", "list", "table", "quote", "code"]):
                text = elem.get_text().strip()
                if not text:
                    continue

                if elem.name == "head":
                    raw_level = elem.get("rend", "h2")
                    level = 2
                    if raw_level and raw_level.startswith("h") and raw_level[1:].isdigit():
                        level = max(2, min(6, int(raw_level[1:])))
                    current_section_path = current_section_path[: max(0, level - 1)] + [text]
                    unified_doc.add_block(
                        block_type=BlockType.HEADING,
                        text=text,
                        level=level,
                        section_path=list(current_section_path),
                    )
                elif elem.name == "p":
                    unified_doc.add_block(
                        block_type=BlockType.PARAGRAPH,
                        text=text,
                        section_path=list(current_section_path),
                    )
                elif elem.name == "code":
                    unified_doc.add_block(
                        block_type=BlockType.CODE,
                        text=text,
                        section_path=list(current_section_path),
                    )
                elif elem.name == "quote":
                    unified_doc.add_block(
                        block_type=BlockType.QUOTE,
                        text=text,
                        section_path=list(current_section_path),
                    )
                elif elem.name == "list":
                    items = [item.get_text().strip() for item in elem.find_all("item") if item.get_text().strip()]
                    if items:
                        unified_doc.add_block(
                            block_type=BlockType.LIST,
                            text="\n".join(items),
                            section_path=list(current_section_path),
                            attributes={"items": items, "ordered": False},
                        )
        else:
            # Fallback to BeautifulSoup clean paragraph extraction
            logger.warning("Trafilatura returned empty result. Falling back to BeautifulSoup.")
            soup = BeautifulSoup(html, "html.parser")
            for tag in soup(["script", "style", "nav", "footer", "header", "noscript", "aside"]):
                tag.decompose()

            for elem in soup.find_all(["h1", "h2", "h3", "h4", "h5", "h6", "p"]):
                text = elem.get_text().strip()
                if not text:
                    continue
                if elem.name.startswith("h"):
                    level = int(elem.name[1])
                    current_section_path = current_section_path[: max(0, level - 1)] + [text]
                    unified_doc.add_block(
                        block_type=BlockType.HEADING,
                        text=text,
                        level=level,
                        section_path=list(current_section_path),
                    )
                else:
                    unified_doc.add_block(
                        block_type=BlockType.PARAGRAPH,
                        text=text,
                        section_path=list(current_section_path),
                    )

        return unified_doc
