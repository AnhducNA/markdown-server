import argparse
from contextlib import asynccontextmanager
import os
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
from typing import List, Optional
import unicodedata
from urllib.parse import quote

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.responses import Response
from paddleocr import PaddleOCR
from PIL import Image
import uvicorn

try:
    from vietocr.tool.config import Cfg
    from vietocr.tool.predictor import Predictor

    VIETOCR_AVAILABLE = True
except ImportError:
    VIETOCR_AVAILABLE = False

# Global OCR instances cached by language
ocr_engines: dict = {}
vietocr_predictor: Optional[object] = None


def get_ocr_engine(lang: str = "vi") -> PaddleOCR:
    global ocr_engines
    if lang not in ocr_engines:
        print(f"[INFO] Initializing PaddleOCR engine for lang='{lang}'...")
        ocr_engines[lang] = PaddleOCR(
            use_angle_cls=True,
            lang=lang,
            use_gpu=False,
        )
    return ocr_engines[lang]


def get_vietocr_predictor():
    global vietocr_predictor
    if vietocr_predictor is None and VIETOCR_AVAILABLE:
        print("[INFO] Initializing VietOCR Predictor (vgg_transformer)...")
        config = Cfg.load_config_from_name("vgg_transformer")
        config["device"] = "cpu"
        vietocr_predictor = Predictor(config)
    return vietocr_predictor


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Load default PaddleOCR and VietOCR models once
    get_ocr_engine("vi")
    if VIETOCR_AVAILABLE:
        get_vietocr_predictor()
    yield


app = FastAPI(
    title="PDF to Markdown OCR API Server",
    description="API Server using PaddleOCR & VietOCR to convert PDF documents into Markdown text.",
    version="1.1.0",
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
    Basic Markdown cleanup and NFC Unicode normalization.
    """
    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)
    text = unicodedata.normalize("NFC", text)
    return text.strip()


def ocr_image_paddle(ocr: PaddleOCR, image_path: Path) -> List[str]:
    """
    Run standard PaddleOCR on one image for text detection + recognition.
    """
    print(f"[OCR-Paddle] Processing: {image_path}")
    result = ocr.ocr(str(image_path), cls=True)

    page_lines = []
    if result and result[0]:
        for line in result[0]:
            text = line[1][0]
            text = clean_text(text)
            if text:
                page_lines.append(text)

    return page_lines


def ocr_image_vietocr(detector: PaddleOCR, image_path: Path) -> List[str]:
    """
    Run PaddleOCR text detection + VietOCR text recognition for Vietnamese text.
    """
    print(f"[OCR-VietOCR] Processing: {image_path}")
    predictor = get_vietocr_predictor()
    if not predictor:
        print("[WARN] VietOCR is not available in environment, falling back to PaddleOCR.")
        return ocr_image_paddle(detector, image_path)

    result = detector.ocr(str(image_path), cls=True)
    if not result or not result[0]:
        return []

    lines_data = []
    with Image.open(image_path) as img:
        img_rgb = img.convert("RGB")
        img_w, img_h = img_rgb.size

        for line in result[0]:
            box = line[0]  # [[x1, y1], [x2, y2], [x3, y3], [x4, y4]]
            xs = [pt[0] for pt in box]
            ys = [pt[1] for pt in box]

            min_x = max(0, int(min(xs)))
            min_y = max(0, int(min(ys)))
            max_x = min(img_w, int(max(xs)))
            max_y = min(img_h, int(max(ys)))

            if max_x - min_x < 5 or max_y - min_y < 5:
                continue

            crop_img = img_rgb.crop((min_x, min_y, max_x, max_y))
            try:
                recognized_text = predictor.predict(crop_img)
                recognized_text = clean_text(recognized_text)
                if recognized_text:
                    lines_data.append((min_y, min_x, recognized_text))
            except Exception as e:
                print(f"[WARN] VietOCR crop recognition failed: {e}")

    # Sort lines by top-to-bottom (min_y), then left-to-right (min_x)
    lines_data.sort(key=lambda item: (item[0], item[1]))
    return [item[2] for item in lines_data]


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


def process_pdf_file(
    pdf_path: Path,
    display_name: Optional[str] = None,
    lang: str = "vi",
    engine: str = "vietocr",
) -> str:
    """
    Process a PDF file and return generated Markdown content.
    """
    detector = get_ocr_engine(lang)
    with tempfile.TemporaryDirectory() as temp_dir:
        image_dir = Path(temp_dir) / "_pages"
        images = pdf_to_images(str(pdf_path), str(image_dir))

        if not images:
            raise RuntimeError("No images generated from PDF")

        pages = []
        for image in images:
            if engine.lower() == "vietocr" and lang == "vi":
                lines = ocr_image_vietocr(detector, image)
            else:
                lines = ocr_image_paddle(detector, image)
            pages.append(lines)

        return generate_markdown(display_name or pdf_path.name, pages)


@app.get("/")
def read_root():
    return {
        "message": "Welcome to PDF to Markdown OCR API Server",
        "endpoints": {
            "health": "/health",
            "convert": "/convert (POST multipart/form-data with 'file', optional 'lang'='vi'|'en', 'engine'='vietocr'|'paddleocr')",
            "docs": "/docs",
        },
    }


@app.get("/health")
def health_check():
    return {"status": "healthy", "vietocr_available": VIETOCR_AVAILABLE}


@app.post("/convert")
async def convert_pdf(
    file: UploadFile = File(...),
    lang: str = Query(
        "vi", description="OCR language: 'vi' (Vietnamese) or 'en' (English)"
    ),
    engine: str = Query(
        "vietocr",
        description="OCR engine: 'vietocr' (best for Vietnamese) or 'paddleocr'",
    ),
    download: bool = Query(
        False, description="If true, downloads the result as a .md file"
    ),
):
    """
    Upload a PDF file and convert it into Markdown format using VietOCR / PaddleOCR.
    """
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(
            status_code=400, detail="Only PDF files are supported."
        )

    with tempfile.TemporaryDirectory() as temp_dir:
        temp_pdf_path = Path(temp_dir) / "input.pdf"
        with open(temp_pdf_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        try:
            markdown_content = process_pdf_file(
                temp_pdf_path,
                display_name=file.filename,
                lang=lang,
                engine=engine,
            )
        except Exception as e:
            print(f"[ERROR] Processing failed: {e}")
            raise HTTPException(
                status_code=500, detail=f"Failed to process PDF: {str(e)}"
            )

    if download:
        stem = Path(file.filename).stem
        filename_out = f"{stem}.md"
        encoded_filename = quote(filename_out)
        ascii_stem = re.sub(r"[^\x00-\x7F]+", "_", stem)
        content_disposition = (
            f'attachment; filename="{ascii_stem}.md"; '
            f"filename*=UTF-8''{encoded_filename}"
        )
        return Response(
            content=markdown_content,
            media_type="text/markdown; charset=utf-8",
            headers={"Content-Disposition": content_disposition},
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
        "--lang", default="vi", help="OCR language: 'vi' (Vietnamese) or 'en' (English)"
    )
    parser.add_argument(
        "--engine",
        default="vietocr",
        choices=["vietocr", "paddleocr"],
        help="OCR engine: 'vietocr' (default for Vietnamese) or 'paddleocr'",
    )
    parser.add_argument(
        "--host", default="0.0.0.0", help="Host address for API server"
    )
    parser.add_argument(
        "--port", type=int, default=6868, help="Port for API server"
    )

    args = parser.parse_args()

    if args.input and args.output:
        # Run CLI mode
        pdf_path = Path(args.input)
        output_dir = Path(args.output)

        if not pdf_path.exists():
            raise FileNotFoundError(f"PDF not found: {pdf_path}")

        output_dir.mkdir(parents=True, exist_ok=True)
        markdown = process_pdf_file(
            pdf_path, lang=args.lang, engine=args.engine
        )

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