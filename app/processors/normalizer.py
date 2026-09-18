"""Markdown Normalizer implementation.

Conforms to Section 10 of the design specification:
- Unicode NFC normalization
- Line endings normalization (LF)
- Collapse redundant blank lines to maximum allowed
- Normalize heading format (ensure space after #)
- Normalize Markdown tables and clean cell whitespace
- Trailing whitespace removal
"""
import re
import unicodedata
from typing import List


class MarkdownNormalizer:
    def __init__(self, max_blank_lines: int = 1):
        self.max_blank_lines = max_blank_lines

    def normalize_unicode(self, text: str) -> str:
        """Normalize Unicode to NFC form."""
        return unicodedata.normalize("NFC", text)

    def normalize_line_endings(self, text: str) -> str:
        """Convert all line endings (CRLF, CR) to standard LF."""
        text = text.replace("\r\n", "\n").replace("\r", "\n")
        return text

    def collapse_blank_lines(self, text: str) -> str:
        """Collapse multiple consecutive blank lines to at most `max_blank_lines`."""
        # For max_blank_lines = 1, consecutive newlines should be at most 2 (\n\n)
        allowed_newlines = self.max_blank_lines + 1
        pattern = r"\n{" + str(allowed_newlines + 1) + r",}"
        replacement = "\n" * allowed_newlines
        return re.sub(pattern, replacement, text)

    def remove_trailing_whitespace(self, text: str) -> str:
        """Strip trailing whitespace from each line while preserving indentation."""
        lines = [line.rstrip() for line in text.split("\n")]
        return "\n".join(lines)

    def normalize_headings(self, text: str) -> str:
        """Ensure there is a single space after # symbols in headings."""
        # Match lines like #Title or ###  Title
        def fix_heading(match):
            hashes = match.group(1)
            content = match.group(2).strip()
            return f"{hashes} {content}"

        return re.sub(r"^(#{1,6})[ \t]*(.*?)$", fix_heading, text, flags=re.MULTILINE)

    def normalize_tables(self, text: str) -> str:
        """Normalize table separators and whitespace within table rows."""
        lines = text.split("\n")
        normalized_lines: List[str] = []
        in_table = False

        for line in lines:
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                in_table = True
                # Split on | that are NOT preceded by a backslash
                raw_cells = re.split(r"(?<!\\)\|", stripped)[1:-1]
                cells = [c.strip() for c in raw_cells]

                # Check if it's a separator line (e.g. |---|:---|)
                is_separator = all(re.match(r"^:?-+:?$", c) for c in cells if c)
                if is_separator:
                    normalized_cells = [
                        re.sub(r"-+", "---", c) if c else "---" for c in cells
                    ]
                    normalized_lines.append("| " + " | ".join(normalized_cells) + " |")
                else:
                    normalized_lines.append("| " + " | ".join(cells) + " |")
            else:
                in_table = False
                normalized_lines.append(line)

        return "\n".join(normalized_lines)

    def normalize(self, text: str) -> str:
        """Run the complete normalization sequence."""
        text = self.normalize_unicode(text)
        text = self.normalize_line_endings(text)
        text = self.remove_trailing_whitespace(text)
        text = self.collapse_blank_lines(text)
        text = self.normalize_headings(text)
        text = self.normalize_tables(text)
        return text.strip() + "\n"
