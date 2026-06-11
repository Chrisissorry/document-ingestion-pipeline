from __future__ import annotations

from ..state import IngestState

CONFIDENCE_THRESHOLD = 0.7
_INVOICE_REQUIRED = {"invoice_number", "date", "vendor", "total"}


def validate(state: IngestState) -> dict:
    if state.get("confidence", 0.0) < CONFIDENCE_THRESHOLD:
        return {"needs_review": True}
    if state.get("doc_type") == "invoice":
        fields = state.get("fields", {})
        if any(fields.get(f) is None for f in _INVOICE_REQUIRED):
            return {"needs_review": True}
    return {"needs_review": False}
