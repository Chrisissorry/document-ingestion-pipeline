from __future__ import annotations

from ..state import IngestState
from ..tools.pdf import extract_text, ocr_available, ocr_first_page


def ingest(state: IngestState) -> dict:
    text = extract_text(state["path"])
    if text:
        return {"raw_text": text, "tier": "text"}

    # Tier 1.5: optional local OCR for scans (#57). Opt-in and self-disabling when
    # Tesseract is absent, so this never blocks the end-to-end path.
    if ocr_available():
        ocr_text = ocr_first_page(state["path"])
        if ocr_text:
            return {"raw_text": ocr_text, "tier": "ocr"}

    # TODO (#40, Ingestion cluster): Tier 2 fallback. Render the page to an image
    # (tools.pdf.render_page_image) and send it to Haiku Vision. The stub just
    # marks the tier and carries empty text.
    return {"raw_text": "", "tier": "vision"}
