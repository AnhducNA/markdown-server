"""Unit tests for OCR Detector logic."""
from app.ocr.detector import OCRDetector


def test_ocr_detector_force():
    detector = OCRDetector()
    decision = detector.evaluate_page(
        text="Lots of rich text here on page.",
        page_width=595.0,
        page_height=842.0,
        force_ocr=True,
    )
    assert decision.needs_ocr
    assert decision.reason == "force_ocr"


def test_ocr_detector_low_text():
    detector = OCRDetector(min_text_chars=30)
    decision = detector.evaluate_page(
        text="Short",
        page_width=595.0,
        page_height=842.0,
        image_count=0,
        force_ocr=False,
    )
    assert decision.needs_ocr
    assert decision.reason == "low_text"


def test_ocr_detector_scan_page():
    detector = OCRDetector(min_text_chars=30)
    decision = detector.evaluate_page(
        text="A",
        page_width=595.0,
        page_height=842.0,
        image_count=1,
        force_ocr=False,
    )
    assert decision.needs_ocr
    assert decision.reason == "scan"


def test_ocr_detector_native_text():
    detector = OCRDetector(min_text_chars=30, min_text_density=0.0005)
    long_text = "Tài liệu này chứa rất nhiều văn bản đầy đủ và rõ ràng trên một trang tài liệu tiêu chuẩn." * 5
    decision = detector.evaluate_page(
        text=long_text,
        page_width=595.0,
        page_height=842.0,
        image_count=0,
        force_ocr=False,
    )
    assert not decision.needs_ocr
    assert decision.reason == "native_text"
