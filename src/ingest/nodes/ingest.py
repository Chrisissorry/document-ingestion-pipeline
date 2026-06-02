from __future__ import annotations

from ..state import IngestState
from ..tools.pdf import extract_text


def ingest(state: IngestState) -> dict:
    text = extract_text(state["path"])
    if text:
        return {"raw_text": text, "tier": "text"}
    # TODO (Ingestion cluster): Tier 2 fallback. Render the page to an image and
    # send it to Haiku Vision. The stub just marks the tier and carries empty text.
    return {"raw_text": "", "tier": "vision"}
