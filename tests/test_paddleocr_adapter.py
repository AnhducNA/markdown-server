"""Tests for PaddleOCR 3.x result handling without loading OCR models."""
from app.ocr.paddleocr_adapter import PaddleOCRAdapter


def test_extracts_paddleocr_v3_result_payload():
    payload = PaddleOCRAdapter._result_payload(
        {"res": {"rec_texts": ["Xin chao"], "rec_scores": [0.99], "rec_polys": []}}
    )

    assert payload["rec_texts"] == ["Xin chao"]
    assert payload["rec_scores"] == [0.99]


def test_extracts_direct_paddleocr_v3_payload():
    payload = PaddleOCRAdapter._result_payload({"rec_texts": ["Van ban"]})

    assert payload == {"rec_texts": ["Van ban"]}
