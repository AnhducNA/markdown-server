"""Unit tests for Markdown validator."""
from app.processors.validator import MarkdownValidator


def test_validator_code_fence():
    validator = MarkdownValidator(strict=True)
    # Valid closed code fence
    valid_md = "# Title\n\n```python\nprint('hello')\n```\n"
    res = validator.validate(valid_md)
    assert res.is_valid
    assert len(res.errors) == 0

    # Unclosed fence
    invalid_md = "# Title\n\n```python\nprint('hello')\n"
    res_inv = validator.validate(invalid_md)
    assert not res_inv.is_valid
    assert any("Unclosed code fence" in err for err in res_inv.errors)


def test_validator_excessive_blank_lines():
    validator = MarkdownValidator(strict=True, max_blank_lines=1)
    text = "Paragraph 1\n\n\n\nParagraph 2"
    res = validator.validate(text)
    assert not res.is_valid
    assert any("consecutive blank lines" in err for err in res.errors)


def test_validator_table_mismatch():
    validator = MarkdownValidator(strict=True)
    bad_table = "| Col A | Col B |\n| --- | --- |\n| Val 1 | Val 2 | Val 3 |"
    res = validator.validate(bad_table)
    assert not res.is_valid
    assert any("Table column mismatch" in err for err in res.errors)
