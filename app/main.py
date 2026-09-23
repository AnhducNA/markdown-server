import argparse
import os
import re
import subprocess
from pathlib import Path

from paddleocr import PaddleOCR


def pdf_to_images(pdf_path: str, output_dir: str):
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

    images = sorted(
        Path(output_dir).glob("page-*.png")
    )

    print(f"[INFO] Generated {len(images)} page images")

    return images


def clean_text(text: str) -> str:
    """
    Basic Markdown cleanup.
    """

    text = text.replace("\n", " ")
    text = re.sub(r"\s+", " ", text)

    return text.strip()


def ocr_image(ocr, image_path: Path):
    """
    Run PaddleOCR on one image.
    """

    print(f"[OCR] Processing: {image_path}")

    result = ocr.predict(str(image_path))

    page_lines = []

    for res in result:

        data = res.json

        if isinstance(data, str):
            import json
            data = json.loads(data)

        # PaddleOCR output structure can vary by version.
        # Try to retrieve recognized text.
        if isinstance(data, dict):

            texts = data.get("rec_texts", [])

            for text in texts:

                text = clean_text(text)

                if text:
                    page_lines.append(text)

    return page_lines


def generate_markdown(pdf_path, pages):
    """
    Generate Markdown document.
    """

    md = []

    md.append(f"# {Path(pdf_path).stem}")
    md.append("")

    for page_number, lines in enumerate(pages, start=1):

        md.append(f"## Trang {page_number}")
        md.append("")

        for line in lines:
            md.append(line)

        md.append("")

    return "\n".join(md)


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--input",
        required=True,
        help="Input PDF file"
    )

    parser.add_argument(
        "--output",
        required=True,
        help="Output directory"
    )

    args = parser.parse_args()

    pdf_path = Path(args.input)

    output_dir = Path(args.output)

    if not pdf_path.exists():
        raise FileNotFoundError(
            f"PDF not found: {pdf_path}"
        )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    # Temporary directory for rendered pages
    image_dir = output_dir / "_pages"

    # --------------------------------------------------
    # 1. PDF -> Images
    # --------------------------------------------------

    images = pdf_to_images(
        str(pdf_path),
        str(image_dir)
    )

    if not images:
        raise RuntimeError(
            "No images generated from PDF"
        )

    # --------------------------------------------------
    # 2. Initialize PaddleOCR
    # --------------------------------------------------

    print("[INFO] Initializing PaddleOCR...")

    ocr = PaddleOCR(
        lang="vi",
    )

    # --------------------------------------------------
    # 3. OCR
    # --------------------------------------------------

    pages = []

    for image in images:

        lines = ocr_image(
            ocr,
            image
        )

        pages.append(lines)

    # --------------------------------------------------
    # 4. Markdown
    # --------------------------------------------------

    markdown = generate_markdown(
        pdf_path,
        pages
    )

    output_file = (
        output_dir /
        f"{pdf_path.stem}.md"
    )

    output_file.write_text(
        markdown,
        encoding="utf-8"
    )

    print("")
    print("=" * 60)
    print("[SUCCESS]")
    print(f"Markdown: {output_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()