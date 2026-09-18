"""Unit tests for Markdown normalizer."""
from app.processors.normalizer import MarkdownNormalizer


def test_normalizer_blank_lines():
    normalizer = MarkdownNormalizer(max_blank_lines=1)
    text = "Paragraph 1\n\n\n\n\nParagraph 2"
    res = normalizer.normalize(text)
    assert res == "Paragraph 1\n\nParagraph 2\n"


def test_normalizer_heading_spaces():
    normalizer = MarkdownNormalizer()
    text = "#Title\n##Subtitle\n###  Deep"
    res = normalizer.normalize(text)
    assert "# Title" in res
    assert "## Subtitle" in res
    assert "### Deep" in res


def test_normalizer_crlf():
    normalizer = MarkdownNormalizer()
    text = "Line 1\r\nLine 2\rLine 3"
    res = normalizer.normalize(text)
    assert "\r" not in res
    assert "Line 1\nLine 2\nLine 3\n" == res


def test_normalizer_unicode_nfc():
    normalizer = MarkdownNormalizer()
    # Decomposed Vietnamese char (e + combining acute)
    decomposed = "e\u0301"
    res = normalizer.normalize(decomposed)
    # NFC unified acute
    assert res == "é\n"
