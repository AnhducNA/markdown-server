# Markdown Output API Server

Hệ thống API Server chuyển đổi tài liệu đa nguồn (**PDF**, **DOCX**, **Web URL**) thành **Markdown chuẩn hóa** và **Unified Document Model (JSON)** phục vụ pipeline RAG (Retrieval-Augmented Generation).

## Tính năng chính

- **Unified Document Model**: Cấu trúc dữ liệu phân tầng theo khối (`blocks`), bảo toàn `level`, `section_path`, `page`, `bbox`, `confidence`.
- **Hỗ trợ đa định dạng**:
  - **PDF**: Hỗ trợ native layout parser (PyMuPDF) và Docling adapter.
  - **DOCX**: Giữ nguyên heading hierarchy, bảng, ảnh, code.
  - **Web**: Bóc tách nội dung chính loại bỏ quảng cáo và menu qua Trafilatura / BeautifulSoup.
- **Tích hợp OCR thông minh (PaddleOCR Adapter & OCR Detector)**:
  - Tự động phát hiện trang quét (scan) hoặc ít chữ theo ngưỡng `text_length` và `text_density`.
  - Chỉ OCR các trang cần thiết, tối ưu thời gian xử lý và tài nguyên.
- **Markdown Renderer & Normalizer**:
  - Chuẩn hóa Unicode NFC, ngắt dòng, dòng trống liên tiếp, GFM tables, code fences.
  - Hỗ trợ YAML Frontmatter và Page Markers theo cấu hình.
- **Traceability & Qdrant Readiness**:
  - Xuất song song `document.md`, `document.json` (manifest) và thư mục `assets/`.
  - Có thể tái tạo Qdrant payload từ manifest JSON mà không cần đọc lại file gốc.
- **RESTful API**: Xây dựng trên FastAPI với Swagger UI tài liệu hóa đầy đủ.

## Cài đặt & Chạy server

```bash
# Cài đặt môi trường ảo và dependencies với uv
uv venv
.\.venv\Scripts\activate
uv pip install -e .

# Khởi chạy server
uv run uvicorn app.main:app --reload --port 8000
```
