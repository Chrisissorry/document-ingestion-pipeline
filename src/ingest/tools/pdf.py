from __future__ import annotations

import os

import pdfplumber
from PIL import Image

# Tier 1.5 OCR is opt-in (CLAUDE.md decision #1). Off unless explicitly enabled.
OCR_ENV_FLAG = "INGEST_ENABLE_OCR"


def extract_text(path: str) -> str:
    """Tier 1: pull the embedded text layer. Empty string if the PDF is a scan."""
    parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()


def render_page_image(path: str, page_index: int = 0, resolution: int = 200) -> Image.Image:
    """Render one PDF page to a PIL image. Shared by Tier 1.5 OCR (#57) and Tier 2 Vision (#40)."""
    with pdfplumber.open(path) as pdf:
        page = pdf.pages[page_index]
        return page.to_image(resolution=resolution).original


def ocr_available() -> bool:
    """True only when OCR is both enabled and actually usable (package + Tesseract binary)."""
    if os.environ.get(OCR_ENV_FLAG, "").strip().lower() not in {"1", "true", "yes", "on"}:
        return False
    try:
        import pytesseract

        pytesseract.get_tesseract_version()
    except Exception:
        # Missing package or missing/broken Tesseract binary: degrade, never crash.
        return False
    return True


def ocr_first_page(path: str) -> str:
    """Tier 1.5: OCR the first page of a scan. Caller must guard with ocr_available()."""
    import pytesseract

    image = render_page_image(path)
    return pytesseract.image_to_string(image).strip()
