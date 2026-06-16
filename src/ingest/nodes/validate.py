from __future__ import annotations

from ..state import IngestState

CONFIDENCE_THRESHOLD = 0.7
_INVOICE_REQUIRED = {"invoice_number", "date", "vendor", "total"}
_CONTRACT_REQUIRED = {"effective_date", "term"}


def validate(state: IngestState) -> dict:
    if state.get("confidence", 0.0) < CONFIDENCE_THRESHOLD:
        return {"needs_review": True}
    fields = state.get("fields", {})
    if state.get("doc_type") == "invoice":
        if any(fields.get(f) is None for f in _INVOICE_REQUIRED):
            return {"needs_review": True}
    elif state.get("doc_type") == "contract":
        if not fields.get("parties") or any(fields.get(f) is None for f in _CONTRACT_REQUIRED):
            return {"needs_review": True}
    return {"needs_review": False}
