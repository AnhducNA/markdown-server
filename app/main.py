import argparse
from contextlib import asynccontextmanager
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import List, Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from paddleocr import PaddleOCR
import uvicorn

# Global OCR instance
ocr_engine: Optional[PaddleOCR] = None


def get_ocr_engine() -> PaddleOCR:
    global ocr_engine
    if ocr_engine is None:
        print("[INFO] Initializing PaddleOCR engine...")
        ocr_engine = PaddleOCR(
            use_angle_cls=True,
            lang="vi",
            use_gpu=False,
        )
    return ocr_engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load PaddleOCR model once
    get_ocr_engine()
    yield
    # Shutdown logic if needed


app = FastAPI(
    title="PDF to Markdown OCR API Server",
    description="API Server using PaddleOCR to convert PDF documents into Markdown text.",
    version="1.0.0",
    lifespan=lifespan,
)


def pdf_to_images(pdf_path: str, output_dir: str) -> List[Path]:
    """
    Convert PDF pages to PNG images using pdftoppm.
    """
    os.makedirs(output_dir, exist_ok=True)
    prefix = os.path.join(output_dir, "page")

    command = [
        "pdftoppm",
        "-png",
        "-r",
        "200",
        pdf_path,
        prefix,
    ]

    print(f"[INFO] Converting PDF: {pdf_path}")
    subprocess.run(command, check=True)

    images = sorted(Path(output_dir).glob("page-*.png"))
    print(f"[INFO] Generated {len(images)} page images")
    return images


def clean_text(text: str) -> str:
    """
    Basic Markdown cleanup.
    """
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def ocr_image(ocr: PaddleOCR, image_path: Path) -> List[str]:
    """
    Run PaddleOCR on one image.
    """
    print(f"[OCR] Processing: {image_path}")
    result = ocr.ocr(str(image_path), cls=True)

    page_lines = []
    if result and result[0]:
        for line in result[0]:
            text = line[1][0]
            text = clean_text(text)
            if text:
                page_lines.append(text)

    return page_lines


def generate_markdown(pdf_name: str, pages: List[List[str]]) -> str:
    """
    Generate Markdown document text from OCR pages.
    """
    md = []
    stem = Path(pdf_name).stem
    md.append(f"# {stem}")
    md.append("")

    for page_number, lines in enumerate(pages, start=1):
        md.append(f"## Trang {page_number}")
        md.append("")
        for line in lines:
            md.append(line)
        md.append("")

    return "\n".join(md)


def process_pdf_file(pdf_path: Path) -> str:
    """
    Process a PDF file and return generated Markdown content.
    """
    ocr = get_ocr_engine()
    with tempfile.TemporaryDirectory() as temp_dir:
        image_dir = Path(temp_dir) / "_pages"
        images = pdf_to_images(str(pdf_path), str(image_dir))

        if not images:
            raise RuntimeError("No images generated from PDF")

        pages = []
        for image in images:
            lines = ocr_image(ocr, image)
            pages.append(lines)

        return generate_markdown(pdf_path.name, pages)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to PDF to Markdown OCR API Server",
        "endpoints": {
            "health": "/health",
            "convert": "/convert (POST multipart/form-data with 'file')",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "healthy"}


@app.post("/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    download: bool = Query(
        False, description="If true, downloads the result as a .md file"
    ),
):
    """
    Upload a PDF file and convert it into Markdown format using PaddleOCR.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Only PDF files are supported."
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_pdf_path = Path(temp_dir) / file.filename
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            markdown_content = process_pdf_file(temp_pdf_path)
        except Exception as e:
            print(f"[ERROR] Processing failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to process PDF: {str(e)}"
            )

    if download:
        stem = Path(file.filename).stem
        return Response(
            content=markdown_content,
            media_type="text/markdown; charset=utf-8",
            headers={
                "Content-Disposition": f'attachment; filename="{stem}.md"'
            },
        )

    return {
        "filename": file.filename,
        "markdown": markdown_content,
    }


def main():
    parser = argparse.ArgumentParser(description="PDF to Markdown API / CLI")
    parser.add_argument("--input", help="Input PDF file for CLI execution")
    parser.add_argument("--output", help="Output directory for CLI execution")
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host address for API server"
    )
    parser.add_argument(
        "--port", type=int, default=8000, help="Port for API server"
    )

    args = parser.parse_args()

    if args.input and args.output:
        # Run CLI mode
        pdf_path = Path(args.input)
        output_dir = Path(args.output)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        markdown = process_pdf_file(pdf_path)

        output_file = output_dir / f"{pdf_path.stem}.md"
        output_file.write_text(markdown, encoding="utf-8")

        print("=" * 60)
        print("[SUCCESS]")
        print(f"Markdown: {output_file}")
        print("=" * 60)
    else:
        # Run API server mode
        uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()