"""Core configuration and settings for Markdown Output Server."""
from pathlib import Path
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    # Output paths
    output_dir: Path = Field(default=Path("./output"), alias="OUTPUT_DIR")
    markdown_output_dir: Path = Field(default=Path("./output/markdown"), alias="MARKDOWN_OUTPUT_DIR")
    asset_output_dir: Path = Field(default=Path("./output/assets"), alias="ASSET_OUTPUT_DIR")
    manifest_output_dir: Path = Field(default=Path("./output/manifest"), alias="MANIFEST_OUTPUT_DIR")
    tmp_dir: Path = Field(default=Path("./tmp"), alias="TMP_DIR")

    # Markdown rendering options
    markdown_include_frontmatter: bool = Field(default=True, alias="MARKDOWN_INCLUDE_FRONTMATTER")
    markdown_include_page_markers: bool = Field(default=True, alias="MARKDOWN_INCLUDE_PAGE_MARKERS")
    markdown_asset_dir: str = Field(default="assets", alias="MARKDOWN_ASSET_DIR")
    markdown_max_blank_lines: int = Field(default=1, alias="MARKDOWN_MAX_BLANK_LINES")
    markdown_encoding: str = Field(default="utf-8", alias="MARKDOWN_ENCODING")
    markdown_strict_validation: bool = Field(default=True, alias="MARKDOWN_STRICT_VALIDATION")

    # OCR options
    ocr_enabled: bool = Field(default=True, alias="OCR_ENABLED")
    ocr_engine: str = Field(default="paddleocr", alias="OCR_ENGINE")
    ocr_min_text_chars: int = Field(default=30, alias="OCR_MIN_TEXT_CHARS")
    ocr_min_text_density: float = Field(default=0.0005, alias="OCR_MIN_TEXT_DENSITY")
    ocr_lang: str = Field(default="vi", alias="OCR_LANG")
    ocr_force: bool = Field(default=False, alias="OCR_FORCE")
    pdf_render_dpi: int = Field(default=200, alias="PDF_RENDER_DPI")

    # Output options
    output_overwrite: bool = Field(default=False, alias="OUTPUT_OVERWRITE")

    # Server settings
    host: str = Field(default="0.0.0.0", alias="HOST")
    port: int = Field(default=8000, alias="PORT")
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    def ensure_directories(self) -> None:
        """Create necessary output and temp directories if they do not exist."""
        for directory in [
            self.output_dir,
            self.markdown_output_dir,
            self.asset_output_dir,
            self.manifest_output_dir,
            self.tmp_dir,
            self.tmp_dir / "rendered_pages",
            self.tmp_dir / "ocr",
            self.tmp_dir / "uploads",
        ]:
            directory.mkdir(parents=True, exist_ok=True)


settings = Settings()
