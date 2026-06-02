from __future__ import annotations

import pdfplumber


def extract_text(path: str) -> str:
    """Tier 1: pull the embedded text layer. Empty string if the PDF is a scan."""
    parts: list[str] = []
    with pdfplumber.open(path) as pdf:
        for page in pdf.pages:
            parts.append(page.extract_text() or "")
    return "\n".join(parts).strip()
