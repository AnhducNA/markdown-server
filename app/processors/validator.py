"""Markdown Validator implementation.

Follows the Validation Checklist in Section 18 of the design document:
- UTF-8 compliance
- Title and heading hierarchy checks
- No redundant consecutive blank lines
- Table structure integrity (matching pipe columns and separators)
- Code fence closure integrity
- Link and image path safety
"""
from pathlib import Path
import re
from typing import List, Optional
from pydantic import BaseModel, Field


class ValidationResult(BaseModel):
    is_valid: bool = True
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


class MarkdownValidator:
    def __init__(self, strict: bool = True, max_blank_lines: int = 1):
        self.strict = strict
        self.max_blank_lines = max_blank_lines

    def validate(self, markdown_text: str, base_asset_dir: Optional[Path] = None) -> ValidationResult:
        result = ValidationResult()

        # 1. UTF-8 Validation
        try:
            markdown_text.encode("utf-8")
        except UnicodeEncodeError as e:
            result.errors.append(f"Invalid UTF-8 encoding: {e}")

        # 2. Consecutive Blank Lines Check
        allowed_newlines = self.max_blank_lines + 1
        excessive_blank_pattern = r"\n{" + str(allowed_newlines + 1) + r",}"
        if re.search(excessive_blank_pattern, markdown_text):
            msg = f"Found more than {self.max_blank_lines} consecutive blank lines."
            if self.strict:
                result.errors.append(msg)
            else:
                result.warnings.append(msg)

        # 3. Code fence closure check
        lines = markdown_text.split("\n")
        fence_count = 0
        in_code_fence = False
        for line in lines:
            if line.strip().startswith("```"):
                fence_count += 1
                in_code_fence = not in_code_fence
        if in_code_fence:
            result.errors.append(f"Unclosed code fence: total count of ``` is {fence_count} (odd number).")

        # 4. Heading hierarchy check
        headings: List[int] = []
        for line in lines:
            match = re.match(r"^(#{1,6})\s+(.*)$", line)
            if match:
                headings.append(len(match.group(1)))

        # Heading check: not more than one H1 if document has multiple sections
        h1_count = sum(1 for h in headings if h == 1)
        if h1_count > 1:
            result.warnings.append(f"Multiple H1 headings detected ({h1_count}). Document should ideally have one main title H1.")

        # Heading skip check (e.g. H1 to H4)
        for i in range(len(headings) - 1):
            curr, nxt = headings[i], headings[i + 1]
            if nxt > curr + 1:
                result.warnings.append(f"Heading hierarchy jump detected from H{curr} to H{nxt}.")

        # 5. Table validation check
        in_table = False
        col_count = 0
        for idx, line in enumerate(lines, start=1):
            stripped = line.strip()
            if stripped.startswith("|") and stripped.endswith("|"):
                cells = [c.strip() for c in stripped.split("|")[1:-1]]
                if not in_table:
                    in_table = True
                    col_count = len(cells)
                else:
                    if len(cells) != col_count:
                        result.errors.append(f"Table column mismatch at line {idx}: expected {col_count} columns, found {len(cells)}.")
            else:
                in_table = False

        # 6. Image & link path safety check
        image_matches = re.findall(r"!\[(.*?)\]\((.*?)\)", markdown_text)
        for alt, img_path in image_matches:
            clean_path = img_path.split()[0].strip()  # remove potential title
            if ".." in clean_path or clean_path.startswith("/"):
                result.warnings.append(f"Suspicious asset path: '{clean_path}'. Relative path recommended.")
            if base_asset_dir:
                # If asset check is requested, verify existence
                target = (base_asset_dir / clean_path).resolve()
                if not target.exists():
                    result.warnings.append(f"Referenced asset does not exist on disk: {clean_path}")

        if result.errors:
            result.is_valid = False

        return result
