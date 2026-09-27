# PaddleOCR PDF to Markdown API Server

This project converts PDF documents into page images, performs OCR using PaddleOCR (Vietnamese support), and returns or saves the recognized text in Markdown format via a **FastAPI Web API Server**.

---

## Project Structure

- `app/main.py` — FastAPI application & OCR conversion pipeline
- `Dockerfile` — Docker environment containerizing Python, Poppler, OpenCV, and PaddleOCR
- `docker-compose.yml` — Docker Compose configuration exposing port `6868`
- `requirements.txt` — Python package dependencies
- `input/` / `output/` — Mount directories for file persistence if needed

---

## Getting Started

### 1. Run with Docker Compose (Recommended)

Start the API server:

```bash
docker compose up --build
```

### Update new source: 
```bash
docker compose up -d --build
```

The server will start on `http://localhost:6868`.

- **Swagger UI Interactive Documentation**: Open `http://localhost:6868/docs` in your browser.
- **ReDoc Documentation**: Open `http://localhost:6868/redoc`.

---

## API Endpoints

### 1. Health Check
- **`GET /health`**
- Returns server status.
```json
{
  "status": "healthy"
}
```

### 2. Convert PDF File to Markdown
- **`POST /convert`**
- **Content-Type**: `multipart/form-data`
- **Body Parameter**: `file` (PDF file)
- **Query Parameter (Optional)**: `download=true` (If set to `true`, downloads the generated `.md` file directly instead of returning JSON)

#### Request Example using `curl`:

**Return JSON:**
```bash
curl -X POST "http://localhost:6868/convert" \
  -F "file=@/path/to/your/document.pdf"
```

**JSON Response Example:**
```json
{
  "filename": "document.pdf",
  "markdown": "# document\n\n## Trang 1\n\nNội dung văn bản nhận diện được..."
}
```

**Download Markdown File directly:**
```bash
curl -X POST "http://localhost:6868/convert?download=true" \
  -F "file=@/path/to/your/document.pdf" \
  -o "output.md"
```

#### Request Example using Python (`requests`):

```python
import requests

url = "http://localhost:6868/convert"
files = {"file": open("document.pdf", "rb")}

response = requests.post(url, files=files)
data = response.json()

print(data["markdown"])
```

---

## CLI Mode (Optional)

You can also execute single-file conversion directly via Python CLI:

```bash
python app/main.py --input input/sample.pdf --output output
```

---

## Notes & Technical Details

- **Model Preloading**: PaddleOCR is initialized once on server startup, avoiding model loading overhead per request.
- **Isolated Storage**: Each request is processed inside a temporary directory and automatically cleaned up upon completion.
