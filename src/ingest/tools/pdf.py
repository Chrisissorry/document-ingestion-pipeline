from __future__ import annotations

import pdfplumber
from PIL import Image


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
